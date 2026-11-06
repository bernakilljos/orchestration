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
    """공식 자료 대조 기록. level: read = 본문 확인 · found = 검색 결과만 (대조로 인정 X).
    패키지명·공개 URL·버전만 저장 — 코드·내부 데이터 금지."""
    if level not in ("read", "found") or not url.startswith("https://"):
        return {"ok": False, "reason": "level 은 read|found · url 은 https"}
    row = {"package": package, "url": url, "version": version, "level": level, "note": note[:200],
           "checked_at": __import__("time").strftime("%Y-%m-%d")}
    EXTERNAL_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EXTERNAL_EVIDENCE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, **row}


def external_scope(packages: List[str]) -> Dict[str, Any]:
    """외부 근거 축 — none_needed | checked | not_checked. 본문 확인(read) 기록이 있는 패키지만 확인으로 센다."""
    if not packages:
        return {"scope": "none_needed", "unchecked": []}
    read = set()
    if EXTERNAL_EVIDENCE.exists():
        for line in EXTERNAL_EVIDENCE.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("level") == "read":
                read.add(row.get("package"))
    unchecked = [p for p in packages if p not in read]
    return {"scope": "not_checked" if unchecked else "checked", "unchecked": unchecked}


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
    """변경 파일의 모듈명을 참조하는 테스트 파일 (회귀 후보) — 변경된 테스트 자신 포함. V1.1 C."""
    out = _run_git_in(cwd, ["ls-files", "*test_*.py", "*_test.py", "*.test.ts", "*.test.js"]) or ""
    tests = [t.strip() for t in out.splitlines() if t.strip()]
    stems = {Path(p).stem for p in changed if Path(p).suffix in (".py", ".sh", ".ts", ".tsx", ".js")}
    hits = [t for t in tests if t in changed]
    for t in tests:
        if t in hits or not stems:
            continue
        try:
            text = (cwd / t).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(re.search(rf"\b{re.escape(s)}\b", text) for s in stems):
            hits.append(t)
    return hits


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
                 "a requirement is met only with [확인] evidence.")
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


def judge_absorb(goal_id: int, judge_result_json: str,
                 required_ids: Optional[List[str]] = None) -> Dict[str, Any]:
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
    # 검증 범위 표시: 요구사항별로 확인했는지, 요구사항 없이 diff·테스트로만 판정했는지
    final["requirements_scope"] = "checked" if required_ids else "not_configured"
    data["llm_verdict"] = llm_verdict
    data["final_verdict"] = final
    data["status"] = "completed"
    handoff_file.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return {"ok": True, "goal_id": goal_id, "final_verdict": final,
            "stat_verdict": stat, "llm_verdict": llm_verdict}


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
    if argv[1] == "external-deps":
        deps = external_dependencies(ROOT)
        print(json.dumps({"packages": deps, **external_scope(deps)}, ensure_ascii=False))
        return 0
    if argv[1] == "external-evidence":
        if len(argv) < 6:
            print("usage: external-evidence <package> <https url> <version> <read|found> [note]")
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
        r = judge_absorb(gid, stdin_data)
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
