#!/usr/bin/env python
"""
request-ledger.py — Request Ledger SoT (요청 원장).

근거: 외부 감사 2026-10-16 · execution-contract.md § 1 "n/n 완료 강제".

문제: 사용자 "A·B·C 다 해" → Claude 가 A만 하고 보고 → 사용자 재지시 반복.
해결: 사용자 메시지에서 N 개 request 추출 → ledger 저장 → N/N 완료 전 Stop 차단.

CLI:
  python request-ledger.py add <description> [--session <id>]  # 1개 request 등록
  python request-ledger.py add-batch <json>                     # 여러 개 등록
  python request-ledger.py complete <id>                        # 완료 체크
  python request-ledger.py status                               # 현재 ledger
  python request-ledger.py gate                                 # Stop hook 용 (exit 0=all done, exit 2=incomplete)
  python request-ledger.py clear                                # 전체 비우기 (사용자 명시 시)

저장:
  .claude/state/request-ledger.json
  {
    "session_id": "...",
    "created_at": "...",
    "requests": [
      {"id": "R1", "desc": "...", "status": "pending|completed", "ts": "..."},
      ...
    ]
  }
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
try:  # 한글 콘솔(cp949) 에서 비 cp949 문자 출력 시 UnicodeEncodeError 로 죽던 것 — 출력을 UTF-8 로 고정 (2026-11-18 R277)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
LEDGER = ROOT / ".claude" / "state" / "request-ledger.json"


# ── 저장 안전장치 (2026-11-18 R303 P0) ─────────────────────────────────────────
# 사고: 시험이 운영 원장을 바꿔 끼워 292건이 1건으로 덮였다. 구조 원인 4가지를 여기서 막는다.
#  ① 읽기 실패(쓰는 도중·깨짐) = 빈 원장으로 다시 시작 → 다음 저장이 전체를 덮음  → prev.json 복구 또는 거부
#  ② 잠금 없는 읽기→수정→저장 (세션 여러 개 · 프롬프트 hook 과 CLI 동시)          → 잠금 파일
#  ③ write_text 직접 덮어쓰기 (중간에 죽으면 반쪽 파일)                            → 임시 파일 + os.replace
#  ④ 기존 ID 가 사라지는 저장·ID 중복·시험 프로세스의 운영 원장 쓰기             → 저장 전 검사로 거부
BACKUP = LEDGER.with_name("request-ledger.prev.json")  # *.bak 은 cleanup-pollution 이 3일 뒤 지운다 → 정리 대상 아닌 이름
LOCK = LEDGER.with_name(LEDGER.name + ".lock")
LOCK_WAIT_SEC = 30.0  # 교체 재시도(최대 10초)를 기다리는 다른 쓰기까지 감안
REPLACE_WAIT_SEC = 10.0
_lock_depth = 0
_lock_fh = None


class LedgerError(RuntimeError):
    """원장을 안전하게 읽거나 쓸 수 없음 — 저장하지 않고 멈춘다 (기존 기록 보호)."""


def _is_test_process() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("ORCA_TEST_MODE"))


def _guard_operational() -> None:
    """시험 프로세스는 시스템 임시 폴더 아래 원장에만 쓴다 (실제 프로젝트 원장은 TEMP 아래에 없다 · 사본 스크립트로 도는 시험도 같은 기준)."""
    if not _is_test_process() or os.environ.get("LEDGER_ALLOW_OPERATIONAL_WRITE") == "1":
        return
    import tempfile
    try:
        tmp = Path(tempfile.gettempdir()).resolve()
        ok = LEDGER.resolve().is_relative_to(tmp)
    except (OSError, ValueError):
        ok = False
    if not ok:
        raise LedgerError("시험 실행 중 운영 원장 쓰기 차단 — CLAUDE_PROJECT_DIR 를 임시 폴더로 지정할 것: " + str(LEDGER))


class _Lock:
    """프로세스 사이 잠금 — OS 파일 잠금 (Windows msvcrt.locking · 그 외 fcntl.flock) · 같은 프로세스 안 중첩 허용.
    2026-11-18 R308: «잠금 파일 생성·삭제 + 죽은 PID 회수» 방식은 A 가 풀고 끝난 직후 C 가 새로 잡은 잠금을 B 가 A 의 죽은 PID 로
    보고 지워 B·C 가 동시에 저장하는 경쟁이 있었다 (IFRS 격리 사본 실측: 동시 24건 중 2건 손실). OS 잠금은 프로세스가 죽으면
    운영체제가 자동으로 풀어 «죽은 잠금 판정» 자체가 필요 없다 · 잠금 파일은 지우지 않는다 (지우면 같은 경쟁이 다시 생김)."""

    def __enter__(self):
        global _lock_depth, _lock_fh
        if _lock_depth:
            _lock_depth += 1
            return self
        import time as _t
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        fh = open(LOCK, "a+b")
        t0 = _t.time()
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if _t.time() - t0 > LOCK_WAIT_SEC:
                    fh.close()
                    raise LedgerError(f"원장 잠금 {LOCK_WAIT_SEC:.0f}초 대기 초과 — 저장하지 않음 ({LOCK})")
                _t.sleep(0.05)
        _lock_fh = fh
        _lock_depth = 1
        return self

    def __exit__(self, *exc):
        global _lock_depth, _lock_fh
        _lock_depth -= 1
        if _lock_depth == 0 and _lock_fh is not None:
            try:
                if os.name == "nt":
                    import msvcrt
                    _lock_fh.seek(0)
                    msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(_lock_fh.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            _lock_fh.close()
            _lock_fh = None
        return False


def _parse(p: Path):
    d = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(d, dict) or not isinstance(d.get("requests", []), list):
        raise ValueError("원장 형식 아님")
    return d


def _load() -> dict:
    """없으면 {} · 깨졌으면 prev.json 으로 복구 · 둘 다 안 되면 LedgerError (빈 원장으로 다시 시작해 덮어쓰지 않는다)."""
    if not LEDGER.exists():
        return {}
    err = None
    for _ in range(3):  # 다른 프로세스가 교체하는 순간을 피해 다시 읽기
        try:
            return _parse(LEDGER)
        except Exception as e:  # noqa: BLE001
            err = e
            import time as _t
            _t.sleep(0.05)
    if BACKUP.exists():
        try:
            d = _parse(BACKUP)
            print(f"[ledger] 원장 읽기 실패({type(err).__name__}) → 직전 정상본 prev.json 으로 복구해 읽음", file=sys.stderr)
            return d
        except Exception:  # noqa: BLE001
            pass
    raise LedgerError(f"원장 읽기 실패·백업 없음 — 저장 중단 ({type(err).__name__}: {err})")


def check_integrity(data: dict, before: dict | None = None) -> list:
    """저장 전 검사 — ID 중복 · 비어 있는 ID · 기존 ID 사라짐. 문제 목록 반환 (빈 목록 = 통과)."""
    probs = []
    reqs = data.get("requests", [])
    ids = [r.get("id") for r in reqs]
    if any(not i for i in ids):
        probs.append("ID 없는 항목")
    dup = sorted({i for i in ids if i and ids.count(i) > 1})
    if dup:
        probs.append("ID 중복 " + ",".join(dup[:10]))
    if before:
        gone = [r.get("id") for r in before.get("requests", []) if r.get("id") not in set(ids)]
        if gone:
            probs.append(f"기존 {len(gone)}건 사라짐 ({','.join(map(str, gone[:10]))}) — 원장은 추가만 허용")
    return probs


def _save(data: dict) -> None:
    _guard_operational()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with _Lock():
        before = None
        if LEDGER.exists():
            try:
                before = _parse(LEDGER)
            except Exception:  # noqa: BLE001 — 깨진 현재본은 비교 대상에서 빼고 prev.json 과 비교
                before = _parse(BACKUP) if BACKUP.exists() else None
        probs = check_integrity(data, before)
        if probs:
            raise LedgerError("원장 저장 거부 — " + " · ".join(probs))
        body = json.dumps(data, ensure_ascii=False, indent=2)
        json.loads(body)  # 쓰기 전 직렬화 결과 재확인
        raw = body.encode("utf-8")
        _atomic_write(LEDGER, raw)
        try:  # 검사를 통과해 저장된 최신 정상본 = 복구본 (원장이 나중에 깨져도 0건 손실로 되살림)
            _atomic_write(BACKUP, raw)
        except LedgerError:
            pass


def _atomic_write(path: Path, raw: bytes) -> None:
    import time as _t
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "wb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    # Windows: 다른 프로세스가 읽는 중이거나 백신이 방금 쓴 파일을 검사하는 중이면 교체가 잠시 거부됨
    #   (2026-11-18 R303 실측: 전체 시험 부하 중 2초 재시도로는 드물게 실패 → 최대 10초 · 간격 점점 늘림)
    t0, i = _t.time(), 0
    while True:
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if _t.time() - t0 > REPLACE_WAIT_SEC:
                break
            _t.sleep(min(0.05 * (2 ** min(i, 4)), 0.5))
            i += 1
    try:
        tmp.unlink()
    except OSError:
        pass
    raise LedgerError(f"원장 교체 {REPLACE_WAIT_SEC:.0f}초 재시도 실패 — 저장하지 않음 ({path})")


def locked_update(fn):
    """잠금 안에서 읽기→fn(data)→저장. fn 이 None 반환 = 저장 안 함. 프롬프트 hook 도 이것만 쓴다."""
    _guard_operational()
    with _Lock():
        data = _load()
        result = fn(data)
        if result is not None:
            _save(data)
        return result


def _next_id(requests: list) -> str:
    nums = [int(m.group(1)) for r in requests for m in [re.fullmatch(r"R(\d+)", str(r.get("id", "")))] if m]
    return f"R{max(nums, default=0) + 1}"


def _idempotency_key(desc: str, session: str = "") -> str:
    """멱등성 키 — 같은 desc 24h 안 재수신 중복 등록 방지 (사용자 지시 2026-10-28)."""
    import hashlib
    norm = (desc or "").strip().lower()[:300]
    base = f"{norm}|{session or 'unknown'}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def cmd_add(desc: str, session: str = "", idempotency_window_h: int = 24) -> int:
    """사용자 지시 등록 — append-only + 멱등성 체크 (중복 skip)."""
    data = _load()
    if not data:
        data = {
            "session_id": session or "unknown",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "requests": [],
        }
    key = _idempotency_key(desc, session)
    import datetime as _dt
    cutoff = (datetime.now() - _dt.timedelta(hours=idempotency_window_h)).isoformat(timespec="seconds")
    for r in data["requests"]:
        if r.get("idempotency_key") == key and r.get("ts", "") > cutoff:
            print(f"[ledger] = {r.get('id')} (duplicate · idempotency_key · skipped)")
            return 0
    rid = _next_id(data["requests"])
    data["requests"].append({
        "id": rid,
        "desc": desc[:200],
        "status": "pending",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "idempotency_key": key,
    })
    _save(data)
    print(f"[ledger] + {rid}: {desc[:80]}")
    return 0


def cmd_add_batch(json_str: str) -> int:
    try:
        items = json.loads(json_str)
    except Exception as e:
        print(f"[ledger] JSON parse error: {e}", file=sys.stderr)
        return 2
    if not isinstance(items, list):
        print("[ledger] expected JSON array", file=sys.stderr)
        return 2
    data = _load() or {
        "session_id": "batch",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "requests": [],
    }
    for d in items:
        rid = _next_id(data["requests"])
        data["requests"].append({
            "id": rid,
            "desc": str(d)[:200],
            "status": "pending",
            "ts": datetime.now().isoformat(timespec="seconds"),
        })
    _save(data)
    print(f"[ledger] + {len(items)} requests · total {len(data['requests'])}")
    return 0


def cmd_out_of_scope(rid: str, target: str = "", reason: str = "") -> int:
    """범위 외 요청 처리 (2026-10-29 P0 fix · 사용자 지시).

    사용자 지적: "다른 프로젝트 요청을 complete 처리하면 작업 끝난 것으로 보일 수 있다"
    해결: OUT_OF_SCOPE / PENDING_HANDOFF 상태 분리. completed 와 혼동 X.

    target 명시 필수 (어느 프로젝트/세션으로 인계되는지).
    실제 인계 증거는 사용자 책임 — 이 상태는 "이 세션 범위 아님" 만 명시.
    """
    if not target:
        print("[ledger] out-of-scope: --target 필수 (어느 프로젝트/세션으로 인계)", file=sys.stderr)
        return 2
    data = _load()
    if not data:
        print("[ledger] empty", file=sys.stderr)
        return 2
    for r in data["requests"]:
        if r["id"] == rid or r["id"].lower() == rid.lower():
            r["status"] = "out_of_scope"
            r["out_of_scope_at"] = datetime.now().isoformat(timespec="seconds")
            r["handoff_target"] = target
            r["handoff_reason"] = reason[:300] if reason else "범위 외"
            r["note"] = "⚠ completed 아님 · 실제 인계 증거는 사용자 책임"
            _save(data)
            print(f"[ledger] ↷ {rid}: OUT_OF_SCOPE → {target} (completed X · 작업 종결 X)")
            return 0
    print(f"[ledger] {rid} not found", file=sys.stderr)
    return 2


def cmd_invalid_registration(rid: str, reason: str = "",
                              detected_by: str = "manual") -> int:
    """자동 등록 분류기 오탐 (false_positive) 처리 (2026-10-30 P5-R1 · 사용자 지시).

    사용자 지적: "R75 는 범위 외 요청이 아니라 자동 등록 분류기가 잘못 생성한 요청.
    OUT_OF_SCOPE 로 처리하면 범위 외 작업과 잘못 등록된 이벤트가 섞인다."

    OUT_OF_SCOPE vs INVALID_REGISTRATION 분리:
      - OUT_OF_SCOPE: 사용자가 명시 요청했으나 이 세션/프로젝트 범위 밖 (인계 필요)
      - INVALID_REGISTRATION: autogoal/parser 오탐 · 애초에 사용자 요구사항 아님 (등재 자체가 결함)

    기록 보존:
      - 추적성 유지 (삭제 X · 상태 변경만)
      - detected_by (manual·stop-gate·autogoal-review 등) 로 오탐 유형 분류
      - 재발 방지 분석에 활용 가능

    Stop gate 통과 조건에 포함 (완료는 아니지만 미완도 아님 · 사용자 작업 아님).
    """
    data = _load()
    if not data:
        print("[ledger] empty", file=sys.stderr)
        return 2
    for r in data["requests"]:
        if r["id"] == rid or r["id"].lower() == rid.lower():
            # 2026-11-06: 승인 대기는 사용자 판단 대상 — 오등록으로 닫아 승인 기록을 지우지 않는다
            if r.get("status") == "approval_required":
                print(f"[ledger] ✗ {rid}: 승인 대기 항목 — invalid-registration 으로 바꾸지 않음 (Stop 을 막지도 않음)",
                      file=sys.stderr)
                return 2
            # 이전 상태 보존 (completed 였던 항목의 evidence·verification 은 그대로 남는다)
            r.setdefault("status_before_invalid", r.get("status"))
            r["status"] = "invalid_registration"
            r["invalid_at"] = datetime.now().isoformat(timespec="seconds")
            r["invalid_reason"] = reason[:300] if reason else "자동 등록 오탐"
            r["invalid_detected_by"] = detected_by[:50]
            r["note"] = "⚠ 사용자 요구사항 아님 · 자동 등록 분류기 오탐 · completed·out_of_scope 와 분리 집계"
            _save(data)
            print(f"[ledger] ✗ {rid}: INVALID_REGISTRATION (reason={reason[:80]} · by={detected_by})")
            return 0
    print(f"[ledger] {rid} not found", file=sys.stderr)
    return 2


# 2026-11-05 작업 수행(status) · 검증 결과(verification) · 종료 허가(gate 판단) 는 별개다.
# PARTIAL·BLOCKED + 증거 = 미완료 그대로 종료 허용 — 사실대로 적어도 막히지 않아야 PASS 로 바꿀 이유가 없다.
VERIFICATION_VALUES = ("PASS", "PARTIAL", "BLOCKED", "FAIL")
HONEST_OPEN = ("PARTIAL", "BLOCKED")


def _honest_open(r: dict) -> bool:
    return (r.get("status") == "verified" and r.get("verification") in HONEST_OPEN
            and bool(str(r.get("evidence") or "").strip()))


GATE_PASS_STATUS = ("completed", "deferred", "out_of_scope", "invalid_registration")


def _is_golden_template(r: dict) -> bool:
    """옛 golden-test 가 운영 원장에 남긴 시험 틀 항목 (id T_R* · ts "t") — 실제 요청 아님 (IFRS 실측 2026-11-18)."""
    return str(r.get("id", "")).startswith("T_R") and r.get("ts") == "t"


def _ledger_in_temp() -> bool:
    import tempfile
    try:
        return LEDGER.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
    except (OSError, ValueError):
        return False


def is_blocking(r: dict) -> bool:
    """정본 — Stop 을 막는 미완료인가 (cmd_gate·statusline 공용 · 2026-11-11 §80)."""
    return ((r.get("status") not in GATE_PASS_STATUS + ("approval_required",)) and not _honest_open(r)
            and not _is_golden_template(r))


def summarize(reqs: list, current_rid: str = "") -> dict:
    """정본 집계 — 완료(completed)만 완료로 센다 · 승인대기·검증중·범위외·오등록·보류·진행중 분리.
    current_rid 가 주어지면 그 요청의 상태(UNKNOWN = Ledger 에 없음)."""
    c = {"total": len(reqs), "completed": 0, "approval_required": 0, "verified": 0, "out_of_scope": 0,
         "invalid_registration": 0, "deferred": 0, "open": 0, "blocking": 0}
    for r in reqs:
        st = r.get("status")
        if st in c and st != "total":
            c[st] += 1
        else:
            c["open"] += 1          # pending·implemented 등 진행 중
        if is_blocking(r):
            c["blocking"] += 1
    cur = next((r for r in reqs if current_rid and r.get("id") == current_rid), None)
    c["current_rid"] = current_rid or ""
    c["current_status"] = (cur.get("status") if cur else "UNKNOWN")
    c["current_verification"] = (cur.get("verification") or "") if cur else ""   # R273 개발 줄 PARTIAL·BLOCKED 구분
    c["current_blocking"] = bool(cur and is_blocking(cur))
    c["current_items"] = item_counts(cur) if cur else (0, 0)
    c["queue"] = queue_view(reqs, cur)
    return c


def queue_view(reqs: list, cur) -> dict:
    """R264 작업 현황 (상태줄 요청 줄) — 현재 요청과 같은 세션의 미완료를 FIFO 순으로.
    실행 = 현재 요청 · 대기 = 지금 진행할 수 없음(승인 필요·BLOCKED) · 다음 = 실행 가능한 나머지 (대기 요청이 앞에 있어도
    뒤의 독립 요청은 «다음» 에 보인다) · 가장 오래된 미완료(oldest)와 실행 중 요청을 따로 둔다."""
    sess = (cur or {}).get("session_id")
    if not sess:
        return {"remaining": 0, "running": "", "next": [], "waiting": [], "oldest": ""}
    open_ = [r for r in reqs if r.get("session_id") == sess and r.get("status") not in GATE_PASS_STATUS]

    def _why(r):
        if r.get("status") == "approval_required":
            return "확인필요"
        if r.get("status") == "verified" and r.get("verification") == "BLOCKED":
            return "차단"
        return ""

    def _tag(r):
        d, t = item_counts(r)
        return r["id"] + (f"({d}/{t})" if t else "") + ("부분" if r.get("verification") == "PARTIAL" else "")
    # R273 (11-16 사용자 캡처 "보고까지 끝났는데 실행R272 · ≈16분"): 최신 요청 = 실행 중이 아니다.
    #   실행 = 현재 요청이 아직 처리 중(pending·implemented)일 때만 · PARTIAL·BLOCKED·승인대기로 끝난 현재 요청은
    #   «최근» 으로 따로 보이고 실행은 비운다 (미완료 상태는 그대로 · 숨기지 않음)
    live = bool(cur in open_ and cur.get("status") in ("pending", "implemented"))
    running = cur["id"] if live else ""
    last = ""
    if cur is not None and not live:
        _lab = {"completed": "완료", "approval_required": "확인필요"}.get(cur.get("status"), "")
        if cur.get("status") == "verified":
            _lab = {"PARTIAL": "부분", "BLOCKED": "차단", "FAIL": "실패"}.get(cur.get("verification"), "검증")
        last = cur["id"] + _lab
    return {"remaining": len(open_), "running": running, "last": last,
            "next": [_tag(r) for r in open_ if r is not cur and not _why(r)],
            "waiting": [f"{r['id']} {_why(r)}" for r in open_ if r is not cur and _why(r)],
            "oldest": open_[0]["id"] if open_ else ""}


def _trace_end(r: dict, verification: str, evidence: str) -> None:
    """§78 요청 종료를 추적에 (PASS→success · PARTIAL→partial · BLOCKED→blocked · FAIL→fail) — 실패해도 Ledger 는 그대로."""
    if not r.get("event_id"):
        return
    try:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("_ledger_trace", str(Path(__file__).resolve().parent / "lib" / "trace.py"))
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        st = {"PASS": "success", "PARTIAL": "partial", "BLOCKED": "blocked", "FAIL": "fail"}.get(verification, "unknown")
        m.emit("request", step=r.get("id", ""), status=st, trace_id=r["event_id"], evidence=(evidence or "")[:300],
               detail={"verification": verification or "UNKNOWN"})
    except Exception:  # noqa: BLE001
        pass


# R261 (2026-11-16 · 사용자 지시 "요구사항 10개를 주면 2개만 등록해 2/2=100% 가 되는 구조"):
#   메시지 1개 = 원장 1행이라 원문 안 번호 붙은 요구사항이 저장되지 않았고, 자유 문장 증거 하나로 PASS 가 됐다.
#   → 등록 때 번호 붙은 줄을 하위 항목으로 저장 (넓게 · 설명 절도 포함 → 해당 없음은 사유와 함께 na) ·
#     열린 항목이 있으면 PASS 거부 (상태 그대로 · PARTIAL 은 그대로 허용 = 사실대로 기록).
_ITEM_RE = re.compile(r"^\s{0,8}(\d{1,2})[.)]\s+(\S.*)$")
ITEM_STATES = ("open", "done", "partial", "na")


def extract_items(text: str, limit: int = 60) -> list:
    out, fence = [], False
    for ln in (text or "").splitlines():
        if ln.strip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else _ITEM_RE.match(ln)
        if m:
            out.append({"i": len(out) + 1, "n": int(m.group(1)), "text": m.group(2).strip()[:150], "state": "open"})
            if len(out) >= limit:
                break
    return out


def item_counts(r: dict) -> tuple:
    """(끝난 항목 = done·na, 전체) · 항목 없으면 (0, 0)."""
    items = r.get("items") or []
    return sum(1 for x in items if x.get("state") in ("done", "na")), len(items)


def cmd_item(rid: str, idx: str, state: str, evidence: str = "") -> int:
    """하위 항목 상태 기록 · idx = 항목 번호(i) 1개 또는 쉼표·범위 (예: 1,3,5-7) · done·na 는 근거 필수."""
    if state not in ITEM_STATES[1:]:
        print(f"[ledger] ✗ 상태는 done·partial·na 중 하나", file=sys.stderr)
        return 2
    if state in ("done", "na") and not evidence.strip():
        print(f"[ledger] ✗ {state} 는 근거(--evidence) 필수 — 해당 없음도 사유를 적는다", file=sys.stderr)
        return 2
    want = set()
    for part in str(idx).split(","):
        part = part.strip()
        if re.fullmatch(r"\d+-\d+", part):
            a, b = map(int, part.split("-"))
            want |= set(range(a, b + 1))
        elif part.isdigit():
            want.add(int(part))
    data = _load()
    for r in (data or {}).get("requests", []):
        if r["id"].lower() == rid.lower():
            hit = [x for x in r.get("items") or [] if x.get("i") in want]
            if not hit:
                print(f"[ledger] ✗ {rid}: 항목 {idx} 없음", file=sys.stderr)
                return 2
            for x in hit:
                x["state"], x["evidence"] = state, evidence[:200]
            _save(data)
            d, t = item_counts(r)
            print(f"[ledger] {rid} 항목 {sorted(want)} → {state} · {d}/{t}")
            return 0
    print(f"[ledger] {rid} not found", file=sys.stderr)
    return 2


# 2026-11-19 R312: 반례를 안내문이 아니라 원장 항목으로 — 요구 문장에서 규칙으로 후보 생성 (모델 호출 0 · 하위 요구 3개+ 만)
#   → 시험(pytest nodeid)에 연결하거나 해당 없음 사유 → complete PASS 때 연결된 시험을 지금 다시 실행 (옛 결과·다른 커밋 결과 불인정).
COUNTEREXAMPLE_MIN_ITEMS = 3
_CX_RULES = (
    (r"동시|병렬|여러\s*세션|다중|경쟁|잠금", "동시 실행: 두 세션이 같은 파일·원장을 동시에 쓸 때 손실·덮어쓰기가 없나"),
    (r"삭제|정리|지우|제거|해제", "삭제 범위: 보존 대상(운영 기록·사용자 수정)이 함께 지워지지 않나 · 대상 0건이면 정상 종료하나"),
    (r"입력|파싱|분류|추출|인식|요구사항", "잘못된 입력: 빈 값·NULL·깨진 인코딩·아주 긴 입력을 거부하거나 안전하게 처리하나"),
    (r"파일|경로|폴더", "경로 경계: 공백·한글 경로·없는 파일·권한 없음에서 동작하나"),
    (r"강제\s*종료|kill|복구|재시작|손상|중단", "중단 복구: 쓰는 도중 강제 종료돼도 원본이 보존되고 다음 실행이 복구하나"),
    (r"승인|보안|권한|우회|차단", "우회 시도: 승인·차단 없이 같은 결과를 내는 다른 경로(다른 명령 형태·시험용 id)가 막히나"),
    (r"성능|속도|지연|캐시", "캐시 경계: 오래된 캐시·동시 갱신에서 틀린 값을 보여주지 않나"),
    (r"전파|배포|install|대상\s*프로젝트", "전파 충돌: 대상의 사용자 수정·고유 설정을 덮지 않나"),
    (r"\d+\s*(?:개|건|회|초|%|자)|이상|이하|최대|최소|상한|하한", "숫자 경계: 기준값 바로 아래·같음·바로 위에서 판정이 맞나"),
    (r"테스트|시험|검증|PASS", "검증 역방향: 결함을 일부러 넣으면 그 시험이 실패하나 (통과만 보는 시험 X)"),
    (r"기존|재사용|연결|중복", "기존 기능 충돌: 같은 파일·공유 상태를 쓰는 기존 호출자가 그대로 동작하나"),
)
CX_LIMIT = 8
CX_TEST_TIMEOUT = 600


def extract_counterexamples(items: list) -> list:
    """하위 요구 문장 → 반례 후보 (같은 규칙에 걸린 요구는 한 반례로 묶음 = 중복 제거) · 3개 미만이면 [] (간단한 작업 비용 0)."""
    if len(items or []) < COUNTEREXAMPLE_MIN_ITEMS:
        return []
    out = []
    for pat, text in _CX_RULES:
        hit = [x.get("i") for x in items if re.search(pat, x.get("text") or "", re.I)]
        if hit:
            out.append({"c": len(out) + 1, "text": text, "items": hit[:12], "state": "open"})
        if len(out) >= CX_LIMIT:
            break
    return out


def cx_counts(r: dict) -> tuple:
    cx = r.get("counterexamples") or []
    return sum(1 for x in cx if x.get("state") in ("tested", "na")), len(cx)


def _cx_nodeid_ok(nodeid: str) -> str:
    """시험 연결 검사 — 'path.py::name' 형식 · 파일 존재 · 그 이름의 시험 함수 존재 (관련 없는·없는 시험을 근거로 못 쓰게). 오류면 사유."""
    m = re.fullmatch(r"([\w./\\-]+\.py)::([\w\[\]:.-]+)", nodeid.strip())
    if not m:
        return "시험은 pytest nodeid (파일.py::시험이름) 형식"
    p = Path(m.group(1)) if Path(m.group(1)).is_absolute() else _project_root() / m.group(1)
    if not p.is_file():
        return f"시험 파일 없음: {m.group(1)}"
    fn = m.group(2).split("::")[-1].split("[")[0]
    if not re.search(rf"^\s*(?:async\s+)?def\s+{re.escape(fn)}\s*\(", p.read_text(encoding="utf-8", errors="replace"), re.M):
        return f"시험 함수 없음: {fn} ({m.group(1)})"
    return ""


def _project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def _head() -> str:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(_project_root()), capture_output=True,
                              text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def run_cx_tests(r: dict) -> dict:
    """연결된 반례 시험을 지금 실행 → {c: (ok, 요약)} · 잠금 밖에서 부른다 (시험 몇 분 동안 다른 세션 원장 쓰기를 막지 않게)."""
    tests = {x["c"]: x["test"] for x in r.get("counterexamples") or [] if x.get("state") == "tested" and x.get("test")}
    if not tests:
        return {}
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    from independent_verifier import _pytest_failures   # 회귀 게이트와 같은 실행기 (재구현 X)
    res = {}
    for c, nodeid in tests.items():
        try:
            fails, summary, rc = _pytest_failures(_project_root(), [nodeid], CX_TEST_TIMEOUT, nopyc=True)
            res[c] = (rc == 0 and not fails, f"rc={rc} {summary}"[:160])
        except Exception as e:  # noqa: BLE001 — 실행 실패 = 통과 아님
            res[c] = (False, f"실행 실패: {e}"[:160])
    return res


def cmd_cx(rid: str, c: str = "", state: str = "", test: str = "", evidence: str = "") -> int:
    """반례 조회(인자 1개) · 연결 (tested --test nodeid · na --evidence 사유) · gen = 기존 요청에 후보 생성."""
    data = _load()
    r = next((x for x in (data or {}).get("requests", []) if x["id"].lower() == rid.lower()), None)
    if not r:
        print(f"[ledger] {rid} not found", file=sys.stderr)
        return 2
    if not c:
        d, t = cx_counts(r)
        print(f"{r['id']} 반례 {d}/{t}" + ("" if t else " (하위 요구 3개 미만 또는 해당 규칙 없음 — 생략)"))
        for x in r.get("counterexamples") or []:
            tail = x.get("test") or x.get("evidence") or ""
            last = x.get("last_run") or {}
            print(f"  c{x['c']} [{x['state']:6s}] 요구{x['items']} {x['text']}" + (f"  ← {tail[:70]}" if tail else "")
                  + (f"  · 최근 {'통과' if last.get('ok') else '실패'} {last.get('head','')}" if last else ""))
        return 0
    if c == "gen":
        if r.get("counterexamples"):
            print(f"[ledger] {rid}: 반례 이미 있음 — 덮지 않음", file=sys.stderr)
            return 2
        r["counterexamples"] = extract_counterexamples(r.get("items") or [])
        _save(data)
        print(f"[ledger] {rid} 반례 {len(r['counterexamples'])}개 생성")
        return 0
    x = next((y for y in r.get("counterexamples") or [] if str(y["c"]) == c.lstrip("c")), None)
    if not x:
        print(f"[ledger] ✗ {rid}: 반례 {c} 없음", file=sys.stderr)
        return 2
    if state == "tested":
        why = _cx_nodeid_ok(test) if test else "tested 는 --test 파일.py::시험이름 필수"
        if why:
            print(f"[ledger] ✗ {rid} c{x['c']}: {why} — 연결 안 함", file=sys.stderr)
            return 2
        x.update({"state": "tested", "test": test.strip()})
    elif state == "na":
        if len(evidence.strip()) < 10:
            print(f"[ledger] ✗ na 는 해당 없음 사유 10자+ (--evidence)", file=sys.stderr)
            return 2
        x.update({"state": "na", "evidence": evidence.strip()[:200]})
    else:
        print("[ledger] ✗ 상태는 tested · na", file=sys.stderr)
        return 2
    _save(data)
    d, t = cx_counts(r)
    print(f"[ledger] {rid} c{x['c']} → {state} · 반례 {d}/{t}")
    return 0


def cmd_complete(rid: str, evidence: str = "", verification: str = "", user_approved: str = "",
                 cx_results: dict = None) -> int:
    """4단계: pending → implemented → verified → completed · 증거 필수 (2026-10-16 외부 감사).
    verification=PASS 는 이 요청의 작업을 수행·확인했다는 뜻이다 — 기능 검증 판정(PASS/PARTIAL)을 대신하지 않는다."""
    data = _load()
    if not data:
        print("[ledger] empty", file=sys.stderr)
        return 2
    for r in data["requests"]:
        if r["id"] == rid or r["id"].lower() == rid.lower():
            # 2026-11-05 R160: 승인 대기를 Claude 가 complete 로 풀어 상태가 바뀌고 Stop 까지 막았다.
            # 승인 대기는 사용자 승인 원문 없이는 상태를 바꾸지 않는다 (Stop 도 막지 않는다).
            if r.get("status") == "approval_required":
                if not user_approved.strip():
                    print(f"[ledger] ✗ {rid}: 사용자 승인 대기 — 상태 변경 안 함 (--user-approved 에 승인 원문 필요)",
                          file=sys.stderr)
                    return 2
                r["user_approved"] = user_approved[:300]
            verification = verification.strip().upper() if verification.strip().upper() in VERIFICATION_VALUES \
                else verification
            if verification and verification not in VERIFICATION_VALUES:
                print(f"[ledger] ✗ {rid}: verification 은 {VERIFICATION_VALUES} 중 하나 — 상태 변경 안 함 (설명은 --evidence)",
                      file=sys.stderr)
                return 2
            # 증거 없으면 implemented 로만 (completed 불허)
            if not evidence:
                r["status"] = "implemented"
                r["note"] = "evidence 없음 · completed 대신 implemented (뻥 완료 방지)"
                _save(data)
                print(f"[ledger] ⚠ {rid}: implemented (evidence 미제공 — completed 보류)", file=sys.stderr)
                return 1
            # P0a-A: verification 명시 요구 (2026-10-28 하드코딩 감사 CRITICAL #1 fix)
            # 기존 L148 'verification or "PASS"' 자동 매핑 제거 — UNKNOWN 을 PASS 로 치환하는 결함
            # R11·R23 거짓 완료의 근본 원인. 이제 verification 미제공 = verified (completed X)
            if not verification:
                r["status"] = "verified"
                r["evidence"] = evidence[:500]
                r["verification"] = "UNKNOWN"
                _save(data)
                print(f"[ledger] ⚠ {rid}: verified (verification 미제공 · UNKNOWN · completed 보류)", file=sys.stderr)
                return 1
            if verification != "PASS":
                r["status"] = "verified"
                r["evidence"] = evidence[:500]
                r["verification"] = verification
                _save(data)
                _trace_end(r, verification, evidence)
                print(f"[ledger] ⚠ {rid}: verified (verification={verification} · PASS 아님)", file=sys.stderr)
                return 1
            done_n, total_n = item_counts(r)
            if done_n < total_n:   # R261: 열린 하위 요구사항이 있으면 전체 완료 불가
                left = [f"{x['i']}:{x['text'][:30]}" for x in r.get("items") or [] if x.get("state") not in ("done", "na")]
                print(f"[ledger] ✗ {rid}: 하위 요구사항 {done_n}/{total_n} — PASS 거부 (상태 그대로) · 남은 항목: "
                      + " | ".join(left[:8]) + " · item <rid> <번호> done|na --evidence … 로 하나씩 근거를 남기거나 "
                      "--verification PARTIAL 로 사실대로 기록", file=sys.stderr)
                return 2
            # R312: 반례 — 열린 반례가 있거나 연결된 시험이 지금 실패하면 PASS 거부 (PARTIAL 로 사실대로 기록은 허용)
            cd, ct = cx_counts(r)
            if cd < ct:
                left = [f"c{x['c']}:{x['text'][:24]}" for x in r.get("counterexamples") or [] if x.get("state") == "open"]
                print(f"[ledger] ✗ {rid}: 반례 {cd}/{ct} — PASS 거부 (상태 그대로) · 남은 반례: " + " | ".join(left)
                      + f" · cx {rid} <c번호> tested --test 파일.py::시험 또는 na --evidence 사유", file=sys.stderr)
                return 2
            if any(x.get("state") == "tested" for x in r.get("counterexamples") or []):
                cx_results = cx_results or {}
                for x in r.get("counterexamples") or []:   # 실행 결과가 없는 연결 시험 = 통과 아님 (옛 결과 불인정)
                    if x.get("state") == "tested" and x["c"] not in cx_results:
                        cx_results[x["c"]] = (False, "이번 완료 처리에서 실행 안 됨")
                head = _head()
                for x in r.get("counterexamples") or []:
                    if x["c"] in cx_results:
                        ok, summ = cx_results[x["c"]]
                        x["last_run"] = {"ok": ok, "summary": summ, "head": head,
                                         "at": datetime.now().isoformat(timespec="seconds")}
                bad = [f"c{c}({s})" for c, (ok, s) in cx_results.items() if not ok]
                if bad:
                    _save(data)   # 실패 기록은 남긴다 (숨기지 않음)
                    print(f"[ledger] ✗ {rid}: 반례 시험 실패 {len(bad)}건 — PASS 거부: " + " | ".join(bad), file=sys.stderr)
                    return 2
            r["status"] = "completed"
            r["completed_at"] = datetime.now().isoformat(timespec="seconds")
            r["evidence"] = evidence[:500]
            r["verification"] = verification  # 명시된 PASS 값만 저장
            _save(data)
            _trace_end(r, verification, evidence)
            print(f"[ledger] ✓ {rid}: {r['desc'][:60]} · evidence 확보")
            return 0
    print(f"[ledger] {rid} not found", file=sys.stderr)
    return 2


def cmd_status() -> int:
    """2026-10-29 사용자 지적 반영: completed · deferred · out_of_scope 집계 분리.

    기존: 셋 다 "완료" 로 묶음 → 범위 외 요청이 작업 끝난 것처럼 보임.
    변경: 완료(completed) 와 진행 가능 상태(deferred·out_of_scope) 를 별도 집계.
    """
    data = _load()
    if not data:
        print("[ledger] empty")
        return 0
    total = len(data["requests"])
    completed = sum(1 for r in data["requests"] if r["status"] == "completed")
    verified = sum(1 for r in data["requests"] if r["status"] == "verified")
    implemented = sum(1 for r in data["requests"] if r["status"] == "implemented")
    out_of_scope = sum(1 for r in data["requests"] if r["status"] == "out_of_scope")
    deferred = sum(1 for r in data["requests"] if r["status"] == "deferred")
    invalid_reg = sum(1 for r in data["requests"] if r["status"] == "invalid_registration")
    pending = sum(1 for r in data["requests"] if r["status"] == "pending")
    # 데이터 계약: 완료(≠ 범위 외 ≠ 오등록) · 진행 가능 · 미완료 분리 (2026-10-30 P5-R1)
    progressable = completed + out_of_scope + deferred + invalid_reg  # Stop gate 통과 가능 (완료 아님)
    print(f"=== Request Ledger · 완료 {completed}/{total} · 범위외 {out_of_scope} · 보류 {deferred} · 오등록 {invalid_reg} · 진행중 {pending} ===")
    for r in data["requests"]:
        st = r["status"]
        if st == "completed":
            mark = "✓"
        elif st == "out_of_scope":
            mark = "↷"  # 범위 외 인계 · completed X
        elif st == "invalid_registration":
            mark = "✗"  # 자동 등록 오탐 · 사용자 요구사항 아님 · completed X
        elif st == "deferred":
            mark = "⏭"
        else:
            mark = "☐"
        suffix = ""
        if st == "out_of_scope":
            suffix = f" [OUT_OF_SCOPE → {r.get('handoff_target','?')}]"
        elif st == "invalid_registration":
            suffix = f" [INVALID by={r.get('invalid_detected_by','?')}: {r.get('invalid_reason','?')[:60]}]"
        print(f"  {mark} {r['id']}: {r['desc'][:100]}{suffix}")
    return 0


GATE_LOOP_FILE = LEDGER.parent / "stop-gate-loop.json"
GATE_LOOP_MAX = 3  # 같은 미완료 집합으로 stop_hook_active 차단이 이만큼 이어지면 루프로 본다


_STOP_PAYLOAD = None


def _stop_hook_payload() -> dict:
    """Stop hook stdin JSON (stop_hook_active · session_id). 터미널·빈 입력 = {}. stdin 은 한 번만 읽히므로 결과를 기억한다."""
    global _STOP_PAYLOAD
    if _STOP_PAYLOAD is not None:
        return _STOP_PAYLOAD
    try:
        if sys.stdin is None or sys.stdin.isatty():
            _STOP_PAYLOAD = {}
        else:
            raw = sys.stdin.read()
            _STOP_PAYLOAD = json.loads(raw) if raw.strip() else {}
    except Exception:
        _STOP_PAYLOAD = {}
    if not isinstance(_STOP_PAYLOAD, dict):
        _STOP_PAYLOAD = {}
    return _STOP_PAYLOAD


def _gate_loop_reset() -> None:
    try:
        GATE_LOOP_FILE.unlink()
    except Exception:
        pass


def _gate_loop_exceeded(blocking: list) -> bool:
    """stop_hook_active=true 로 같은 미완료 집합이 연속 GATE_LOOP_MAX 회 막히면 True (통과 · 로그).
    미완료 집합이 바뀌면(진행이 있으면) 카운터는 처음부터. stop_hook_active 없는 첫 차단은 항상 막는다."""
    payload = _stop_hook_payload()
    key = ",".join(sorted(r["id"] + ":" + r["status"] for r in blocking))
    sid = payload.get("session_id", "")
    try:
        st = json.loads(GATE_LOOP_FILE.read_text(encoding="utf-8"))
    except Exception:
        st = {}
    if not payload.get("stop_hook_active") or st.get("key") != key or st.get("session_id") != sid:
        st = {"key": key, "session_id": sid, "count": 0}
    st["count"] = int(st.get("count", 0)) + 1
    if st["count"] > GATE_LOOP_MAX:
        _gate_loop_reset()
        line = (f"[{datetime.now().isoformat(timespec='seconds')}] stop-gate loop 해제 · session={sid} · "
                f"같은 미완료 {key} 로 {GATE_LOOP_MAX}회 연속 차단 후 진전 없음 → 이번 Stop 통과 (항목은 미완료 유지)\n")
        try:
            log = LEDGER.parent.parent / "logs" / "stop-gate-loop.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
        print("[request-ledger] " + line.strip(), file=sys.stderr)
        return True
    try:
        GATE_LOOP_FILE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return False


def cmd_gate() -> int:
    """Stop hook용. exit 0 = all done · exit 2 = incomplete (block Stop)."""
    # 2026-11-18 R310 fail-closed: 원장이 깨지고 복구본도 없으면 예전엔 main 의 LedgerError 처리가 0 을 돌려
    #   미완료가 있어도 Stop 이 통과했다 (격리 사본 실측 rc=0). 읽지 못한 원장 = 완료 확인 불가 → 막고 복구 안내.
    #   무한 차단은 기존 반복 해제(_gate_loop_exceeded) 가 같은 기준으로 푼다.
    try:
        data = _load()
    except LedgerError as e:
        if _gate_loop_exceeded([{"id": "__ledger_unreadable__", "status": "corrupt"}]):
            return 0
        print(f"[request-ledger] 원장을 읽을 수 없어 완료 여부 확인 불가 — Stop 차단: {e}\n"
              f"→ 손상 파일 {LEDGER.name} 은 지우지 말고 보존 · 같은 폴더 request-ledger.cleared-*.json·"
              f"{BACKUP.name} 확인 후 복구 · 복구 못 하면 사실대로 보고", file=sys.stderr)
        return 2
    if not data or not data.get("requests"):
        return 0  # ledger 없음 = 통과
    # 2026-10-16: 시험이 남긴 ledger(session_id "test") 하나가 모든 세션의 Stop 을 막았다.
    #   시험 기록과 오래된 기록(지난 작업)은 이번 세션의 미완이 아니다 → 통과.
    # BASIS: agreed(2026-10-16, 한 세션의 요청 묶음은 몇 시간 안에 끝난다 — 6시간 넘게 안 바뀐 ledger 는 지난 작업.
    #   한계: 6시간 넘게 이어지는 긴 작업의 미완은 놓친다. 그때는 시각이 아니라 세션 id 대조로 바꾼다.)
    STALE_SEC = 6 * 3600
    import time as _t
    # 2026-11-18 R309 fail-open 제거: "test" 통과는 시험 영역(TEMP) 원장일 때만 — 옛 골든 결함으로 덮인 운영 원장
    #   (IFRS: session_id=test · 11-04 이후 실제 요청 R2~R5) 의 완료 게이트가 통째로 꺼져 있었다. 시험 틀 항목은 is_blocking 에서 제외.
    if (data.get("session_id") == "test" and _ledger_in_temp()) or _t.time() - LEDGER.stat().st_mtime > STALE_SEC:
        print("[request-ledger] 시험·지난 작업 ledger — 이번 세션 기준 아님 · 통과", file=sys.stderr)
        return 0
    total = len(data["requests"])
    done = sum(1 for r in data["requests"] if r["status"] in GATE_PASS_STATUS)  # deferred = 다음 세션 지연 · out_of_scope = 범위 외 인계 (2026-10-29) · invalid_registration = 자동 등록 분류기 오탐 (2026-10-30 P5-R1)
    if done == total:
        _gate_loop_reset()
        return 0  # 모두 완료 = 통과
    # 2026-11-02: approval_required = 사용자 승인 대기. Claude 가 계속 일해도 풀 수 없으므로 Stop 을 막지 않는다
    #   (R126: 읽기 전용 분석 요청이 '운영' 단어로 승인 대기 등록 → Stop 9회 연속 차단 · 해결 수단 없음).
    #   항목은 그대로 미완료로 남고 status·statusline 에 보인다 (완료 처리 X).
    waiting = [r for r in data["requests"] if r["status"] == "approval_required"]
    blocking = [r for r in data["requests"] if is_blocking(r)]
    # 2026-11-18: 원장은 모든 세션이 같이 쓴다 — 다른 세션이 남긴 옛 미완료(459건)로 이 세션의 Stop 이 매 회차 막혔다.
    #   Stop payload 의 session_id 가 있으면 다른 세션 id 가 적힌 항목은 막지 않는다 (남의 미완료는 그대로 미완료 · 상태줄·status 에 보임).
    #   session_id 를 못 받으면(터미널 실행 등) 종전대로 전체.
    _sid = str(_stop_hook_payload().get("session_id") or "")
    if _sid:
        blocking = [r for r in blocking if not r.get("session_id") or r.get("session_id") == _sid]   # 세션 id 없는 옛 항목은 종전대로 막음
    if not blocking:
        _gate_loop_reset()
        open_items = waiting + [r for r in data["requests"] if _honest_open(r)]
        print(f"[request-ledger] 미완료 {len(open_items)}건 유지 · Stop 허용 (완료 처리 아님): "
              + ", ".join(f"{r['id']}:{r.get('verification') or r['status']}" for r in open_items), file=sys.stderr)
        return 0
    # stop_hook_active 반복 차단 해소: 같은 미완료 집합으로 연속 N 회 막혔으면 무한 루프 → 통과 + 로그
    if _gate_loop_exceeded(blocking):
        return 0
    # 미완료 있음 — Claude 에게 알림
    pending = blocking
    msg = f"[request-ledger] {done}/{total} 완료 · 미완료 {len(pending)}건:\n"
    for r in pending[:5]:
        msg += f"  ☐ {r['id']}: {r['desc'][:80]}\n"
    msg += ("→ 미완료 request 계속 실행 후 보고 (execution-contract § 2 n/n 완료 전 보고 금지) · "
            "끝나지 않았으면 PASS 로 바꾸지 말고 complete --evidence ... --verification PARTIAL 또는 BLOCKED 로 사실대로 기록 · "
            "사용자 지시가 아닌 자동 등록(상태 보고·인용·붙여 넣은 이전 대화)이면 PASS 로 닫지 말고 "
            "invalid-registration <id> --reason ... --detected-by stop-gate")
    print(msg, file=sys.stderr)
    return 2


def cmd_clear() -> int:
    """비우기 = 지우지 않고 보관 이름으로 옮김 (2026-11-18 R303 · 되돌릴 수 있게)."""
    _guard_operational()
    with _Lock():
        if LEDGER.exists():
            dst = LEDGER.with_name(f"request-ledger.cleared-{datetime.now():%Y%m%d-%H%M%S}.json")
            os.replace(LEDGER, dst)
            print(f"[ledger] cleared · 보관 {dst.name}")
            return 0
    print("[ledger] cleared")
    return 0


def cmd_to_goals() -> int:
    """pending Ledger entries → Supervisor create_goal 자동 변환 (사용자 지시 2026-10-28).
    각 request 는 request_id 를 goal source_ref 에 저장 → 역추적 가능.
    기존 goal 보존 (덮어쓰기 X) · idempotency 는 ledger 에서 이미 처리됨."""
    data = _load()
    if not data:
        print("[ledger→goal] no ledger")
        return 1
    import sqlite3
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    # 2026-11-04 F7 FAIL (R154 → Goal #1464): 대화 지시가 전부 Goal 로 승격됐다.
    # 승격 기준은 UserPromptSubmit 자동 등재와 같은 정본 정책 (명시 실행 토큰 · 질문/보고 skip · 1h 중복) 을 쓴다.
    from auto_goal_from_prompt import is_urgent, should_register
    from supervisor import ensure_schema
    ensure_schema()
    sup_db = ROOT / ".claude" / "state" / "orca.db"
    created = 0
    skipped = 0
    not_promoted = 0
    with sqlite3.connect(str(sup_db)) as c:
        for r in data.get("requests", []):
            if r.get("status") != "pending":
                continue
            rid = r.get("id")
            desc = r.get("desc") or ""
            if not should_register(desc).get("register"):
                not_promoted += 1          # ledger 항목은 그대로 둔다 (원장 수정 X)
                continue
            source_ref = f"ledger:{rid}"
            # 기존 goal 중 같은 source_ref 있나 (idempotency)
            exist = c.execute("SELECT goal_id FROM goals WHERE source_ref=?",
                             (source_ref,)).fetchone()
            if exist:
                skipped += 1
                continue
            import time as _t
            now = int(_t.time())
            c.execute(
                "INSERT INTO goals (description, status, workflow_type, source_ref, "
                "max_retry, timeout_h, created_at, updated_at, priority) "
                "VALUES (?, 'PENDING', 'GENERAL', ?, 3, 24, ?, ?, ?)",
                (f"[{rid}] {desc}", source_ref, now, now, 1 if is_urgent(desc) else 0)
            )
            created += 1
    # Request 완료 ≠ Goal 완료. 불일치는 경고만 하고 Goal 상태는 바꾸지 않는다 (상태 전이는 supervisor 증거 기준).
    from ledger_goal_integrity import check
    mismatch = [i for i in check().get("issues", []) if i.get("kind") == "ledger_completed_but_goal_incomplete"]
    warn = "".join(f" WARN ledger {i['rid']} completed but goal #{i['goal_id']} {i['goal_status']} (상태 변경 안 함)"
                   for i in mismatch)
    print(f"[ledger→goal] created={created} skipped_existing={skipped} not_promoted={not_promoted}{warn}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op")

    p_add = sub.add_parser("add")
    p_add.add_argument("desc")
    p_add.add_argument("--session", default="")

    p_batch = sub.add_parser("add-batch")
    p_batch.add_argument("json_str")

    p_comp = sub.add_parser("complete")
    p_comp.add_argument("rid")
    p_comp.add_argument("--evidence", default="", help="실제 수행 증거 (git diff·실행 결과·파일 경로)")
    p_comp.add_argument("--verification", default="", help="PASS·PARTIAL·BLOCKED·FAIL 만 허용 · 이 요청의 결과이며 기능 전체 판정 아님")
    p_comp.add_argument("--user-approved", default="", help="승인 대기 항목의 사용자 승인 원문")

    # out-of-scope — 범위 외 요청 (completed 와 혼동 금지 · 2026-10-29 P0 fix)
    p_oos = sub.add_parser("out-of-scope")
    p_oos.add_argument("rid")
    p_oos.add_argument("--target", required=True, help="인계 대상 (예: C:/pjt/Project1.5)")
    p_oos.add_argument("--reason", default="", help="범위 외 사유")

    # invalid-registration — 자동 등록 분류기 오탐 (2026-10-30 P5-R1 · 사용자 지시)
    # OUT_OF_SCOPE 와 분리: OUT_OF_SCOPE 는 명시 요청·범위 밖 · INVALID 는 애초에 사용자 요구사항 아님
    p_inv = sub.add_parser("invalid-registration")
    p_inv.add_argument("rid")
    p_inv.add_argument("--reason", default="", help="오탐 사유 (예: 사용자 비판 메시지 자동 등재)")
    p_inv.add_argument("--detected-by", default="manual",
                       help="감지 주체 (manual·stop-gate·autogoal-review·sweep 등)")

    p_item = sub.add_parser("item")      # R261 하위 요구사항 상태
    p_item.add_argument("rid")
    p_item.add_argument("idx", help="항목 번호 (예: 3 · 1,4 · 2-5)")
    p_item.add_argument("state", help="done · partial · na")
    p_item.add_argument("--evidence", default="", help="done=실행 증거 · na=해당 없음 사유")
    p_items = sub.add_parser("items")
    p_items.add_argument("rid")
    p_cx = sub.add_parser("cx")          # R312 반례 (조회 · gen · tested/na 연결)
    p_cx.add_argument("rid")
    p_cx.add_argument("c", nargs="?", default="", help="반례 번호 (예: 2 · c2) 또는 gen")
    p_cx.add_argument("state", nargs="?", default="", help="tested · na")
    p_cx.add_argument("--test", default="", help="pytest nodeid (파일.py::시험이름)")
    p_cx.add_argument("--evidence", default="", help="na 사유")

    sub.add_parser("status")
    sub.add_parser("gate")
    sub.add_parser("clear")
    sub.add_parser("to-goals")

    args = ap.parse_args()
    if args.op == "complete" and args.verification.strip().upper() == "PASS":
        # R312: 반례 시험은 잠금 밖에서 먼저 실행 (몇 분 걸려도 다른 세션 원장 쓰기를 막지 않게) → 결과를 잠금 안 판정에 넘김
        try:
            r0 = next((x for x in (_load() or {}).get("requests", []) if x["id"].lower() == args.rid.lower()), None)
        except LedgerError:
            r0 = None
        args.cx_results = run_cx_tests(r0) if r0 and cx_counts(r0)[0] == cx_counts(r0)[1] else None
    if args.op in _MUTATING:
        with _Lock():  # 읽기→수정→저장 전체를 한 잠금 안에서 (세션 여러 개·프롬프트 hook 동시 접근)
            return _dispatch(ap, args)
    return _dispatch(ap, args)


_MUTATING = {"add", "add-batch", "complete", "out-of-scope", "invalid-registration", "item", "cx", "clear"}


def _dispatch(ap, args) -> int:
    if args.op == "add":
        return cmd_add(args.desc, args.session)
    if args.op == "add-batch":
        return cmd_add_batch(args.json_str)
    if args.op == "complete":
        return cmd_complete(args.rid, args.evidence, args.verification, args.user_approved,
                            getattr(args, "cx_results", None))
    if args.op == "cx":
        return cmd_cx(args.rid, args.c, args.state, args.test, args.evidence)
    if args.op == "out-of-scope":
        return cmd_out_of_scope(args.rid, args.target, args.reason)
    if args.op == "invalid-registration":
        return cmd_invalid_registration(args.rid, args.reason, args.detected_by)
    if args.op == "item":
        return cmd_item(args.rid, args.idx, args.state, args.evidence)
    if args.op == "items":
        for r in (_load() or {}).get("requests", []):
            if r["id"].lower() == args.rid.lower():
                d, t = item_counts(r)
                print(f"{r['id']} 하위 요구사항 {d}/{t}")
                for x in r.get("items") or []:
                    print(f"  {x['i']:>2} [{x['state']:7s}] {x['text'][:90]}" + (f"  ← {x['evidence'][:60]}" if x.get("evidence") else ""))
                return 0
        return 2
    if args.op == "status":
        return cmd_status()
    if args.op == "gate":
        return cmd_gate()
    if args.op == "clear":
        return cmd_clear()
    if args.op == "to-goals":
        return cmd_to_goals()
    ap.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LedgerError as e:  # 저장 거부·잠금 실패 = 기록 안 됨을 숨기지 않는다 (gate·status 는 아래 0 유지)
        print(f"[request-ledger] 저장 안 함: {e}", file=sys.stderr)
        sys.exit(3 if len(sys.argv) > 1 and sys.argv[1] in _MUTATING else 0)
    except Exception as e:
        print(f"[request-ledger] fatal: {e}", file=sys.stderr)
        sys.exit(0)
