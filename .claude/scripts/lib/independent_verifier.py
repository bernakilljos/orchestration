"""independent_verifier.py — 독립 검증 (2026-10-29 Phase 2-C 완결).

사용자 지시 (391e691 후속):
  "개발 Agent 성공 주장만으로 VERIFIED X · 독립 Verifier 가 요구사항·실제 Diff·테스트 결과 비교"
  "Verifier 실패/미실행 시 VERIFIED 금지 · Judge 성공 주장만으로 테스트 성공 대체 X"

Phase 2-C 완결 (2026-10-29):
  - safe_mode sandbox cwd 기반 git diff 수집 (원본 아닌 격리 공간)
  - scope-lock 통합 (요구사항 외 변경 탐지)
  - executions 테이블의 verified 플래그 재확인 (개발 Agent 보고 재사용 X)
  - 상태 enum: VERIFIED · UNVERIFIED · REPAIRING · FAILED · OUT_OF_SCOPE

evidence 수집 (실 데이터만):
  - goal description (원문 요구사항)
  - task 실제 cmd + exit_code
  - git diff (sandbox 우선 · 없으면 ROOT)
  - verifier 결과 (등록 verifier · executions.verified 재조회)
  - 테스트 결과 (있으면)
  - scope 위반 (allow_paths 외 수정 파일)

판정:
  - verifier 미실행 (verify_type 없음) → UNVERIFIED
  - verifier 실패 (status!="ok") → REPAIRING
  - evidence 부족 → UNVERIFIED
  - scope 위반 → OUT_OF_SCOPE (fail-closed)
  - 전부 완료 AND verifier PASS AND scope OK → VERIFIED

Judge agent 는 **옵션** · LLM 호출 없이도 판정 (안전 default).

사용:
  from independent_verifier import collect_evidence, judge
  evidence = collect_evidence(goal_id, sandbox_cwd="/path/to/sandbox", allow_paths=["src/"])
  verdict = judge(evidence)
  # verdict: {"status": "VERIFIED"|"UNVERIFIED"|"REPAIRING"|"OUT_OF_SCOPE", "reasons": [...]}
"""
from __future__ import annotations
import fnmatch
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"


def _run_git_in(cwd: Path, args: list, timeout: int = 10) -> Optional[str]:
    """git 명령 실행 · 실패 시 None."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    return None


def _collect_diff_paths(cwd: Path) -> List[str]:
    """git diff --name-only · 커밋 안 된 변경 파일 목록."""
    out = _run_git_in(cwd, ["diff", "--name-only"])
    if not out:
        return []
    paths = [p.strip() for p in out.splitlines() if p.strip()]
    return paths


def changed_paths(cwd: Path) -> List[str]:
    """추적 파일 변경 + 새 파일 (ignore 제외)."""
    untracked = _run_git_in(cwd, ["ls-files", "--others", "--exclude-standard"]) or ""
    return _collect_diff_paths(cwd) + [p.strip() for p in untracked.splitlines() if p.strip()]


def same_pattern_candidates(cwd: Path, limit: int = 20) -> List[Dict[str, Any]]:
    """이번 변경에서 고친(지운) 줄이 저장소 다른 곳에 그대로 남은 위치 — 같은 유형 누락 후보. 판단은 사람·Judge 몫."""
    # HEAD 기준: 스테이징한 변경도 포함 (2026-11-06 실측 — `git add` 뒤 검증하면 후보 0건이었다)
    diff = _run_git_in(cwd, ["diff", "HEAD", "-U0"]) or ""
    removed = {ln[1:].strip() for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---")}
    added = {ln[1:].strip() for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")}
    # 들여쓰기만 바뀌거나 옮긴 줄은 고친 줄이 아니다 (실제 fix 커밋 30건 측정에서 자기 자신을 잡았다)
    code = sorted(x for x in removed - added if len(x) >= 20 and not x.startswith(("#", "//", "|", "*", "-")))
    found = []
    for line in code[:limit]:
        hits = _run_git_in(cwd, ["grep", "-n", "-F", "-e", line]) or ""
        # -F 는 부분 일치라 고친 줄의 새 형태도 잡힌다 → 줄 전체가 같은 것만
        where = [":".join(p[:2]) for p in (h.split(":", 2) for h in hits.splitlines())
                 if len(p) == 3 and p[2].strip() == line]
        if 0 < len(where) <= 20:     # 20곳 초과 = `except Exception as e:` 같은 일반 구문
            found.append({"line": line[:120], "where": where[:5], "count": len(where)})
    return found


EXTERNAL_EVIDENCE = ROOT / ".claude" / "state" / "external-evidence.jsonl"
_MANIFESTS = {"requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml", "pom.xml"}
_IMPORT_LINE = re.compile(r"^\+\s*(?:import|from)\s+([A-Za-z_]\w*)", re.MULTILINE)


def external_dependencies(cwd: Path) -> List[str]:
    """이번 변경이 새로 쓰는 외부 패키지 (표준 라이브러리·저장소 내부 모듈 제외) + 변경된 의존성 파일. V1.1 B."""
    diff = _run_git_in(cwd, ["diff", "-U0", "--", "*.py"]) or ""
    tracked = _run_git_in(cwd, ["ls-files"]) or ""
    local = {Path(p).stem for p in tracked.split()} | {part for p in tracked.split() for part in Path(p).parts}
    found = {m for m in _IMPORT_LINE.findall(diff) if m not in sys.stdlib_module_names and m not in local}
    found |= {Path(p).name for p in changed_paths(cwd) if Path(p).name in _MANIFESTS}
    return sorted(found)


def record_external_evidence(package: str, url: str, version: str, level: str, note: str = "") -> Dict[str, Any]:
    """공식 자료 대조 기록. level: read = 본문 확인 · found = 검색 결과만 (대조로 인정 X) ·
    failed = 검색·접속 실패 (대조로 인정 X · 미확인과 구분해 BLOCKED 로 보고).
    read 는 note 에 본문 인용(20자+), failed 는 note 에 실패 사유 필수 (2026-11-06 · 제목만 보고 확인 처리 방지).
    패키지명·공개 URL·버전·공개 문서 인용만 저장 — 코드·내부 데이터 금지."""
    if level not in ("read", "found", "failed") or not url.startswith("https://"):
        return {"ok": False, "reason": "level 은 read|found|failed · url 은 https"}
    if level == "read" and len(note.strip()) < 20:
        return {"ok": False, "reason": "read 는 본문 인용(20자 이상)을 note 로 남겨야 함"}
    if level == "failed" and not note.strip():
        return {"ok": False, "reason": "failed 는 실패 사유를 note 로 남겨야 함"}
    row = {"package": package, "url": url, "version": version, "level": level, "note": note[:300],
           "checked_at": __import__("time").strftime("%Y-%m-%d")}
    EXTERNAL_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EXTERNAL_EVIDENCE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, **row}


def external_scope(packages: List[str]) -> Dict[str, Any]:
    """외부 근거 축 — none_needed | checked | not_checked | blocked. 본문 확인(read) 기록이 있는 패키지만 확인으로 센다.
    확인 못 한 패키지 중 검색·접속 실패(failed) 기록만 있는 것이 있으면 blocked (외부 사정으로 검증 불가 · PASS 아님)."""
    if not packages:
        return {"scope": "none_needed", "unchecked": [], "blocked": []}
    read, failed = set(), set()
    if EXTERNAL_EVIDENCE.exists():
        for line in EXTERNAL_EVIDENCE.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("level") == "read":
                read.add(row.get("package"))
            elif row.get("level") == "failed":
                failed.add(row.get("package"))
    unchecked = [p for p in packages if p not in read]
    blocked = [p for p in unchecked if p in failed]
    scope = "blocked" if blocked else ("not_checked" if unchecked else "checked")
    return {"scope": scope, "unchecked": unchecked, "blocked": blocked}


def external_evidence_rows(packages: List[str]) -> List[Dict[str, Any]]:
    """패키지별 공식 자료 기록 (read·failed · 최신 순) — Judge 가 인용과 실제 코드 사용의 관련성을 비교하도록 넘긴다."""
    rows = []
    if packages and EXTERNAL_EVIDENCE.exists():
        for line in EXTERNAL_EVIDENCE.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("package") in packages and row.get("level") in ("read", "failed"):
                rows.append(row)
    return rows[::-1]


def _verified_output(task_ids: List[str]) -> str:
    """goal 의 verified=1 실행 기록 (명령 + 출력 끝부분) — 개발 Agent 보고가 아닌 runner 기록."""
    if not task_ids or not DB.exists():
        return ""
    try:
        with sqlite3.connect(str(DB)) as c:
            rows = c.execute(
                f"SELECT cmd, stdout_tail, stderr_tail FROM executions WHERE verified=1 "
                f"AND task_id IN ({','.join('?' * len(task_ids))})", task_ids).fetchall()
    except sqlite3.Error:
        return ""
    return "\n".join(" ".join(x or "" for x in r) for r in rows)


def affected_tests(cwd: Path, changed: List[str]) -> List[str]:
    """변경 파일의 모듈명을 참조하는 테스트 파일 (회귀 후보) — 변경된 테스트 자신 포함. V1.1 C.
    2026-11-09: impact_selection 으로 확장 (이름 변형·호출 관계 2단계·과거 동반 수정)."""
    return impact_selection(cwd, changed)["tests"]


# 2026-11-09 회귀 게이트가 영향 시험을 너무 적게 고르던 결함 (실측: 2ae76b1 은 새 시험 1개만 · 107654b 는
#   pre_commit_full_check(_) ↔ pre-commit-full-check(-) 이름 차이·호출하는 쪽 미추적).
#   공통 모듈·판단 불가 → 전체 회귀. 새 검사 엔진 X — 기존 선정 함수 안에서 넓힌다.
_SRC_EXT = (".py", ".sh", ".ps1", ".psm1", ".bat", ".cmd", ".ts", ".tsx", ".js")
_FULL_ALWAYS = re.compile(r"(^|/)(conftest\.py|pytest\.ini|tool-dispatch\.py|_common\.py|settings\.json)$")
_FANOUT_FULL = 8          # 직접 참조하는 파일 수가 이 이상이면 공통 모듈로 보고 전체 회귀
# 계약(다른 코드가 형식에 의존하는 파일): DB 스키마·마이그레이션·플러그인 스키마 → 전체 회귀
_CONTRACT = re.compile(r"(^|/)(state_db\.py|[^/]*schema[^/]*\.(json|py)|plugin\.json|[^/]*migrat[^/]*\.py|[^/]*\.sql)$", re.I)
_DEFECT_FULL = 3          # orca.db problem_solutions 에 이 파일이 고쳐진 기록이 이 이상이면 재발 위험 → 전체 회귀


def _past_defects(cwd: Path, code: List[str]) -> Dict[str, Any]:
    """기존 결함 기록(orca.db problem_solutions.files_modified · 읽기 전용) 재사용 — 파일별 기록 수와 함께 고쳐진 시험."""
    import sqlite3
    db = cwd / ".claude" / "state" / "orca.db"
    out: Dict[str, Any] = {"counts": {}, "tests": set(), "error": None}
    if not db.is_file():
        return out
    try:
        with sqlite3.connect("file:%s?mode=ro" % db.as_posix(), uri=True, timeout=2) as c:
            rows = [(r[0] or "").replace("\\", "/") for r in c.execute("SELECT files_modified FROM problem_solutions")]
    except sqlite3.Error as e:
        out["error"] = "결함 기록 조회 실패: %s" % e
        return out
    for p in code:
        hits = [r for r in rows if re.search(r"(^|[/,])%s(,|$)" % re.escape(p.replace("\\", "/")), r)]
        if hits:
            out["counts"][p] = len(hits)
            for r in hits:
                out["tests"].update(x for x in r.split(",") if re.search(r"/(test_[^/]+\.py|[^/]+_test\.py)$", x))
    return out
_COCHANGE_COMMITS = 40
_COCHANGE_MAX_FILES = 20
_BULK_CODE_FILES = 40
# 고른 시험 파일 수 상한 (2026-11-16): 단계마다 참조 수는 _FANOUT_FULL 미만이어도 합치면 시험 221개(e2e 포함)를
#   파일 단위로 골라 900초 시간 초과 → 커밋 blocked(사이클 1048 saju_match). 전체 회귀(약 7분)가 더 빠르고 넓다.
_TESTS_FULL = 80


def _name_variants(path: str) -> set:
    s = Path(path).stem
    if s in ("__init__", "__main__", "index", "main"):   # 패키지 진입 파일은 폴더 이름으로 참조된다
        s = Path(path).parent.name
    return {s, s.replace("-", "_"), s.replace("_", "-")} if len(s) >= 3 else set()


def _mentions(text: str, names: set) -> bool:
    return any(re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", text) for n in names)


_COLLECT_CACHE: Dict[str, Any] = {}


def _collectable(cwd: Path, t: str) -> bool:
    """pytest 가 실제로 모으는 시험 파일인가 (pytest.ini 의 testpaths 폴더 안 + python_files 이름).
    2026-11-15: 'git ls-files *_test.py' 가 tools/playwright_sidebar_test.py 같은 실행 스크립트(가져오면 바로 브라우저 로그인 후
    sys.exit)까지 골라 pytest 에 파일로 직접 넘겼고 → 'mainloop: caught unexpected SystemExit' rc=3 로 게이트가 blocked."""
    if not t.endswith(".py"):
        return True
    key = str(cwd)
    if key not in _COLLECT_CACHE:
        pats = set()
        for ini in (_run_git_in(cwd, ["ls-files", "*pytest.ini"]) or "").split():
            try:
                txt = (cwd / ini).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            m = re.search(r"^\s*python_files\s*=([^\n]*)", txt, re.M)
            pats.update(m.group(1).split() if m else ["test_*.py", "*_test.py"])
        _COLLECT_CACHE[key] = (_configured_test_dirs(cwd), sorted(pats) or ["test_*.py", "*_test.py"])
    dirs, pats = _COLLECT_CACHE[key]
    t = t.replace("\\", "/")
    in_dir = (not dirs) or any(d in (".", "") or t.startswith(d.rstrip("/") + "/") for d in dirs)
    return in_dir and any(fnmatch.fnmatch(Path(t).name, p) for p in pats)


def impact_selection(cwd: Path, changed: List[str]) -> Dict[str, Any]:
    """{"tests": [...], "full": 사유|None, "why": {시험: 사유}} — 회귀 게이트·self-healing 공용."""
    out = _run_git_in(cwd, ["ls-files", "*test_*.py", "*_test.py", "*.test.ts", "*.test.js"]) or ""
    tests = [t.strip() for t in out.splitlines() if t.strip() and _collectable(cwd, t.strip())]
    tset = set(tests)
    code = [p for p in changed if Path(p).suffix in _SRC_EXT and p not in tset]
    why: Dict[str, str] = {t: "변경된 시험" for t in tests if t in changed}
    full = None
    for p in changed:
        if _FULL_ALWAYS.search(p.replace("\\", "/")):
            full = "공통 설정·실행 기반 변경 (%s)" % p
            break
    contract = [p for p in changed if _CONTRACT.search(p.replace("\\", "/"))]
    if contract and not full:
        full = "계약 파일 변경 (%s)" % ", ".join(contract[:3])
    if not code:
        return {"tests": list(why), "full": full, "why": why}
    defects = _past_defects(cwd, code)
    risky = {p: n for p, n in defects["counts"].items() if n >= _DEFECT_FULL}
    if risky and not full:
        full = "과거 결함 기록이 많은 파일 변경 (%s)" % ", ".join("%s %d건" % (Path(p).name, n) for p, n in risky.items())
    for t in tests:   # 결함 기록에서 함께 고쳐진 시험 (절대 경로로 저장돼 있어 끝 경로로 대조)
        if any(x.endswith("/" + t) for x in defects["tests"]):
            why.setdefault(t, "과거 결함 수정 때 함께 고쳐진 시험")
    short = [p for p in code if not _name_variants(p)]
    if short and not full:          # 이름으로 참조를 찾을 수 없는 파일 (db.py 등) — 범위 판단 불가 (리뷰 SHOULD 8)
        full = "이름이 짧아 참조를 추적할 수 없는 변경 (%s)" % ", ".join(short[:3])
    if len(code) > _BULK_CODE_FILES and not full:   # 대량 변경 — 추적 비용 > 전체 회귀 (리뷰 SHOULD 9)
        full = "대량 코드 변경 %d개" % len(code)
    if full and len(code) > _BULK_CODE_FILES:
        return {"tests": [t for t in tests if t in why], "full": full, "why": why}
    corpus = [p.strip() for p in (_run_git_in(cwd, ["ls-files"]) or "").splitlines()
              if p.strip().endswith(_SRC_EXT) and p.strip() not in tset]
    texts: Dict[str, str] = {}

    def _text(p):
        if p not in texts:
            try:
                texts[p] = (cwd / p).read_text(encoding="utf-8", errors="replace")
            except OSError:
                texts[p] = ""
        return texts[p]

    # 호출 관계 2단계: 바뀐 파일 → 그것을 부르는 파일 → 그것을 부르는 파일
    names = set().union(*(_name_variants(p) for p in code))
    frontier, seen = list(code), set(code)
    for hop in (1, 2):
        nxt = []
        for src in frontier:
            v = _name_variants(src)
            if not v:
                continue
            users = [p for p in corpus if p not in seen and p != src and _mentions(_text(p), v)]
            # 2단계도 같은 상한 (2026-11-15): 죽은 web 멘션 모듈 삭제 → 1단계 호출자 web/app.py(같은 낱말) →
            #   2단계에서 'app' 이름으로 넓혀 시험 278개를 파일 단위로 골랐고(e2e 포함) 900초 초과로 blocked ·
            #   dev 회차가 61분에 끊겼다. 공통 모듈을 거치면 전체 회귀(405초)가 더 빠르고 정확하다.
            if len(users) >= _FANOUT_FULL and not full:
                full = "공통 모듈 %s 를 %d개 파일이 참조%s" % (src, len(users), "" if hop == 1 else " (2단계 호출자)")
            nxt += users
            seen.update(users)
        if full:      # 이미 전체 회귀 — 더 넓히는 계산은 버려진다 (리뷰 재공격 SHOULD 성능)
            return {"tests": [t for t in tests if t in why], "full": full, "why": why}
        names |= set().union(*(_name_variants(p) for p in nxt)) if nxt else set()
        frontier = nxt
    for t in tests:
        if t not in why and names:
            try:
                txt = (cwd / t).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if _mentions(txt, names):
                why[t] = "변경 파일 또는 그 호출자를 참조"
    # 과거 결함 기록: 같은 파일을 고칠 때 함께 고쳐진 시험 (git 이력)
    log = _run_git_in(cwd, ["log", "-n", str(_COCHANGE_COMMITS), "--full-diff", "--format=%x01", "--name-only",
                            "--", *code], timeout=30)
    if log is None:
        why_skipped = "git 이력 조회 실패 (동반 수정 근거 미사용)"
        log = ""
    else:
        why_skipped = None
    for chunk in log.split("\x01"):
        files = {x.strip() for x in chunk.splitlines() if x.strip()}
        if len(files) > _COCHANGE_MAX_FILES:      # 일괄 커밋(초기·병합·대량 정리)은 근거로 쓰지 않는다
            continue
        for t in files & tset:
            why.setdefault(t, "과거 같은 파일과 함께 수정됨")
    n_sel = sum(1 for t in why if t.endswith(".py"))
    if n_sel > _TESTS_FULL and not full:
        full = "영향 시험 %d개 — 파일 단위 실행보다 전체 회귀가 빠름" % n_sel
    if not any(t.endswith(".py") for t in why) and not full:   # .ts 등만 잡히면 게이트가 실행할 시험 0 (리뷰 NIT)
        full = "영향 시험을 찾지 못함 — 범위를 안전하게 정할 수 없어 전체 회귀"
    out = {"tests": [t for t in tests if t in why], "full": full, "why": why}
    if why_skipped:
        out["cochange"] = why_skipped
    return out


def _gate_mem_need(history: Optional[List[float]] = None) -> tuple:
    """R339 전체 회귀를 바로 시작해도 되는 절대 여유 (GB) — (commit, 물리).

    R352 (2026-11-20 · 사용자 결정 '기본 OFF 유지 · 고정 수치·단일 조건 X'): commit 기준을 고정 2.0GB 가정이 아니라
    실측한 '게이트 실행 중 commit 증가량' 최근 이력의 최대치 × 여유 배수 + 여유분 으로 정한다 (이력 없으면 종전 기본값).
    실측 근거: 전체 회귀 중 commit 87.7→95.0% · 최저 여유 1.27GB · 물리 여유는 4.3GB 이상 → 묶이는 쪽은 commit.
    물리 기준은 강제 종료 시점 물리 여유 2.3GB 보다 위 (3.0). 모두 환경 변수로 조정 (이름 붙인 안전 상수)."""
    def _f(name, default):
        try:
            return max(0.0, float(os.environ.get(name, default)))
        except ValueError:
            return float(default)
    floor = _f("ORCA_GATE_MEM_FREE_GB", "2.0")
    used = [float(x) for x in (history or []) if isinstance(x, (int, float)) and x >= 0]
    if used:
        need = max(used) * _f("ORCA_GATE_MEM_MARGIN_X", "1.5") + _f("ORCA_GATE_MEM_MARGIN_GB", "0.5")
        floor = max(need, _f("ORCA_GATE_MEM_MIN_GB", "1.0"))
    return floor, _f("ORCA_GATE_PHYS_FREE_GB", "3.0")


class _CommitWatch:
    """R352: 시험 실행 동안 commit 메모리를 5초마다 재서 '이 작업이 추가로 쓴 양' 을 실측 (스레드 · 실측 오버헤드 780초 중 0.14초).
    측정 불가면 아무것도 기록하지 않는다 (0 으로 만들지 않음)."""

    def __init__(self, interval: float = 5.0):
        self.interval, self.samples = interval, []
        self._stop = None
        self._th = None

    def __enter__(self):
        import threading
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import repair_sandbox as _sb
            self._probe = _sb.commit_memory
        except Exception:  # noqa: BLE001
            return self
        self._stop = threading.Event()
        self._take()
        self._th = threading.Thread(target=self._loop, daemon=True)
        self._th.start()
        return self

    def _take(self):
        try:
            cm = self._probe() or {}
        except Exception:  # noqa: BLE001
            return
        if cm.get("measured") and cm.get("free_gb") is not None:
            self.samples.append((cm.get("percent"), cm.get("free_gb")))
        self._take_cpu()

    def _take_cpu(self):
        """R349: 같은 스레드에서 전체 CPU 도 기록 · 90% 이상일 때만 상위 프로세스 3개 (기계 전체 대비 % · 코어 수로 나눔).
        psutil 첫 호출은 기준점이라 버림 · psutil 없으면 기록 안 함 (0 으로 만들지 않음)."""
        try:
            import psutil
        except ImportError:
            return
        if not hasattr(self, "cpu"):
            self.cpu, self.cpu_top = [], []
            psutil.cpu_percent(None)
            return
        v = psutil.cpu_percent(None)
        self.cpu.append(v)
        if v >= 90 and len(self.cpu_top) < 5:
            import time as _t
            n = psutil.cpu_count() or 1
            plist = list(psutil.process_iter(["name"]))
            for p in plist:              # 기준점 한 번 → 0.5초 뒤 한 번에 읽음 (프로세스마다 기다리면 300개 × 0.1초 = 30초)
                try:
                    p.cpu_percent(None)
                except Exception:  # noqa: BLE001
                    pass
            _t.sleep(0.5)
            procs = []
            for p in plist:
                try:
                    procs.append((round(p.cpu_percent(None) / n, 1), p.info["name"]))
                except Exception:  # noqa: BLE001
                    pass
            self.cpu_top.append({"cpu": v, "top": sorted(procs, reverse=True)[:3]})

    def _loop(self):
        while not self._stop.wait(self.interval):
            self._take()

    def __exit__(self, *exc):
        if self._stop:
            self._stop.set()
            self._th.join(2)
            self._take()
        return False

    def summary(self) -> Optional[Dict[str, Any]]:
        if len(self.samples) < 2:
            return None
        start_pct, start_free = self.samples[0]
        cpu = getattr(self, "cpu", [])
        cpu_info = ({"cpu_avg": round(sum(cpu) / len(cpu), 1), "cpu_max": max(cpu), "cpu_ge90": sum(1 for c in cpu if c >= 90),
                     "cpu_samples": len(cpu), "cpu_top_when_saturated": getattr(self, "cpu_top", [])} if cpu else {})
        return {**cpu_info, "start_pct": start_pct, "peak_pct": max(p for p, _ in self.samples if p is not None),
                "start_free_gb": start_free, "min_free_gb": min(f for _, f in self.samples),
                "used_gb": round(max(0.0, start_free - min(f for _, f in self.samples)), 2), "samples": len(self.samples)}


def _wait_memory_for_heavy(res: Dict[str, Any]) -> str | None:
    """STD-MEMORY-001: 무거운 전체 회귀 전 commit 메모리 80%↑면 75% 이하까지 대기 · 90%↑가 계속되면 실행 보류(blocked).
    측정 불가는 막지 않는다 (기록만). 메모리 부족을 이유로 시험을 생략·PASS 처리하지 않는다."""
    import time as _t
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import repair_sandbox as _sb
        probe = _sb.commit_memory
    except Exception:  # noqa: BLE001
        return None
    try:
        wait_max = float(os.environ.get("ORCA_GATE_MEM_WAIT_SEC", "300"))
    except ValueError:                      # 잘못된 값으로 게이트가 죽지 않게 (리뷰 SHOULD 10)
        wait_max = 300.0
    t0 = _t.time()
    while True:
        cm = probe() or {}
        if not cm.get("measured") or cm.get("percent") is None:
            res["memory_wait"] = "측정 불가"
            return None
        pct, waited = cm["percent"], _t.time() - t0
        res["memory_wait"] = {"waited_sec": round(waited), "percent": pct, "free_gb": cm.get("free_gb"),
                              "phys_free_gb": cm.get("phys_free_gb")}
        if pct < (75 if waited > 0 else 80):        # 대기에 들어가면 75% 이하에서 재개
            return None
        # R339: % 만으로 기다리면 commit 이 85~87% 에 머무는 PC 에선 300초 뒤 결국 그대로 진행해 대기가 순수 낭비였다
        #   (2026-11-20 실측 3회: 86.7·85.6% · commit 여유 3.5GB · 물리 여유 5.7GB · pytest 최대 0.5GB).
        #   90% 미만이고 commit 여유·물리 여유가 둘 다 넉넉하면 바로 진행 · 하나라도 부족하면 종전대로 대기 · 90%+ 는 종전대로 보류.
        need_commit, need_phys = _gate_mem_need(res.get("memory_history"))
        # 기본 꺼짐: STD-MEMORY-001(사용자 확정 2026-11-09 '80%부터 무거운 작업 대기') 을 바꾸는 판정이라 사용자 결정 전까지 opt-in
        if os.environ.get("ORCA_GATE_MEM_ABSOLUTE") == "1" and pct < 90 and (cm.get("free_gb") or 0) >= need_commit and (cm.get("phys_free_gb") or 0) >= need_phys:
            res["memory_wait"]["reason"] = "여유 충분 (commit %.2fGB ≥ %.1f · 물리 %.2fGB ≥ %.1f)" % (
                cm["free_gb"], need_commit, cm["phys_free_gb"], need_phys)
            return None
        if waited >= wait_max:
            if pct >= 90:
                return "메모리 %s%% — %d초 대기 후에도 90%% 이상 · 전체 회귀 보류 (메모리 회복 후 다시 실행)" % (pct, wait_max)
            return None                              # 80~90%: 병렬 없이 순차 실행 (pytest 단일 프로세스)
        _t.sleep(min(15.0, max(0.2, wait_max / 20)))


def _configured_test_dirs(cwd: Path) -> List[str]:
    """pytest.ini 의 testpaths (저장소에 등록된 설정 전부) → 상대 폴더 목록. 설정이 없으면 시험 파일 폴더."""
    dirs = set()
    for ini in (_run_git_in(cwd, ["ls-files", "*pytest.ini"]) or "").split():
        try:
            txt = (cwd / ini).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        m = re.search(r"^\s*testpaths\s*=([^\n]*(?:\n[ \t]+[^\n]+)*)", txt, re.M)   # 들여쓴 이어지는 줄 포함
        base = Path(ini).parent
        for d in (m.group(1).split() if m else ["."]):
            for hit in sorted((cwd / base).glob(d)) if any(ch in d for ch in "*?[") else [cwd / base / d]:
                if hit.is_dir():
                    dirs.add(str(hit.relative_to(cwd)).replace("\\", "/"))
    if not dirs:
        dirs = {str(Path(t).parent).replace("\\", "/") for t in
                (_run_git_in(cwd, ["ls-files", "*test_*.py"]) or "").split() if t.strip()}
    return sorted(dirs)


REGRESSION_STAMP = ".claude/state/regression-gate.json"
# 2026-11-14: .vue·.jsx·.mjs·.cjs·.json 이 빠져 Vue 만 바꾼 커밋은 'skip' = 아무 검사 없이 커밋됐다
# 2026-11-15 (R256): 실제 개발 프로젝트(IFRS = SVN · 최근 200 커밋 변경 파일 java 604 · vue 470 · js 47 · yml 9 · xml 9)
#   의 java·xml·yml 이 검사 대상에 없어 Java 변경은 아무 검사 없이 들어갔다 → 추가. (css 4건은 문법 검사기 없음 · 대상 외)
#   이 목록은 커밋 훅(pre_commit_full_check.py · pre-commit-full-check.sh)과 같아야 한다 — 시험이 대조.
_CODE_EXT = (".py", ".sh", ".ps1", ".psm1", ".bat", ".cmd", ".js", ".ts", ".tsx",
             ".vue", ".jsx", ".mjs", ".cjs", ".json", ".java", ".xml", ".yml", ".yaml", ".go")
_JSON_LENIENT = re.compile(r"(^|/)(tsconfig[^/]*|jsconfig[^/]*|\.eslintrc[^/]*)\.json$|(^|/)\.vscode/", re.I)
SYNTAX_STAMP = ".claude/state/syntax-gate.json"   # git 이 아닌 작업본(SVN·버전 관리 없음)용 기록


def _jsonc_to_json(text: str) -> str:
    """주석(// · /* */)과 끝 쉼표를 문자열 밖에서만 걷어 낸다 — tsconfig·.vscode 설정 (2026-11-15 R256:
    전에는 이 파일들을 아예 '미검사' 로 남겼다). 문자열 안의 // 나 , 는 건드리지 않는다."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
        elif c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise ValueError("닫히지 않은 /* 주석")
            i = j + 2
        else:
            out.append(c)
            i += 1
    s, res, in_str, esc = "".join(out), [], False, False
    for k, c in enumerate(s):
        if in_str:
            res.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == ",":
            rest = s[k + 1:].lstrip()
            if rest[:1] in ("}", "]"):
                continue   # 끝 쉼표
        res.append(c)
    return "".join(res)


# PowerShell 공식 구문 분석기 (실행하지 않음) — 오류가 있으면 줄:열 메시지를 찍고 exit 1
_PS_PARSE = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; $e=$null; $t=$null; "
             "[void][System.Management.Automation.Language.Parser]::ParseFile($env:ORCA_PSF,[ref]$t,[ref]$e); "
             "if($e -and $e.Count){ foreach($x in $e){ '{0}:{1} {2}' -f $x.Extent.StartLineNumber,"
             "$x.Extent.StartColumnNumber,$x.Message }; exit 1 }; exit 0")

# Java 구문 분석만 (클래스경로 없이) — 공식 컴파일러 API JavacTask.parse(). javac 를 그냥 돌리면 import·심볼 해석
#   오류(package does not exist)가 섞이고, JDK 8 은 -XDshould-stop 계열로 구문 단계에서 멈추지 않는다 (2026-11-15 실측).
#   JavacTask 는 com.sun.source.util (JDK 9+ 공개 모듈 · JDK 8 tools.jar) — 반영(reflection)으로 불러 컴파일 의존 없음.
_JAVA_HELPER = r"""import javax.tools.*; import java.util.*; import java.nio.charset.Charset;
public class OrcaJavaParse { public static void main(String[] a) throws Exception {
  JavaCompiler c = ToolProvider.getSystemJavaCompiler();
  if (c == null) { System.out.println("NOCOMPILER"); System.exit(3); }
  DiagnosticCollector<JavaFileObject> d = new DiagnosticCollector<JavaFileObject>();
  StandardJavaFileManager fm = c.getStandardFileManager(d, Locale.ENGLISH, Charset.forName(a[0]));
  List<String> files = Arrays.asList(a).subList(1, a.length);
  Object t = c.getTask(null, fm, d, Arrays.asList("-proc:none", "-encoding", a[0]), null, fm.getJavaFileObjectsFromStrings(files));
  Class.forName("com.sun.source.util.JavacTask").getMethod("parse").invoke(t);
  int n = 0;
  for (Diagnostic<? extends JavaFileObject> x : d.getDiagnostics()) {
    if (x.getKind() != Diagnostic.Kind.ERROR) continue;
    n++;
    System.out.println("ERR\t" + (x.getSource() == null ? "" : x.getSource().getName()) + "\t" + x.getLineNumber()
        + "\t" + x.getMessage(Locale.ENGLISH).replace('\n', ' ').replace('\r', ' '));
  }
  System.exit(n > 0 ? 1 : 0);
} }
"""


def _java_parse(cwd: Path, rels: List[str]):
    """(오류 [{file,error}], 검사한 rel, 미검사 rel+사유) — JDK 없으면 전부 미검사."""
    import hashlib
    import shutil as _sh
    import tempfile
    javac = _sh.which("javac")
    if not javac:
        return [], [], [r + " (javac 없음)" for r in rels]
    jbin = Path(javac).resolve().parent
    java = next((str(p) for p in (jbin / "java.exe", jbin / "java") if p.is_file()), None)
    if not java:
        return [], [], [r + " (JDK java 없음)" for r in rels]
    key = hashlib.sha256((_JAVA_HELPER + str(jbin)).encode("utf-8")).hexdigest()[:12]
    cache = Path(tempfile.gettempdir()) / ("orca-javaparse-" + key)
    tools = jbin.parent / "lib" / "tools.jar"   # JDK 8 만 있음 (9+ 는 모듈)
    cp = str(cache) + (os.pathsep + str(tools) if tools.is_file() else "")
    try:
        if not (cache / "OrcaJavaParse.class").is_file():
            cache.mkdir(parents=True, exist_ok=True)
            (cache / "OrcaJavaParse.java").write_text(_JAVA_HELPER, encoding="utf-8")
            r = subprocess.run([javac, "-encoding", "UTF-8", "-d", str(cache), str(cache / "OrcaJavaParse.java")],
                               capture_output=True, text=True, errors="replace", timeout=120)
            if r.returncode != 0:
                return [], [], [x + " (Java 검사기 준비 실패)" for x in rels]
        enc = "UTF-8"
        for pom in (cwd / "pom.xml", *sorted(cwd.glob("*/pom.xml")), *sorted(cwd.glob("*/*/pom.xml"))):
            try:
                m = re.search(r"<project\.build\.sourceEncoding>\s*([\w-]+)\s*<", pom.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if m:
                enc = m.group(1)
                break
        r = subprocess.run([java, "-Duser.language=en", "-cp", cp, "OrcaJavaParse", enc, *[str(cwd / x) for x in rels]],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [], [], [x + " (%s)" % type(e).__name__ for x in rels]
    if r.returncode not in (0, 1):
        return [], [], [x + " (Java 검사기 실행 실패 rc=%s)" % r.returncode for x in rels]
    by_abs = {os.path.normcase(str((cwd / x).resolve())): x for x in rels}
    errors: Dict[str, List[str]] = {}
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 4 and parts[0] == "ERR":
            rel = by_abs.get(os.path.normcase(str(Path(parts[1]).resolve())), parts[1])
            errors.setdefault(rel, []).append("%s:%s %s" % (rel, parts[2], parts[3]))
    if r.returncode == 1 and not errors:
        return [], [], [x + " (Java 검사기 출력 판독 불가)" for x in rels]
    return ([{"file": f, "error": "\n".join(v)[:600]} for f, v in errors.items()],
            [x for x in rels if x not in errors], [])


def staged_syntax_check(cwd: Path, files: List[str]) -> Dict[str, Any]:
    """커밋할 소스 파일 자체의 문법 검사 (2026-11-14 · 사용자: "테스트 몇 개 통과보다 변경한 소스가 실제로 검사됐나").
    회귀 시험은 영향 시험만 돌려 바뀐 파일의 문법 오류를 놓칠 수 있었다. 검사기는 기존·공식 도구만:
      .py compile() (SyntaxWarning 도 오류) · .json json.loads (주석 허용 설정은 주석·끝 쉼표 제거 후) · .sh bash -n ·
      .js/.mjs/.cjs/.jsx/.ts/.tsx/.vue = 편집 직후 훅 check-js-syntax.sh (프로젝트 node·tsc·Vue 컴파일러) ·
      .ps1/.psm1 PowerShell Parser.ParseFile · .java JavacTask.parse · .xml ElementTree · .yml yaml.compose · .go gofmt -e
    도구가 없어 못 본 파일은 통과로 세지 않고 unchecked 로 남긴다 → 게이트가 unverified 로 커밋 차단 (R256)."""
    import shutil as _sh
    errors, checked, unchecked, java = [], [], [], []
    hook = cwd / ".claude" / "hooks" / "check-js-syntax.sh"
    if not hook.is_file():
        hook = Path(__file__).resolve().parents[2] / "hooks" / "check-js-syntax.sh"
    bash, node = _sh.which("bash"), _sh.which("node")
    tsc = _sh.which("tsc") or ((cwd / "node_modules" / ".bin" / "tsc").exists() and "local")
    for rel in files:
        p = cwd / rel
        if not p.is_file():
            continue   # 삭제된 파일
        ext = p.suffix.lower()
        try:
            if ext == ".py":
                # SyntaxWarning(잘못된 이스케이프 "\s" 등)도 오류로 — 이후 버전에서 SyntaxError 가 될 예정이고
                #   R255 커밋에서 실제로 게이트를 통과한 사례 (Windows 경로 "\scripts\tests" → 탭 문자로 바뀐 시험)
                import warnings as _w
                with _w.catch_warnings():
                    _w.simplefilter("error", SyntaxWarning)
                    # Python 3.11 이하는 같은 잘못된 이스케이프를 DeprecationWarning 으로 낸다 (3.12 부터 SyntaxWarning) —
                    #   이 머신(3.11.9)에서 test_syntax_check_treats_invalid_escape_warning_as_error 가 실패해 확인 (2026-11-18 병합)
                    _w.filterwarnings("error", message=r"invalid escape sequence", category=DeprecationWarning)
                    compile(p.read_bytes(), rel, "exec")
                checked.append(rel)
            elif ext == ".json":
                text = p.read_text(encoding="utf-8-sig")
                json.loads(_jsonc_to_json(text) if _JSON_LENIENT.search(rel.replace("\\", "/")) else text)
                checked.append(rel)
            elif ext == ".sh":
                if not bash:
                    unchecked.append(rel + " (bash 없음)")
                    continue
                r = subprocess.run([bash, "-n", str(p)], capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=30)
                (checked.append(rel) if r.returncode == 0 else errors.append({"file": rel, "error": r.stderr.strip()[:400]}))
            elif ext in (".ps1", ".psm1"):
                ps = _sh.which("powershell") or _sh.which("pwsh")
                if not ps:
                    unchecked.append(rel + " (PowerShell 없음)")
                    continue
                r = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-Command", _PS_PARSE], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=60,
                                   env={**os.environ, "ORCA_PSF": str(p.resolve())})
                if r.returncode == 0:
                    checked.append(rel)
                elif r.returncode == 1 and r.stdout.strip():
                    errors.append({"file": rel, "error": "\n".join("%s:%s" % (rel, x) for x in r.stdout.strip().splitlines())[:600]})
                else:
                    unchecked.append(rel + " (PowerShell 구문 분석 실행 실패 rc=%s)" % r.returncode)
            elif ext == ".java":
                java.append(rel)   # JVM 기동 1회로 모아서 검사 (아래)
            elif ext == ".xml":
                import xml.etree.ElementTree as _ET
                try:
                    _ET.parse(str(p))   # 정형성(well-formed) 검사 · 외부 DTD 는 가져오지 않음
                    checked.append(rel)
                except _ET.ParseError as e:
                    errors.append({"file": rel, "error": "%s %s" % (rel, e)})
            elif ext in (".yml", ".yaml"):
                try:
                    import yaml as _yaml
                except ImportError:
                    unchecked.append(rel + " (PyYAML 없음)")
                    continue
                try:   # compose = 구문만 (사용자 태그 !Ref 등은 객체로 만들지 않으므로 오류 아님)
                    for _ in _yaml.compose_all(p.read_text(encoding="utf-8-sig"), Loader=_yaml.SafeLoader):
                        pass
                    checked.append(rel)
                except _yaml.YAMLError as e:
                    errors.append({"file": rel, "error": ("%s %s" % (rel, e))[:600]})
            elif ext == ".go":
                gofmt = _sh.which("gofmt")
                if not gofmt:
                    unchecked.append(rel + " (gofmt 없음)")
                    continue
                r = subprocess.run([gofmt, "-e", "-l", str(p)], capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=30)
                (checked.append(rel) if r.returncode == 0 else errors.append({"file": rel, "error": r.stderr.strip()[:400]}))
            elif ext in (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".vue"):
                need = {"node": node, "ts": tsc or _nearest_ts_pkg(p), "jsx": _sh.which("esbuild")}
                key = "ts" if ext in (".ts", ".tsx") else ("jsx" if ext == ".jsx" else "node")
                if not (bash and hook.is_file() and node and need[key]):
                    unchecked.append(rel + " (%s 없음)" % ("tsc" if key == "ts" else "esbuild" if key == "jsx" else "node"))
                    continue
                if ext == ".vue":
                    probe = subprocess.run([node, "-e", "const r=require('module').createRequire(process.argv[1]);"
                                            "for(const m of ['vue/compiler-sfc','@vue/compiler-sfc']){try{r.resolve(m);process.exit(0)}catch(e){}}process.exit(3)",
                                            str(p.resolve())], capture_output=True, timeout=30)
                    if probe.returncode != 0:
                        unchecked.append(rel + " (Vue 컴파일러 없음)")
                        continue
                r = subprocess.run([bash, str(hook)], input=json.dumps({"tool_input": {"file_path": str(p.resolve())}}),
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                                   env={**os.environ, "CLAUDE_PROJECT_DIR": str(cwd)})
                out = (r.stdout or "").strip()
                if r.returncode == 2 or '"decision"' in out:
                    try:
                        msg = json.loads(out.splitlines()[-1]).get("reason", out)
                    except (ValueError, IndexError):
                        msg = out or r.stderr
                    errors.append({"file": rel, "error": str(msg).strip()[:600]})
                else:
                    checked.append(rel)
            else:
                unchecked.append(rel + " (문법 검사기 없음)")
        except SyntaxError as e:
            errors.append({"file": rel, "error": "%s:%s %s" % (rel, e.lineno, e.msg)})
        except ValueError as e:   # json.JSONDecodeError 포함
            errors.append({"file": rel, "error": "%s %s" % (rel, e)})
        except (OSError, subprocess.TimeoutExpired) as e:
            unchecked.append("%s (%s)" % (rel, type(e).__name__))
    if java:
        je, jc, ju = _java_parse(cwd, java)
        errors += je
        checked += jc
        unchecked += ju
    return {"errors": errors, "checked": checked, "unchecked": unchecked}


def _nearest_ts_pkg(p: Path) -> Optional[Path]:
    """파일에서 가장 가까운 node_modules/typescript — 훅 check-js-syntax.sh 가 이것으로 문법만 본다(2026-11-19:
    TS 패키지가 하위 폴더 nextjs/ 에만 있는 대상에서 .tsx 가 늘 'tsc 없음' 미검증이 되어 커밋이 막혔다)."""
    for d in p.resolve().parents:
        cand = d / "node_modules" / "typescript"
        if (cand / "lib" / "typescript.js").is_file():
            return cand
    return None


def _syntax_verdict(res: Dict[str, Any], syn: Dict[str, Any]) -> bool:
    """문법 검사 결과로 상태를 정하면 True (오류 = syntax_error · 미검사 = unverified · 둘 다 커밋 차단)."""
    res["syntax_checked"], res["syntax_unchecked"], res["syntax_errors"] = syn["checked"], syn["unchecked"], syn["errors"]
    if syn["errors"]:
        res["status"] = "syntax_error"   # 시험 결과와 무관하게 커밋 차단 — 고친 뒤 게이트 재실행
        res["reason"] = "변경 소스 문법 오류 %d건: %s" % (len(syn["errors"]), "; ".join(
            "%s — %s" % (e["file"], e["error"].splitlines()[0] if e["error"] else "") for e in syn["errors"][:3]))
        return True
    if syn["unchecked"]:
        # 2026-11-15 (R256) 사용자: "검사기 없음 → 미검증, 검증 완료로 판단하거나 자동 커밋하지 않음" —
        #   전에는 unchecked 로 적기만 하고 pass 가 나와 그대로 커밋됐다
        res["status"] = "unverified"
        res["reason"] = "문법 검사기가 없어 확인 못 한 변경 파일 %d건 — 검증 완료로 보지 않고 자동 커밋하지 않음: %s" % (
            len(syn["unchecked"]), ", ".join(syn["unchecked"][:5]))
        return True
    return False


def _svn_changed(cwd: Path, timeout: int = 60) -> Optional[List[str]]:
    """SVN 작업본의 수정·추가·교체 파일 (커밋 대상 후보 · 경로 '/' 통일). svn 아님·실패 = None.
    timeout: 커밋 훅(5초 제한)은 짧게 넘긴다 · 넘으면 None → 훅이 차단 (fail-closed)."""
    import shutil as _sh
    svn = _sh.which("svn")
    if not svn or not (cwd / ".svn").is_dir():
        return None
    try:
        r = subprocess.run([svn, "status", "-q", "--non-interactive"], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    out = []
    for line in r.stdout.splitlines():
        if len(line) > 8 and line[0] in "MAR":
            rel = line[8:].strip().replace("\\", "/")
            if (cwd / rel).is_file():
                out.append(rel)
    return out


def file_hashes(cwd: Path, rels: List[str]) -> Dict[str, str]:
    import hashlib
    out = {}
    for rel in rels:
        try:
            out[rel] = hashlib.sha256((cwd / rel).read_bytes()).hexdigest()
        except OSError:
            out[rel] = ""
    return out


def syntax_gate(cwd: Path) -> Dict[str, Any]:
    """git 이 아닌 작업본(IFRS = SVN)의 커밋 전 문법 게이트 (2026-11-15 R256 · 커밋 훅이 git commit 에만 반응해
    실제 개발 프로젝트의 svn commit 은 문법 검사를 한 번도 거치지 않았다). 수정 파일 내용 해시와 함께 SYNTAX_STAMP 에 기록 →
    커밋 훅(pre_commit_full_check.py)이 지금 수정 파일 해시가 같고 상태가 pass/skip 일 때만 svn commit 을 통과시킨다."""
    import time as _t
    changed = _svn_changed(cwd)
    res: Dict[str, Any] = {"at": int(_t.time()), "vcs": "svn" if changed is not None else "none"}
    if changed is None:
        res.update(status="blocked", reason="SVN 작업본이 아니거나 svn status 실패 — 수정 파일을 확정할 수 없음", files={})
    else:
        code = [p for p in changed if p.lower().endswith(_CODE_EXT)]
        res["changed_code"] = code
        res["files"] = file_hashes(cwd, code)
        if not code:
            res["status"] = "skip"
        elif not _syntax_verdict(res, staged_syntax_check(cwd, code)):
            res["status"] = "pass"
        if res.get("status") in ("pass", "skip"):   # R296 SVN 작업본도 페이지·DB 속도 검사 (SQL·매퍼만 바뀐 경우 포함)
            try:
                perf = perf_gate(cwd, changed)
            except Exception as e:  # noqa: BLE001
                perf = {"status": "perf_unmeasured", "items": [], "reason": "성능 검사 오류: %s" % e}
            res["perf"] = perf
            if perf.get("status") in ("perf_regression", "perf_unmeasured"):
                res["status"] = perf["status"]
                res["reason"] = "속도 검사 실패: " + " · ".join(
                    "%s %sms (%s)" % (r["name"], r.get("ms"), r.get("reason") or "측정 실패")
                    for r in perf.get("items", []) if r.get("verdict") != "pass")
    stamp = cwd / SYNTAX_STAMP
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
# 2026-11-14: 매개변수 id 에 공백이 있으면 (예: [cd /c/x; git push origin main-True]) \S+ 가 못 읽어
#   실패 0건으로 집계 → rc=1 '실행 오류' blocked 로 오분류되고 기준선 비교(신규 회귀 판정)를 못 했다
_RX_FAILED = re.compile(r"^(?:FAILED|ERROR) (.+?\.py::.+?)(?: - .*)?$", re.M)
_RX_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")   # 대상 pytest.ini 의 --color=yes 가 'FAILED' 앞에 색 코드를 붙였다(11-13: 60 failed 인데 failures [])


FRESH_PYC_DIR = "orca-fresh-pyc"


def fresh_source_env(cwd) -> Dict[str, str]:
    """시험 대상 소스는 늘 새로 컴파일하고, 표준 라이브러리·pytest 는 캐시를 재사용하는 환경 변수 (R334).
    종전(11-13·11-18): 쓰기 금지 + 매번 빈 캐시 폴더 → 대상 코드뿐 아니라 pytest·표준 라이브러리까지 매 실행 다시 컴파일해
    가장 느린 시험 2개(94초)의 대부분이 이 컴파일이었다. 이제 공유 캐시 폴더(PYTHONPYCACHEPREFIX)를 쓰되, 실행 직전에
    그 안의 대상 폴더(cwd) 사본 부분만 지운다 → '같은 초·같은 크기로 고친 파일을 옛 .pyc 로 판정' 하던 조건은 그대로 막힌다
    (캐시 폴더를 지정하면 파이썬은 소스 옆 __pycache__ 를 읽지 않는다 · 공식 문서 PYTHONPYCACHEPREFIX).
    지우는 곳은 임시 폴더 아래 이 함수가 만든 캐시뿐이다 (대상 저장소 파일은 건드리지 않음)."""
    import shutil
    import tempfile as _tf
    prefix = os.path.join(_tf.gettempdir(), FRESH_PYC_DIR)
    stamp = os.path.join(prefix, ".created")
    try:   # 상한: 시험 임시 폴더 사본이 쌓이므로 7일마다 통째로 비운다 (다음 실행이 캐시를 한 번 다시 만든다)
        import time as _time
        if os.path.isfile(stamp) and _time.time() - os.path.getmtime(stamp) > 7 * 86400:
            shutil.rmtree(prefix, ignore_errors=True)
        if not os.path.isfile(stamp):
            os.makedirs(prefix, exist_ok=True)
            open(stamp, "w").close()
    except OSError:
        pass
    rel = os.path.splitdrive(os.path.abspath(str(cwd)))[1].lstrip("\\/")   # 파이썬이 캐시 경로를 만들 때 드라이브를 뗀다
    mirror = os.path.join(prefix, rel) if rel else ""
    if mirror and os.path.isdir(mirror):
        shutil.rmtree(mirror, ignore_errors=True)
    return {"PYTHONPYCACHEPREFIX": prefix}


def _pytest_failures(cwd: Path, tests: List[str], timeout: int, nopyc: bool = False):
    """(실패 nodeid 집합, 요약 줄, 종료 코드) — 시험 파일만 넘긴다. 0 통과 · 1 실패 · 5 수집 0 · 그 외 실행 오류.
    nopyc=True (R314): 바이트코드 캐시를 쓰지도 읽지도 않음 — 같은 초·같은 크기로 고친 시험을 옛 .pyc 로 판정하지 않게
    (반례 재실행·해결 시험처럼 '지금 실행한 결과' 만 증거로 인정하는 호출 · real_repair_chain._nopyc_env 와 같은 방식)."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    if nopyc:
        # R334: 종전 '쓰기 금지 + 매번 빈 폴더' (임시 폴더 잔여 0) 대신 대상 사본만 지우는 공유 캐시
        env.update(fresh_source_env(cwd))
    env.pop("CLAUDE_PROJECT_DIR", None)   # 기준선 사본(worktree)에서 시험이 자기 위치를 ROOT 로 쓰게
    r = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no", "-rfE",
                        "--color=no", *tests], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, env=env)
    out = _RX_ANSI.sub("", r.stdout + r.stderr)
    fails = {m.replace("\\", "/") for m in _RX_FAILED.findall(out)}
    summary = (out.strip().splitlines() or [""])[-1][:200]
    return fails, summary, r.returncode

def code_fingerprint(cwd: Path) -> str:
    """스테이징(index)된 코드 파일만의 지문 — 문서(CLAUDE.md AUTO-STATS·guide.txt)만 더 stage 해도 그대로다.
    lottoclaude 11-16 21:40: 전체 회귀(7분 15초) 통과 직후 커밋 훅이 CLAUDE.md 날짜 한 줄 stage 를 요구 → 트리 해시가 바뀌어
    stale → 재실행 중 dev 회차 61분 시간 초과. pre-commit-full-check.sh 가 같은 식으로 계산해 비교한다."""
    import hashlib
    rows = [ln for ln in (_run_git_in(cwd, ["-c", "core.quotepath=off", "ls-files", "-s"]) or "").splitlines()
            if ln.split("\t")[-1].lower().endswith(_CODE_EXT)]
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest() if rows else ""


def _gate_timeout() -> int:
    """2026-11-12 (R245): 900초 고정이던 상한이 영향 시험 14개(이 PC 부하 시 1,527초 실측)보다 짧아
    실패 0건인데도 늘 시간 초과 BLOCKED → 커밋 불가 순환. 검사 범위·통과 기준은 그대로, 상한만 늘리고 조정 가능하게."""
    try:
        return max(60, int(os.environ.get("REGRESSION_GATE_TIMEOUT_SEC", "2400")))
    except ValueError:
        return 2400


PERF_BUDGET = ".claude/config/perf-budget.json"          # kit 공통 항목 (전파됨)
PERF_BUDGET_LOCAL = ".claude/config/perf-budget.local.json"   # 대상 프로젝트 고유 항목 (페이지·DB · 전파 안 됨)
PERF_BASELINE = ".claude/state/perf-baseline.json"


def _perf_items(cwd: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for rel in (PERF_BUDGET, PERF_BUDGET_LOCAL):
        try:
            items += json.loads((cwd / rel).read_text(encoding="utf-8")).get("items", [])
        except (OSError, ValueError, AttributeError):
            continue
    return [i for i in items if isinstance(i, dict) and i.get("name") and i.get("cmd")]


def _perf_measure(cwd: Path, item: Dict[str, Any]) -> Optional[float]:
    """명령을 runs 회 실행한 실행 시간 중앙값(ms) · 실패(종료 코드≠0·시간 초과) = None (측정 실패 = 통과 아님)."""
    import statistics
    import time as _t
    shell = isinstance(item["cmd"], str)
    times = []
    for _ in range(max(1, int(item.get("warmup", 1)))):
        try:
            subprocess.run(item["cmd"], cwd=str(cwd), shell=shell, input=item.get("stdin", ""), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=float(item.get("timeout_s", 30)))
        except (OSError, subprocess.SubprocessError):
            return None
    for _ in range(max(3, int(item.get("runs", 5)))):
        t0 = _t.perf_counter()
        try:
            r = subprocess.run(item["cmd"], cwd=str(cwd), shell=shell, input=item.get("stdin", ""), capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=float(item.get("timeout_s", 30)))
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode != 0:
            return None
        times.append((_t.perf_counter() - t0) * 1000)
    return round(statistics.median(times), 1)


PERF_SAMPLES = 7          # 기준선 = 최근 통과 측정 7개의 중앙값 (2026-11-18 R303 실측: 상태줄 같은 방식 8회 387~524ms · 폭 35%)
PERF_MIN_REGRESS_MS = 60  # 기준선 대비 이만큼 이상 느려져야 차단 (비율만 보면 작은 값은 잡음으로 넘음)


def _perf_baseline_ms(entry: Optional[Dict[str, Any]]) -> Optional[float]:
    """기준선 = 최근 통과 측정값들의 중앙값 · 옛 형식 {"ms"} 도 읽음 · 운 좋게 빨랐던 1회에 기준이 끌려 내려가지 않게."""
    import statistics
    if not entry:
        return None
    vals = [float(v) for v in (entry.get("samples") or []) if v]
    if not vals and entry.get("ms"):
        vals = [float(entry["ms"])]
    return round(statistics.median(vals), 1) if vals else None


def perf_gate(cwd: Path, staged: List[str]) -> Dict[str, Any]:
    """R295·R296 성능 회귀 게이트 — 바뀐 파일과 관련된 속도 항목(상태줄·페이지·DB 등)만 재서 느려지면 커밋 차단.

    항목 = perf-budget.json(kit) + perf-budget.local.json(대상 고유) 의 items:
      {"name", "cmd"(문자열=셸·목록=직접 실행), "triggers"(바뀐 파일 glob 목록 · 없으면 항상), "budget_ms"(절대 상한),
       "max_regress_pct"(기준선 대비 허용 · 기본 30), "min_regress_ms"(절대 허용 폭 · 기본 60), "runs", "warmup", "stdin", "timeout_s"}
    판정: 상한 초과 또는 기준선 대비 허용 초과 → 1번 다시 재서 그래도 초과면 perf_regression · 측정 실패 = perf_unmeasured(차단).
    기준선 = 최근 통과 측정 7개 중앙값 (R303 · 옛 방식은 마지막 통과값 1개라 빠른 1회에 끌려 내려가 거짓 차단) (.claude/state/perf-baseline.json · 통과할 때만 갱신 · 기계 부하로 흔들리는 값을 그대로 기준 삼지 않게
    처음 측정은 기준선만 저장)."""
    import fnmatch
    out: Dict[str, Any] = {"items": [], "status": "pass"}
    items = _perf_items(cwd)
    if not items:
        out["status"] = "none"
        return out
    try:
        base = json.loads((cwd / PERF_BASELINE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        base = {}
    for it in items:
        trig = it.get("triggers") or []
        hit = not trig or any(fnmatch.fnmatch(p, g) for p in staged for g in trig)
        if not hit:
            continue
        ms = _perf_measure(cwd, it)
        rec: Dict[str, Any] = {"name": it["name"], "ms": ms, "baseline_ms": _perf_baseline_ms(base.get(it["name"])),
                               "budget_ms": it.get("budget_ms")}
        if ms is None:
            rec["verdict"] = "unmeasured"
            out["items"].append(rec)
            continue
        pct = float(it.get("max_regress_pct", 30))
        min_abs = float(it.get("min_regress_ms", PERF_MIN_REGRESS_MS))

        def _over(v: float) -> Optional[str]:
            if it.get("budget_ms") and v > float(it["budget_ms"]):
                return "상한 %sms 초과" % it["budget_ms"]
            b = float(rec["baseline_ms"] or 0)
            if b and v > b * (1 + pct / 100) and v - b > min_abs:   # 비율과 절대 폭 둘 다 넘어야 (작은 값의 잡음 차단 방지)
                return "기준선 %sms 대비 %d%%·%dms 초과" % (rec["baseline_ms"], pct, min_abs)
            return None
        why = _over(ms)
        if why:   # 기계 부하로 한 번 튄 값일 수 있어 1번 더 잰다 · 둘 중 작은 값으로 판정
            ms2 = _perf_measure(cwd, it)
            if ms2 is not None:
                rec["ms_retry"] = ms2
                ms = min(ms, ms2)
                why = _over(ms)
        rec["ms"] = ms
        rec["verdict"] = "regression" if why else "pass"
        if why:
            rec["reason"] = why
        out["items"].append(rec)
    if any(r["verdict"] == "regression" for r in out["items"]):
        out["status"] = "perf_regression"
    elif any(r["verdict"] == "unmeasured" for r in out["items"]):
        out["status"] = "perf_unmeasured"
    else:
        import time as _t
        for r in out["items"]:
            prev = base.get(r["name"]) or {}
            samples = (list(prev.get("samples") or ([prev["ms"]] if prev.get("ms") else [])) + [r["ms"]])[-PERF_SAMPLES:]
            base[r["name"]] = {"ms": _perf_baseline_ms({"samples": samples}), "samples": samples, "at": int(_t.time())}
        try:
            p = cwd / PERF_BASELINE
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, p)
        except OSError:
            pass
    if not out["items"]:
        out["status"] = "not_triggered"
    return out


def risk_tier(sel: Dict[str, Any]) -> str:
    """R336 위험 등급 (표기 · 선택 규칙은 impact_selection 그대로): high = 전체 회귀 (고위험 파일·공통 모듈·실행 기반·계약·
    범위 불명·사용자 명시) · medium = 호출자·동반 수정 근거로 고른 시험 · low = 바뀐 시험 자신만 / 영향 시험 없음."""
    if sel.get("full"):
        return "high"
    why = sel.get("why") or {}
    return "medium" if any(v != "변경된 시험" for v in why.values()) else "low"


def staging_preflight(cwd: Path) -> Optional[List[str]]:
    """R350: 시험 전에 커밋 훅(pre-commit-full-check.sh)을 미리보기로 돌려 동반 파일 누락을 한 번에 받는다.

    종전: 회귀 게이트(수 분) → 커밋 → 훅이 그제야 marketplace·guide 누락 발견 → stage → 지문 바뀜 → 게이트 재실행 (세션 실측 3회).
    정본은 훅 하나 (같은 규칙을 여기 다시 쓰지 않음) · None = 훅 없음/bash 없음/실행 실패 (판정 안 함 · 커밋 때 훅이 그대로 검사)."""
    import shutil
    hook = Path(cwd) / ".claude" / "hooks" / "pre-commit-full-check.sh"
    bash = shutil.which("bash")
    if not hook.is_file() or not bash:
        return None
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(cwd), "PRECOMMIT_PREFLIGHT": "1"}
    try:
        r = subprocess.run([bash, hook.as_posix()], input=json.dumps({"tool_input": {"command": "git commit"}}),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(cwd), timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode == 0:
        return []
    if r.returncode != 2:
        return None
    return [ln.strip()[2:] for ln in (r.stderr or "").splitlines() if ln.strip().startswith("- ")]


def regression_gate(cwd: Path, timeout: Optional[int] = None, force_full: bool = False) -> Dict[str, Any]:
    """회귀 방지 게이트 (2026-11-09 · 사용자 지시: A 를 고쳐 B·C 가 깨지는 것을 커밋 전에 막는다).

    스테이징된 코드 변경 → affected_tests 로 영향 시험 선정 → 실행.
    실패가 있으면 수정 전(HEAD) 사본(git worktree)에서 같은 시험을 돌려 '원래 있던 실패' 와 '이번 변경으로 생긴 회귀' 를 가른다.
    결과는 스테이징 트리 해시와 함께 REGRESSION_STAMP 에 기록 → pre-commit-full-check.sh 가 해시 일치·상태만 확인 (훅 5초 제한).
    status: skip(코드 변경 없음) · pass · preexisting(실패 전부 HEAD 에서도 실패) · regression(신규 실패 · 커밋 차단) · blocked(실행 불가)."""
    import tempfile
    import time as _t
    if timeout is None:
        timeout = _gate_timeout()
    tree = (_run_git_in(cwd, ["write-tree"]) or "").strip()
    staged = [p.strip() for p in (_run_git_in(cwd, ["diff", "--cached", "--name-only"]) or "").splitlines() if p.strip()]
    code = [p for p in staged if p.lower().endswith(_CODE_EXT)]
    res: Dict[str, Any] = {"tree": tree, "code_tree": code_fingerprint(cwd), "at": int(_t.time()), "changed_code": code,
                           "tests": [], "failures": [], "baseline_failures": [], "new_failures": []}
    try:   # R352: 직전 게이트들의 '실행 중 commit 증가량' 이력을 이어받음 (메모리 판정의 예상 사용량 근거)
        _prev = json.loads((cwd / REGRESSION_STAMP).read_text(encoding="utf-8"))
        if isinstance(_prev.get("memory_history"), list):
            res["memory_history"] = [x for x in _prev["memory_history"] if isinstance(x, (int, float))][-5:]
    except (OSError, ValueError, AttributeError):
        pass
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import repair_sandbox as _sb
        res["commit_memory_pct"] = (_sb.commit_memory() or {}).get("percent")
    except Exception:  # noqa: BLE001 — 측정 실패는 기록만 (시험 생략 사유로 쓰지 않는다)
        res["commit_memory_pct"] = None
    syn = staged_syntax_check(cwd, code) if (tree and code) else {"errors": [], "checked": [], "unchecked": []}
    if not tree:
        res["status"] = "blocked"
        res["reason"] = "스테이징 트리 해시를 못 얻음 (병합 충돌 중?)"
        _syntax_verdict(res, {"errors": [], "checked": [], "unchecked": []})
    elif not code:
        res["status"] = "skip"
        _syntax_verdict(res, syn)
    elif _syntax_verdict(res, syn):
        pass   # syntax_error · unverified = 시험 결과와 무관하게 커밋 차단 — 고친 뒤 게이트 재실행
    elif os.environ.get("REGRESSION_GATE_NO_PREFLIGHT") != "1" and (missing := staging_preflight(cwd)):
        # R350: 동반 파일이 빠진 스테이징으로 시험을 돌리면, 채워 넣는 순간 지문이 바뀌어 같은 시험을 또 돌린다 → 시험 전에 한 번에 알림
        res["status"] = "incomplete_staging"
        res["missing"] = missing
        res["reason"] = "커밋 동반 파일 누락 — 모두 stage 한 뒤 게이트를 한 번만 실행: " + " · ".join(missing)
    else:
        unstaged = set((_run_git_in(cwd, ["diff", "--name-only"]) or "").split())
        dirty = sorted(set(code) & unstaged)
        tests, runners = [], []
        sel = impact_selection(cwd, staged)
        if force_full and not sel["full"]:   # R336: 사용자 명시 '전체 테스트' (--full · REGRESSION_GATE_FULL=1) 는 예외 없이 전체
            sel["full"] = "사용자 명시 전체 회귀 (--full)"
        res["full"] = sel["full"]
        res["why"] = sel["why"]
        res["risk_tier"] = risk_tier(sel)
        for t in sel["tests"]:
            if not t.endswith(".py"):
                continue
            # 파일을 직접 넘기면 pytest 가 conftest collect_ignore 를 적용하지 않아 자체 main() 러너가 오류로 잡힌다
            #   (2026-11-09 실측: phase2·3·5 러너 33 errors) → 같은 폴더 conftest 의 collect_ignore 는 따로 표시
            conf = cwd / Path(t).parent / "conftest.py"
            try:
                ignored = Path(t).name in conf.read_text(encoding="utf-8", errors="replace") and re.search(
                    r"collect_ignore\s*=\s*\[[^\]]*['\"]%s['\"]" % re.escape(Path(t).name),
                    conf.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                ignored = False
            (runners if ignored else tests).append(t)
        if sel["full"]:
            # 전체 회귀 = 공식 시험 범위 (pytest.ini testpaths) · 없으면 시험 파일 폴더 단위
            #   (폴더를 넘겨야 conftest collect_ignore 가 적용된다 · 범위 밖 잔여 파일은 실행하지 않는다)
            tests = _configured_test_dirs(cwd)
            res["runners_not_run"] = []
            runners = []
        res["tests"] = tests
        res["runners_not_run"] = runners
        res["same_pattern"] = same_pattern_candidates(cwd, limit=10)
        mem_block = _wait_memory_for_heavy(res) if (sel["full"] and tests and not dirty) else None
        if sel["full"] and not tests and not dirty:
            res["status"] = "blocked"
            res["reason"] = "전체 회귀가 필요하지만 실행할 시험 폴더를 찾지 못함 (pytest.ini testpaths 확인)"
        elif mem_block:
            res["status"] = "blocked"
            res["reason"] = mem_block
        elif dirty:
            res["status"] = "blocked"
            res["reason"] = "스테이징 안 된 수정이 남은 코드 파일 — 시험 대상과 커밋 내용이 다름: %s" % ", ".join(dirty[:5])
        elif not tests:
            res["status"] = "pass"
            res["reason"] = "영향 시험 없음 (affected_tests 0건) — 새 시험 필요 여부는 독립 검토로 판단"
        else:
            watch = _CommitWatch()
            try:
                with watch:
                    fails, summary, rc = _pytest_failures(cwd, tests, timeout)
            except subprocess.TimeoutExpired:
                fails, summary, rc = set(), "시간 초과 %ds" % timeout, -1
            mem = watch.summary()
            if mem:   # R352: 예상 추가 사용량 실측 (전체 회귀만 이력에 남김 — 부분 시험과 섞지 않음)
                res["memory_during"] = mem
                if sel["full"]:
                    res["memory_history"] = (res.get("memory_history") or [])[-4:] + [mem["used_gb"]]
            res["summary"] = summary
            res["failures"] = sorted(fails)
            if rc == 5:
                # pytest 종료 코드 5 = 시험 0건 수집 (공식 문서 · Exit codes) — 아무것도 검사 안 했으므로 통과 아님
                res["status"] = "blocked"
                res["reason"] = "선정된 시험이 하나도 수집되지 않음 (pytest rc=5) — %s" % summary
            elif rc not in (0, 1) or (rc == 1 and not fails):
                res["status"] = "blocked"
                res["reason"] = "시험 실행 오류 (rc=%s) — %s" % (rc, summary)
            elif not fails:
                res["status"] = "pass"
            else:
                base_dir = Path(tempfile.mkdtemp(prefix="regress-base-"))
                wt = base_dir / "wt"
                try:
                    if _run_git_in(cwd, ["worktree", "add", "--detach", str(wt), "HEAD"], timeout=600) is None:
                        raise RuntimeError("worktree 생성 실패")
                    # 기준선은 '작업 트리에서 실패한 시험' 만 다시 돌린다 — 비교는 fails - bfails 뿐이다(11-13: 범위 전체를
                    #   돌리다 HEAD 쪽 conftest 에 없는 옵트인 탓에 e2e 161개까지 돌아 900초 시간 초과로 커밋이 막혔다).
                    #   200개를 넘으면 명령줄 길이 때문에 파일 단위로 묶는다.
                    picks = sorted(fails) if len(fails) <= 200 else sorted({f.split("::")[0] for f in fails})
                    base_tests = [t for t in picks if (wt / t.split("::")[0]).exists()]
                    bfails, bsummary, _brc = _pytest_failures(wt, base_tests, timeout) if base_tests else (set(), "", 5)
                    res["baseline_summary"] = bsummary
                    res["baseline_failures"] = sorted(bfails)
                    res["new_failures"] = sorted(fails - bfails)
                    res["status"] = "regression" if res["new_failures"] else "preexisting"
                except Exception as e:  # noqa: BLE001 — 기준선 못 돌리면 신규 여부를 모른다 → 차단
                    res["status"] = "blocked"
                    res["reason"] = "기준선(HEAD) 시험 실행 불가: %s" % e
                finally:
                    _run_git_in(cwd, ["worktree", "remove", "--force", str(wt)], timeout=600)
                    try:
                        base_dir.rmdir()
                    except OSError:
                        pass
    if res.get("status") in ("pass", "preexisting"):   # R295·R296 시험이 통과한 변경만 속도 검사 (실패는 이미 차단)
        try:
            perf = perf_gate(cwd, staged)
        except Exception as e:  # noqa: BLE001 — 검사 자체가 깨지면 통과로 보지 않는다
            perf = {"status": "perf_unmeasured", "items": [], "reason": "성능 검사 오류: %s" % e}
        res["perf"] = perf
        if perf.get("status") in ("perf_regression", "perf_unmeasured"):
            res["status"] = perf["status"]
            bad = [r for r in perf.get("items", []) if r.get("verdict") != "pass"]
            res["reason"] = "속도 검사 실패: " + " · ".join(
                "%s %sms (%s)" % (r["name"], r.get("ms"), r.get("reason") or "측정 실패") for r in bad)
    stamp = cwd / REGRESSION_STAMP
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    try:  # §78 회귀 결과를 현재 요청 추적에 (근거 = regression-gate.json)
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("_gate_trace", str(Path(__file__).resolve().with_name("trace.py")))
        tm = ilu.module_from_spec(spec)
        spec.loader.exec_module(tm)
        st = {"pass": "success", "fail": "fail", "blocked": "blocked", "syntax_error": "fail", "regression": "fail",
              "unverified": "blocked", "preexisting": "success", "skip": "success"}.get(str(res.get("status")), "unknown")
        # R341: 시험이 임시 저장소에서 부른 게이트도 운영 추적(kit logs/trace-events.jsonl)에 쌓여 상태줄 «검증skip» 이 부풀었다
        #   (24시간 blocked·unknown 609건 중 거의 전부가 src/mod.py·deploy.bat·메모리 95% 1초 같은 시험 기록) →
        #   게이트를 돌린 저장소가 추적 대상 프로젝트일 때만 기록한다.
        try:
            same = Path(cwd).resolve() == Path(tm._root()).resolve()
        except Exception:  # noqa: BLE001
            same = False
        if not same:
            return res
        tm.emit("test", step="regression-gate", status=st, error=res.get("reason"), evidence=str(REGRESSION_STAMP),
                detail={"summary": res.get("summary"), "new_failures": (res.get("new_failures") or [])[:10],
                        "tests": len(res.get("tests") or []), "memory_pct": res.get("commit_memory_pct")})
    except Exception:  # noqa: BLE001
        pass
    return res


def _check_scope(diff_paths: List[str], allow_paths: Optional[List[str]]) -> Dict[str, Any]:
    """scope-lock 통합 — allow_paths glob/prefix 외 수정 파일 탐지.

    allow_paths 가 None 이거나 빈 리스트 → 검사 skip (기존 호환).
    예: allow_paths=["src/", ".claude/scripts/"] → 둘 중 하나로 시작하는 파일만 허용.
    """
    if not allow_paths:
        return {"enforced": False, "violations": []}
    violations = []
    for p in diff_paths:
        matched = any(p == a or p.startswith(a.rstrip("/") + "/") or p.startswith(a)
                      for a in allow_paths)
        if not matched:
            violations.append(p)
    return {"enforced": True, "violations": violations,
            "allow_paths": list(allow_paths)}


def _executions_verified(task_id: str) -> Optional[bool]:
    """executions 테이블에서 해당 task 의 verified 플래그 재조회.
    - 독립 Verifier 는 개발 Agent 보고 (tasks.status) 를 그대로 안 믿고
      runner 가 mark_verified() 한 실제 플래그 확인.
    - 레코드 없음 → None (미실행 신호)
    - 마지막 execution 기준 (여러 번 재시도 가능)
    """
    if not DB.exists():
        return None
    try:
        with sqlite3.connect(str(DB)) as c:
            row = c.execute(
                "SELECT verified FROM executions WHERE task_id=? "
                "ORDER BY exec_id DESC LIMIT 1",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return bool(row[0])
    except Exception:
        return None


def collect_evidence(goal_id: int,
                     sandbox_cwd: Optional[str] = None,
                     allow_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """goal 1건의 evidence 수집 (DB · git · verifier 결과 · scope).

    Phase 2-C 완결 (2026-10-29):
      - sandbox_cwd 전달 시 git diff 를 sandbox 에서 수행
      - allow_paths 전달 시 scope-lock 검사 포함
      - executions.verified 재조회 (tasks.status 그대로 안 믿음)
    """
    evidence: Dict[str, Any] = {"goal_id": goal_id}
    if not DB.exists():
        return {**evidence, "error": "orca.db not found"}

    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT description, status, workflow_type, source_ref, failure_reason "
            "FROM goals WHERE goal_id=?",
            (goal_id,),
        ).fetchone()
        if not row:
            return {**evidence, "error": "goal not found"}
        evidence["description"] = row[0]
        evidence["status"] = row[1]
        evidence["workflow_type"] = row[2]
        evidence["source_ref"] = row[3]
        evidence["failure_reason"] = row[4]

        tasks = c.execute(
            "SELECT task_id, task_file, status FROM tasks "
            "WHERE task_id IN (SELECT task_id FROM goal_tasks WHERE goal_id=?)",
            (goal_id,),
        ).fetchall()

    task_specs: List[Dict] = []
    for tid, tfile, tstatus in tasks:
        try:
            spec = json.loads(tfile) if tfile else {}
        except Exception:
            spec = {}
        # 독립 재조회: executions.verified
        exec_verified = _executions_verified(tid)
        task_specs.append({
            "task_id": tid,
            "status": tstatus,
            "kind": spec.get("kind"),
            "cmd": spec.get("cmd"),
            "verify_type": spec.get("verify_type", "shell"),
            "verifier_id": spec.get("verifier_id"),
            "verify": spec.get("verify"),
            "risk": spec.get("risk"),
            "requires_user_approval": spec.get("requires_user_approval"),
            "executions_verified": exec_verified,  # None = 실행 기록 없음
        })
    evidence["tasks"] = task_specs
    evidence["task_count"] = len(task_specs)
    evidence["tasks_completed"] = sum(1 for t in task_specs if t["status"] == "completed")
    evidence["tasks_failed"] = sum(1 for t in task_specs if t["status"] == "failed")
    evidence["tasks_unverified"] = sum(
        1 for t in task_specs if t["status"] == "executed_unverified"
    )
    evidence["tasks_exec_verified"] = sum(
        1 for t in task_specs if t["executions_verified"] is True
    )
    evidence["tasks_exec_unverified_or_missing"] = sum(
        1 for t in task_specs if t["executions_verified"] is not True
    )

    # git diff · sandbox 우선 · 없으면 ROOT
    diff_cwd = Path(sandbox_cwd) if sandbox_cwd and Path(sandbox_cwd).exists() else ROOT
    evidence["diff_cwd"] = str(diff_cwd)
    evidence["diff_source"] = "sandbox" if sandbox_cwd and diff_cwd != ROOT else "root"
    diff_stat = _run_git_in(diff_cwd, ["diff", "--stat"])
    evidence["git_diff_stat"] = (diff_stat or "").strip()[:500] if diff_stat else None
    diff_paths = _collect_diff_paths(diff_cwd)
    evidence["git_diff_paths"] = diff_paths
    evidence["git_diff_file_count"] = len(diff_paths)
    evidence["changed_paths"] = changed_paths(diff_cwd)
    evidence["external_dependencies"] = external_dependencies(diff_cwd)
    evidence["same_pattern_candidates"] = same_pattern_candidates(diff_cwd)
    evidence["verified_output"] = _verified_output([t["task_id"] for t in task_specs])
    evidence["affected_tests"] = affected_tests(diff_cwd, evidence["changed_paths"])
    evidence["affected_tests_not_run"] = [t for t in evidence["affected_tests"]
                                          if Path(t).name not in evidence["verified_output"]]

    # scope 검사
    evidence["scope"] = _check_scope(diff_paths, allow_paths)

    return evidence


def judge(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """evidence 기반 독립 판정 (LLM 호출 X · 안전 default).

    Phase 2-C 완결 상태:
      - no tasks → UNVERIFIED
      - failed > 0 → REPAIRING
      - scope violation → OUT_OF_SCOPE (fail-closed)
      - executions 재조회 verified != task_count → UNVERIFIED
      - verifier 미등록 (verifier_id 없음) → UNVERIFIED
      - 모두 통과 → VERIFIED
    """
    reasons: List[str] = []
    task_count = evidence.get("task_count", 0)
    completed = evidence.get("tasks_completed", 0)
    failed = evidence.get("tasks_failed", 0)
    unverified = evidence.get("tasks_unverified", 0)
    exec_verified = evidence.get("tasks_exec_verified", 0)
    exec_unverified = evidence.get("tasks_exec_unverified_or_missing", 0)
    scope = evidence.get("scope") or {}
    tasks = evidence.get("tasks") or []

    if task_count == 0:
        return {"status": "UNVERIFIED", "reasons": ["no tasks registered"]}

    # scope 위반 — fail-closed · 다른 판정보다 우선
    if scope.get("enforced") and scope.get("violations"):
        v = scope.get("violations", [])
        reasons.append(f"scope violations ({len(v)} files outside allow_paths)")
        return {"status": "OUT_OF_SCOPE", "reasons": reasons,
                "violations": v[:20]}

    if failed > 0:
        reasons.append(f"{failed} tasks failed (per tasks.status)")
        return {"status": "REPAIRING", "reasons": reasons}
    if unverified > 0:
        reasons.append(f"{unverified} tasks executed but unverified (per tasks.status)")
        return {"status": "REPAIRING", "reasons": reasons}

    # 독립 재조회: executions.verified 가 task_count 와 일치해야.
    # 개발 Agent 가 tasks.status='completed' 로 바꿔도 executions.verified=0 이면 인정 X.
    if exec_unverified > 0:
        reasons.append(
            f"{exec_unverified}/{task_count} tasks lack verified executions "
            f"(executions.verified != 1 or missing)"
        )
        return {"status": "UNVERIFIED", "reasons": reasons}

    # verifier 등록 여부
    tasks_with_verifier = [t for t in tasks
                           if t.get("verifier_id") or t.get("verify_type") == "shell"]
    if not tasks_with_verifier:
        reasons.append("no verifier registered for any task")
        return {"status": "UNVERIFIED", "reasons": reasons}

    if completed == task_count and exec_verified == task_count:
        reasons.append(
            f"all {task_count} tasks completed · {exec_verified} executions verified "
            f"· scope {'OK' if scope.get('enforced') else 'unchecked'}"
        )
        return {"status": "VERIFIED", "reasons": reasons}

    reasons.append(f"only {completed}/{task_count} completed · exec_verified={exec_verified}")
    return {"status": "UNVERIFIED", "reasons": reasons}


JUDGE_QUEUE = ROOT / ".claude" / "state" / "judge-queue"


def judge_handoff(goal_id: int,
                  sandbox_cwd: Optional[str] = None,
                  allow_paths: Optional[List[str]] = None,
                  judge_notes: str = "",
                  requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """agent-01-judge subagent 호출용 context 생성 + judge-queue 저장.
    requirements = 요구사항 스냅샷 {path, sha256, ids} · handoff 에 저장해 judge_absorb 가 호출자와 무관하게 강제.

    Phase 3-R5 (사용자 지시 3307fcd 후속):
      - Independent Judge 보완 · agent-01-judge 재사용
      - 통계·evidence 기반 judge() 는 유지 · 그 위에 LLM 평가 연결
      - LLM 결과가 PASS 라도 테스트 실패 시 VERIFIED 금지 (judge() 가 선 판정)
      - Judge 미실행·근거 부족 → UNVERIFIED (안전 default)

    사용 흐름:
      1. supervisor.execute_goal 완료 후 이 함수 호출
      2. judge-queue 에 goal 별 context JSON 저장 (handoff file)
      3. 메인 Claude 가 Task tool 로 agent-01-judge subagent 호출 유도 (systemMessage)
      4. subagent 결과 (JSON score) 를 judge_absorb() 로 저장
      5. 최종 verdict = combine(statistical_judge, llm_judge, test_results)

    반환:
      - evidence · verdict (통계) · judge_prompt (subagent 호출용) · handoff_file 경로
    """
    JUDGE_QUEUE.mkdir(parents=True, exist_ok=True)
    evidence = collect_evidence(goal_id, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
    stat_verdict = judge(evidence)

    # 통계 verdict 가 이미 VERIFIED 가 아니면 LLM judge 로도 뒤집히지 않음 (안전 우선)
    requires_llm = (stat_verdict.get("status") == "VERIFIED")

    desc = evidence.get("description") or ""
    tasks = evidence.get("tasks") or []
    diff_stat = evidence.get("git_diff_stat") or "(no diff)"
    diff_paths = evidence.get("git_diff_paths") or []
    scope = evidence.get("scope") or {}

    judge_prompt = (
        f"# agent-01-judge · goal #{goal_id}\n\n"
        f"## 요구사항 원문 (사용자 요청)\n{desc[:600]}\n\n"
        f"## 실제 변경 (git diff)\n{diff_stat}\n\n"
        f"변경 파일 ({len(diff_paths)}): {', '.join(diff_paths[:10])}\n\n"
        f"## 회귀 후보 (변경 모듈을 참조하는 테스트)\n"
        f"전체 {len(evidence.get('affected_tests') or [])} · "
        f"이번 검증 미실행: {', '.join((evidence.get('affected_tests_not_run') or [])[:10]) or '없음'}\n\n"
        f"## 외부 의존 (새로 쓰는 패키지·의존성 파일)\n"
        f"{', '.join(evidence.get('external_dependencies') or []) or '없음'} — 공식 자료 대조는 external-evidence 기록으로만 인정\n\n"
        f"## 같은 유형 누락 후보 (고친 줄이 남은 위치)\n"
        + ("\n".join(f"- {c['line']} → {', '.join(c['where'])}" for c in (evidence.get("same_pattern_candidates") or [])[:5])
           or "없음") + "\n\n"
        f"## tasks 실행 결과\n"
        + "\n".join(
            f"  - {t['task_id']}: status={t['status']} verify={t.get('verify_type')} "
            f"exec_verified={t.get('executions_verified')}"
            for t in tasks
        )
        + f"\n\n## scope\n enforced={scope.get('enforced')} violations={scope.get('violations', [])[:5]}\n\n"
        f"## 통계 판정 (사전)\n{json.dumps(stat_verdict, ensure_ascii=False)}\n\n"
        f"## 요청\n"
        f"다음을 평가해 JSON 으로 반환해라:\n"
        f"  {{\n"
        f"    \"satisfies_requirement\": true|false,  // 요구사항 충족\n"
        f"    \"missing_requirements\": [\"<요구 사항 누락 목록>\"],\n"
        f"    \"unexpected_side_effects\": [\"<예상 밖 부작용>\"],\n"
        f"    \"scope_adequacy\": \"ok|too_narrow|too_broad\",\n"
        f"    \"confidence\": 0-10,\n"
        f"    \"recommendation\": \"VERIFIED|UNVERIFIED|REPAIRING|OUT_OF_SCOPE\",\n"
        f"    \"reasoning\": \"<한 단락>\"\n"
        f"  }}\n\n"
        f"지켜라:\n"
        f"  - 통계 판정이 VERIFIED 가 아니면 LLM 평가로 VERIFIED 승격 X (안전 우선)\n"
        f"  - 테스트 실패·exec_verified!=task_count 는 VERIFIED 금지\n"
        f"  - 근거 부족 (diff 비어있거나 요구사항 모호) → UNVERIFIED\n"
        f"  - 범위 외 수정 발견 → OUT_OF_SCOPE\n"
    )
    if judge_notes:
        judge_prompt += f"\n## 추가 노트\n{judge_notes}\n"

    handoff_file = JUDGE_QUEUE / f"goal-{goal_id}.json"
    handoff_data = {
        "goal_id": goal_id,
        "created_at": __import__("time").time(),
        "stat_verdict": stat_verdict,
        "evidence_summary": {
            "task_count": evidence.get("task_count"),
            "tasks_completed": evidence.get("tasks_completed"),
            "tasks_exec_verified": evidence.get("tasks_exec_verified"),
            "diff_file_count": evidence.get("git_diff_file_count"),
            "scope_enforced": scope.get("enforced"),
            "scope_violations": scope.get("violations", [])[:10],
        },
        "judge_prompt": judge_prompt,
        "external_dependencies": evidence.get("external_dependencies") or [],
        "affected_tests_not_run": evidence.get("affected_tests_not_run") or [],
        "requires_llm_judge": requires_llm,
        "status": "pending_llm_judge" if requires_llm else "stat_verdict_blocking",
    }
    if requirements:
        handoff_data["requirements"] = requirements
        # judge_absorb 가 요구사항별 근거를 실물과 대조할 기준 (LLM 이 쓴 문장이 아니라 git·runner 기록)
        handoff_data["evidence_anchors"] = {"root": evidence.get("diff_cwd"),
                                            "paths": evidence.get("changed_paths") or [],
                                            "verified_output": (evidence.get("verified_output") or "")[-8000:]}
    handoff_file.write_text(json.dumps(handoff_data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {
        "ok": True,
        "goal_id": goal_id,
        "handoff_file": str(handoff_file),
        "stat_verdict": stat_verdict,
        "requires_llm_judge": requires_llm,
        "judge_prompt_head": judge_prompt[:600],
    }


FACT_TAG_RULE = ("Label every factual claim: [확인] = observed here (file:line, test output), [예시] = illustrative, "
                 "[추정] = inference, [미확인] = not verified, [판독불가] = unreadable. Never present [추정]/[예시] as [확인]; "
                 "a requirement is met only with [확인] evidence. "
                 "Write every explanation, reason and report in Korean (한국어); keep code, commands, file paths, "
                 "identifiers, JSON keys and enum values in their original form.")
NON_FACT_TAGS = re.compile(r"\[(추정|예시|미확인|판독불가)\]")
_FACT_SPLIT = re.compile(r"(\[(?:확인|추정|예시|미확인|판독불가)\])")
_PATH_REF = re.compile(r"([\w./\\~-]+\.[A-Za-z]\w{0,7})(?::(\d+))?")
_TEST_REF = re.compile(r"\btest_\w+")


def _fact_text(evidence: str) -> str:
    """근거 문장에서 [추정]·[예시]·[미확인]·[판독불가] 구간을 뺀 나머지 — 부연 설명은 근거로 세지 않는다."""
    parts = _FACT_SPLIT.split(evidence)
    kept, skip = [], False
    for part in parts:
        if _FACT_SPLIT.fullmatch(part):
            skip = part != "[확인]"
        elif not skip:
            kept.append(part)
    return " ".join(kept)


def evidence_is_anchored(evidence: str, anchors: Dict[str, Any]) -> bool:
    """V1.1 B: [확인] 글자가 아니라 실물로 판정. 사실 구간에 아래 중 하나가 있어야 True.
    - 변경 파일 또는 verified 실행에 나온 파일의 실재 경로 (`:줄` 이 있으면 파일 줄 수 안)
    - verified 실행 기록에 나온 테스트 이름"""
    fact = _fact_text(evidence)
    output = anchors.get("verified_output") or ""
    if any(m.group(0) in output for m in _TEST_REF.finditer(fact)):
        return True
    root = Path(anchors.get("root") or ".")
    changed = [p.replace("\\", "/") for p in anchors.get("paths") or []]
    for m in _PATH_REF.finditer(fact):
        ref = m.group(1).replace("\\", "/").lstrip("./")
        rel = next((p for p in changed if p == ref or p.endswith("/" + ref)), None)
        if rel is None and ref in output.replace("\\", "/"):
            rel = ref
        if rel is None:
            continue
        target = (root / rel).resolve()
        if root.resolve() not in target.parents or not target.is_file():
            continue
        if m.group(2):
            with target.open(encoding="utf-8", errors="replace") as f:
                if not 1 <= int(m.group(2)) <= sum(1 for _ in f):
                    continue
        return True
    return False


def check_requirement_verdicts(llm_verdict: Dict[str, Any], required_ids: List[str],
                               anchors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Judge 의 요구사항별 판정을 LLM 문장과 무관하게 검사 (2026-11-03 F4).
    필수 ID 마다 status=met + 근거(evidence) 가 있어야 ok. unmet → REPAIRING · 누락·ID 불일치·근거 없음·확인 불가 → UNVERIFIED.
    anchors (judge_handoff 스냅샷) 가 있으면 근거가 실제 변경·실행 기록에 닿는지도 요구한다."""
    rows = llm_verdict.get("requirements")
    if not isinstance(rows, list):
        return {"ok": False, "status": "UNVERIFIED", "reason": "requirements verdict list missing"}
    by_id = {}
    for r in rows:
        if isinstance(r, dict) and isinstance(r.get("id"), str):
            by_id[r["id"].strip().upper()] = r
    unmet, unverifiable, missing, no_evidence, unanchored = [], [], [], [], []
    for rid in required_ids:
        r = by_id.get(rid.upper())
        if r is None:
            missing.append(rid)
            continue
        st = str(r.get("status", "")).strip().lower()
        if st == "unmet":
            unmet.append(rid)
        elif st != "met":
            unverifiable.append(rid)
        elif not str(r.get("evidence") or "").strip():
            no_evidence.append(rid)
        elif NON_FACT_TAGS.search(str(r.get("evidence"))) and "[확인]" not in str(r.get("evidence")):
            # V1.1 B: 예시·추정 설명 자체는 허용 · [확인] 근거 없이 [추정]·[예시]·[미확인]·[판독불가] 만으로 met 을 주장하는 경우만 차단
            unverifiable.append(rid)
        elif anchors is not None and not evidence_is_anchored(str(r.get("evidence")), anchors):
            unanchored.append(rid)
    unknown = sorted(set(by_id) - {i.upper() for i in required_ids})
    if unmet:
        return {"ok": False, "status": "REPAIRING", "reason": f"requirements unmet: {unmet}", "unmet": unmet}
    if missing or unverifiable or no_evidence or unanchored:
        return {"ok": False, "status": "UNVERIFIED",
                "reason": f"requirements not verified: missing={missing} unverifiable={unverifiable} "
                          f"no_evidence={no_evidence} unanchored={unanchored}"}
    return {"ok": True, "status": "VERIFIED", "checked": list(required_ids), "unknown_ids": unknown}


def judge_source(agent_run: Optional[Dict[str, Any]] = None, kind: str = "unattested") -> Dict[str, Any]:
    """V1.1 B: Judge 판정이 어디서 왔는지. 실제 LLM 실행 = Agent 세션 ID 와 청구 비용이 둘 다 있을 때만.
    그 외 (CLI stdin·손으로 쓴 JSON·mock) 는 내용이 같아도 실제 Judge 로 세지 않는다."""
    run = agent_run or {}
    if run.get("agent_session_id") and run.get("cost_usd") is not None:
        return {"kind": "llm_agent", "agent_session_id": run.get("agent_session_id"),
                "model": run.get("model"), "cost_usd": run.get("cost_usd")}
    return {"kind": "agent_unattested" if agent_run is not None else kind}


def judge_absorb(goal_id: int, judge_result_json: str,
                 required_ids: Optional[List[str]] = None,
                 source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """agent-01-judge subagent 결과를 받아 최종 verdict 결합.

    사용자 지시: "Judge 가 승인하더라도 필수 테스트 실패 시 VERIFIED 금지"
                "Judge 미실행·근거 부족 → UNVERIFIED"
    """
    try:
        llm_verdict = json.loads(judge_result_json)
    except Exception as e:
        return {"ok": False, "error": f"json parse: {e}"}
    handoff_file = JUDGE_QUEUE / f"goal-{goal_id}.json"
    if not handoff_file.exists():
        return {"ok": False, "error": f"handoff file not found: {handoff_file}"}
    try:
        data = json.loads(handoff_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"handoff read: {e}"}
    stat = data.get("stat_verdict") or {}
    # handoff 에 요구사항 스냅샷이 있으면 호출자가 ID 를 넘기지 않아도 강제 (CLI judge-absorb 우회 차단)
    if not required_ids:
        required_ids = (data.get("requirements") or {}).get("ids") or None
    # 안전 결합 규칙:
    #   - stat != VERIFIED → final = stat (LLM 으로 승격 X)
    #   - stat == VERIFIED AND llm.satisfies AND llm.confidence>=7 → VERIFIED
    #   - stat == VERIFIED AND NOT llm.satisfies → REPAIRING
    #   - llm 결과 파싱 실패·confidence 부족 → UNVERIFIED
    stat_status = stat.get("status")
    reasons = list(stat.get("reasons") or [])
    if stat_status != "VERIFIED":
        final = {"status": stat_status, "reasons": reasons + ["statistical judgment blocks VERIFIED"]}
    else:
        satisfies = llm_verdict.get("satisfies_requirement") is True
        try:
            confidence = int(llm_verdict.get("confidence", 0) or 0)
        except (TypeError, ValueError):
            confidence = 0          # 숫자가 아닌 confidence = 근거 부족 (예외로 체인을 죽이지 않음)
        rec = llm_verdict.get("recommendation", "")
        missing = llm_verdict.get("missing_requirements") or []
        unexpected = llm_verdict.get("unexpected_side_effects") or []
        # 2026-11-03: Judge 가 스스로 VERIFIED 를 권고하지 않았거나(누락 포함) 누락 요구사항·범위 문제를 적었는데
        #   satisfies=true·confidence≥7 만으로 VERIFIED 로 새던 5가지 경우를 막는다 (fail-closed).
        if satisfies and (missing or llm_verdict.get("scope_adequacy", "ok") != "ok"):
            satisfies = False
        if not satisfies:
            final = {"status": "REPAIRING",
                     "reasons": reasons + [f"llm judge: not satisfied ({len(missing)} missing)"]}
        elif confidence < 7:
            final = {"status": "UNVERIFIED",
                     "reasons": reasons + [f"llm judge confidence {confidence} < 7"]}
        elif rec == "OUT_OF_SCOPE":
            final = {"status": "OUT_OF_SCOPE",
                     "reasons": reasons + ["llm judge detected scope violation"]}
        elif unexpected:
            final = {"status": "REPAIRING",
                     "reasons": reasons + [f"llm judge: {len(unexpected)} unexpected side effects"]}
        elif rec != "VERIFIED":
            final = {"status": rec if rec in ("UNVERIFIED", "REPAIRING") else "UNVERIFIED",
                     "reasons": reasons + [f"llm judge recommendation {rec or 'missing'} (not VERIFIED)"]}
        elif required_ids and not (rq := check_requirement_verdicts(llm_verdict, required_ids,
                                                                    data.get("evidence_anchors")))["ok"]:
            final = {"status": rq["status"], "reasons": reasons + [rq["reason"]]}
        else:
            final = {"status": "VERIFIED",
                     "reasons": reasons + [
                         f"llm judge confirms (conf={confidence})",
                         f"missing={len(missing)} unexpected={len(unexpected)}"]}
    # V1.1 B: 외부 근거·내부 구현·실행 결과는 별개 축 — 외부 근거 미확인이면 테스트가 통과해도 VERIFIED 금지
    ext = external_scope(data.get("external_dependencies") or [])
    final["external_scope"] = ext["scope"]
    if ext["unchecked"] and final["status"] == "VERIFIED":
        final = {**final, "status": "UNVERIFIED",
                 "reasons": final["reasons"] + [f"external source not checked: {ext['unchecked']}"]}
    # 2026-11-06: 변경을 참조하는 회귀 시험이 실행 기록(verified)에 없으면 실행 증거 누락 → VERIFIED 금지
    not_run = data.get("affected_tests_not_run") or []
    final["regression_scope"] = "not_run" if not_run else "run_or_none"
    if not_run and final["status"] == "VERIFIED":
        final = {**final, "status": "UNVERIFIED",
                 "reasons": final["reasons"] + [f"affected regression tests not run: {not_run[:10]}"]}
    # 검증 범위 표시: 요구사항별로 확인했는지, 요구사항 없이 diff·테스트로만 판정했는지
    final["requirements_scope"] = "checked" if required_ids else "not_configured"
    # Mock·수동 판정과 실제 LLM Judge 를 분리 기록 (판정 결과는 바꾸지 않음 · 감사 시 구분용)
    final["judge_source"] = source or judge_source()
    data["llm_verdict"] = llm_verdict
    data["final_verdict"] = final
    data["status"] = "completed"
    handoff_file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {"ok": True, "goal_id": goal_id, "final_verdict": final,
            "stat_verdict": stat, "llm_verdict": llm_verdict}


_REVIEW_LINE = re.compile(r"^\s*\[?(PASS|FAIL|WARN|BLOCK)\]?[\s:\-]+(.*)$", re.I | re.M)
_EXEC_EVIDENCE = re.compile(r"\bexit(?:\s*code)?\s*[:=]?\s*\d+|\b\d+\s+passed\b|\breturncode\s*[:=]?\s*\d+", re.I)


def review_verdict(text: str) -> Dict[str, Any]:
    """Gemini 등 외부 검증 보고서 판정 (2026-11-06). 'PASS' 글자 존재가 아니라 줄 단위:
    FAIL·BLOCK 줄 1개라도 → FAIL · PASS 줄 0개 → UNVERIFIED · 실행 출력(exit N · N passed) 없는 PASS 줄 → UNVERIFIED."""
    rows = [(m.group(1).upper(), m.group(2)) for m in _REVIEW_LINE.finditer(text or "")]
    fails = [r for r in rows if r[0] in ("FAIL", "BLOCK")]
    passes = [r for r in rows if r[0] == "PASS"]
    if fails:
        return {"ok": False, "status": "FAIL", "reason": f"{len(fails)} FAIL/BLOCK line(s)"}
    if not passes:
        return {"ok": False, "status": "UNVERIFIED", "reason": "no PASS line"}
    no_exec = [r[1][:80] for r in passes if not _EXEC_EVIDENCE.search(r[1]) or re.search(r"\bUNVERIFIED\b", r[1])]
    if no_exec:
        return {"ok": False, "status": "UNVERIFIED",
                "reason": f"{len(no_exec)}/{len(passes)} PASS line(s) without execution output", "lines": no_exec[:5]}
    return {"ok": True, "status": "VERIFIED", "passes": len(passes)}


_FINAL_CLAIM = re.compile(r"(?:최종\s*판정|final\s*verdict)[^\n]*?\b(PASS|PARTIAL|BLOCKED|FAIL)\b", re.I)


def codex_check(cwd: Path, report: Optional[Path] = None, timeout: int = 300) -> Dict[str, Any]:
    """Codex 등 외부 구현 결과 대조 (2026-11-06): 변경을 참조하는 pytest 시험을 실제 실행 + 보고서 최종 판정과 비교.
    스크립트형(`__main__`) 시험은 운영 상태에 쓸 수 있어 자동 실행하지 않고 미실행으로 남긴다.
    FAIL = 회귀 실패 또는 보고서가 FAIL · PARTIAL = 보고서 없음·판정 없음·PASS 주장인데 실행 증거/미실행 시험 · PASS = 그 외."""
    cwd = Path(cwd)
    changed = changed_paths(cwd)
    tests = [t for t in affected_tests(cwd, changed) if t.endswith(".py") and (cwd / t).is_file()]
    results, not_run = [], []
    for t in tests:
        if "__main__" in (cwd / t).read_text(encoding="utf-8", errors="replace"):
            not_run.append(t)
            continue
        try:
            # 11-13: 같은 초에 같은 크기로 고친 파일은 옛 __pycache__ 가 그대로 쓰여(파이썬은 시각(초)·크기로만 비교)
            #   고친 코드가 아닌 옛 코드로 판정했다 — 쓰지 않고(-B), 읽는 곳도 빈 임시 폴더로 돌려 늘 현재 소스로 돌린다.
            env = {**os.environ, **fresh_source_env(cwd)}   # R334: 대상만 새로 컴파일 · pytest·표준 라이브러리는 캐시
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", t], cwd=str(cwd),
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                               env=env)
            results.append({"test": t, "exit_code": r.returncode, "tail": (r.stdout or "")[-200:]})
        except subprocess.TimeoutExpired:
            results.append({"test": t, "exit_code": None, "tail": f"timeout {timeout}s"})
    failed = [x["test"] for x in results if x["exit_code"] != 0]
    text = report.read_text(encoding="utf-8", errors="replace") if report and Path(report).is_file() else ""
    m = _FINAL_CLAIM.search(text)
    claimed = m.group(1).upper() if m else None
    out = {"changed": changed, "tests": results, "not_run": not_run, "report": str(report) if report else None,
           "claimed": claimed}
    if failed:
        return {**out, "status": "FAIL", "reason": f"regression failed: {failed}"}
    if claimed == "FAIL":
        return {**out, "status": "FAIL", "reason": "report final verdict FAIL"}
    if not text:
        return {**out, "status": "PARTIAL", "reason": "implementation report missing"}
    if claimed is None:
        return {**out, "status": "PARTIAL", "reason": "report has no final verdict (PASS/PARTIAL/BLOCKED/FAIL)"}
    if claimed == "PASS" and not_run:
        return {**out, "status": "PARTIAL", "reason": f"report claims PASS but related tests not run: {not_run}"}
    if claimed == "PASS" and not _EXEC_EVIDENCE.search(text):
        return {**out, "status": "PARTIAL", "reason": "report claims PASS without execution output (exit N / N passed)"}
    return {**out, "status": claimed, "reason": "regression ok · report verdict consistent"}


def _cli_main(argv):
    """CLI: `independent_verifier.py <goal_id> [--sandbox PATH] [--allow PATH1,PATH2]`"""
    if len(argv) < 2:
        print("usage: independent_verifier.py <goal_id> [--sandbox PATH] [--allow P1,P2]")
        print("       independent_verifier.py judge-handoff <goal_id> [--sandbox PATH] [--allow P1,P2]")
        print("       independent_verifier.py judge-absorb <goal_id>  (stdin: LLM result JSON)")
        print("       independent_verifier.py affected-tests  (작업 트리 변경 기준 회귀 후보)")
        return 2
    if argv[1] == "affected-tests":
        changed = (_run_git_in(ROOT, ["diff", "--name-only", "HEAD"]) or "").split()
        print("\n".join(affected_tests(ROOT, changed)))
        return 0
    if argv[1] == "same-pattern":
        print(json.dumps(same_pattern_candidates(ROOT), ensure_ascii=False, indent=2))
        return 0
    if argv[1] == "regression-gate":     # 커밋 전: exit 0 = pass·preexisting·skip · 2 = regression · 1 = blocked
        res = regression_gate(ROOT, force_full=("--full" in argv[2:] or os.environ.get("REGRESSION_GATE_FULL") == "1"))
        brief = {k: res.get(k) for k in ("status", "reason", "risk_tier", "full", "summary", "tests", "new_failures",
                                         "baseline_failures", "commit_memory_pct", "perf")}
        print(json.dumps(brief, ensure_ascii=False, indent=1))
        # 2026-11-15 (R256): syntax_error 가 0(통과)으로 나가던 것 — 문법 오류·미검증도 실패 종료
        return {"regression": 2, "syntax_error": 2, "perf_regression": 2, "blocked": 1, "unverified": 1,
                "perf_unmeasured": 1, "incomplete_staging": 1}.get(res["status"], 0)   # R350: 동반 파일 누락 = 미실행 (통과 아님)
    if argv[1] == "syntax-gate":         # git 이 아닌 작업본(SVN) 커밋 전: exit 0 = pass·skip · 2 = 문법 오류 · 1 = 미검증·확정 불가
        res = syntax_gate(ROOT)
        print(json.dumps({k: res.get(k) for k in ("status", "reason", "vcs", "changed_code", "syntax_errors",
                                                   "syntax_unchecked")}, ensure_ascii=False, indent=1))
        return {"syntax_error": 2, "perf_regression": 2, "blocked": 1, "unverified": 1,
                "perf_unmeasured": 1}.get(res["status"], 0)
    if argv[1] == "external-deps":
        deps = external_dependencies(ROOT)
        print(json.dumps({"packages": deps, **external_scope(deps)}, ensure_ascii=False))
        return 0
    if argv[1] == "review-verdict":      # gemini-auto.bat: exit 0 = VERIFIED 만
        if len(argv) < 3:
            print("usage: review-verdict <report file>")
            return 2
        p = Path(argv[2])
        r = review_verdict(p.read_text(encoding="utf-8", errors="replace") if p.is_file() else "")
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["ok"] else 1
    if argv[1] == "codex-check":         # codex-auto.bat: exit 2 = FAIL (완료 처리 안 함) · 1 = PARTIAL/BLOCKED · 0 = PASS
        cwd = Path(argv[argv.index("--cwd") + 1]) if "--cwd" in argv else ROOT      # 격리 worktree 에서 대조
        rest = [a for i, a in enumerate(argv[2:], 2) if a != "--cwd" and argv[i - 1] != "--cwd"]
        r = codex_check(cwd, Path(rest[0]) if rest else None)
        print(json.dumps(r, ensure_ascii=False))
        return 2 if r["status"] == "FAIL" else (0 if r["status"] == "PASS" else 1)
    if argv[1] == "external-evidence":
        if len(argv) < 6:
            print("usage: external-evidence <package> <https url> <version> <read|found|failed> <본문 인용|실패 사유>")
            return 2
        r = record_external_evidence(argv[2], argv[3], argv[4], argv[5], argv[6] if len(argv) > 6 else "")
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["ok"] else 2
    if argv[1] == "judge-handoff":
        if len(argv) < 3:
            print("usage: judge-handoff <goal_id> [--sandbox PATH] [--allow P1,P2]")
            return 2
        gid = int(argv[2])
        sandbox_cwd = None
        allow_paths = None
        for i, a in enumerate(argv):
            if a == "--sandbox" and i + 1 < len(argv):
                sandbox_cwd = argv[i + 1]
            elif a == "--allow" and i + 1 < len(argv):
                allow_paths = [p.strip() for p in argv[i + 1].split(",") if p.strip()]
        r = judge_handoff(gid, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    if argv[1] == "judge-absorb":
        if len(argv) < 3:
            print("usage: judge-absorb <goal_id>  (stdin: LLM JSON)")
            return 2
        gid = int(argv[2])
        stdin_data = sys.stdin.read()
        r = judge_absorb(gid, stdin_data, source=judge_source(kind="cli_stdin"))
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    try:
        gid = int(argv[1])
    except ValueError:
        print(f"invalid goal_id: {argv[1]}")
        return 2

    sandbox_cwd = None
    allow_paths = None
    for i, a in enumerate(argv):
        if a == "--sandbox" and i + 1 < len(argv):
            sandbox_cwd = argv[i + 1]
        elif a == "--allow" and i + 1 < len(argv):
            allow_paths = [p.strip() for p in argv[i + 1].split(",") if p.strip()]

    ev = collect_evidence(gid, sandbox_cwd=sandbox_cwd, allow_paths=allow_paths)
    v = judge(ev)
    print(json.dumps({"evidence": ev, "verdict": v}, ensure_ascii=False, indent=2))
    return 0 if v.get("status") == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
