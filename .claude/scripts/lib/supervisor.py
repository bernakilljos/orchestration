"""supervisor.py — 2026-10-26 외부 AI 제안 Supervisor 모듈 scaffold.

Goal → Plan → Execute → Review → Repair 상태머신. 상위 감독 계층.

상태 전환:
  PENDING → PLANNING → RUNNING → VERIFIED (완료)
                               → REPAIRING → RUNNING (재시도)
                               → FAILED (한계 도달 · 승인 요청)

사용:
  python supervisor.py create "목표 설명" [--max-retry 3] [--timeout-h 24]
  python supervisor.py advance <goal_id> <new_status>
  python supervisor.py list [--status PENDING|RUNNING|VERIFIED|FAILED]
  python supervisor.py show <goal_id>

scaffold 수준:
- goals 테이블 신설 (ensure_schema idempotent)
- 상태 전환 CAS (잘못된 전환 거부)
- tasks 와 느슨한 연결 (goal_id 로 묶어서 조회)
- 자동 재계획·에이전트 할당은 다음 단계 (이번은 상태머신·DB·CLI 만)
"""
from __future__ import annotations
import sys
import os
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"

VALID_STATES = ("PENDING", "PLANNING", "RUNNING", "VERIFIED", "REPAIRING", "FAILED", "BLOCKED")

# 허용되는 상태 전환 (A → B)
# BLOCKED = 외부 의존 (사용자 승인·권한·계정) 대기 · 나머지 goal 은 계속 진행
ALLOWED_TRANSITIONS = {
    "PENDING":   {"PLANNING", "BLOCKED", "FAILED"},
    "PLANNING":  {"RUNNING", "BLOCKED", "FAILED"},
    "RUNNING":   {"VERIFIED", "REPAIRING", "BLOCKED", "FAILED"},
    "REPAIRING": {"RUNNING", "BLOCKED", "FAILED"},
    "BLOCKED":   {"PENDING", "PLANNING", "RUNNING", "FAILED"},  # 해제 시 복귀
    "VERIFIED":  set(),  # 종결
    "FAILED":    set(),  # 종결
}

# 미완 상태 (Stop hook 이 next-actions.md 재기록 트리거)
ACTIVE_STATES = {"PENDING", "PLANNING", "RUNNING", "REPAIRING", "BLOCKED"}


def ensure_schema() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB)) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS goals (
          goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
          description TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING',
          workflow_type TEXT DEFAULT 'GENERAL',
          source_ref TEXT,
          max_retry INTEGER DEFAULT 3,
          retry_count INTEGER DEFAULT 0,
          timeout_h INTEGER DEFAULT 24,
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL,
          completed_at INTEGER,
          plan TEXT,
          result TEXT,
          failure_reason TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status, created_at DESC);

        CREATE TABLE IF NOT EXISTS goal_tasks (
          goal_id INTEGER NOT NULL,
          task_id TEXT NOT NULL,
          sequence INTEGER DEFAULT 0,
          PRIMARY KEY (goal_id, task_id),
          FOREIGN KEY (goal_id) REFERENCES goals(goal_id)
        );
        CREATE INDEX IF NOT EXISTS idx_goal_tasks_goal ON goal_tasks(goal_id, sequence);

        CREATE TABLE IF NOT EXISTS goal_transitions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          goal_id INTEGER NOT NULL,
          from_status TEXT,
          to_status TEXT NOT NULL,
          reason TEXT,
          actor TEXT,
          ts INTEGER NOT NULL,
          FOREIGN KEY (goal_id) REFERENCES goals(goal_id)
        );
        CREATE INDEX IF NOT EXISTS idx_goal_trans ON goal_transitions(goal_id, ts);
        """)
        # 2026-10-26 외부 AI 설계 수용: workflow_type / source_ref 선확장 (기존 테이블)
        try:
            cols = [r[1] for r in c.execute("PRAGMA table_info(goals)").fetchall()]
            if "workflow_type" not in cols:
                c.execute("ALTER TABLE goals ADD COLUMN workflow_type TEXT DEFAULT 'GENERAL'")
            if "source_ref" not in cols:
                c.execute("ALTER TABLE goals ADD COLUMN source_ref TEXT")
            # 컬럼 보장 후 index 생성
            c.execute("CREATE INDEX IF NOT EXISTS idx_goals_workflow ON goals(workflow_type, status)")
        except Exception:
            pass


def create_goal(description: str, max_retry: int = 3, timeout_h: int = 24,
                workflow_type: str = "GENERAL", source_ref: str = "") -> int:
    """workflow_type: GENERAL (일반 목표) | REPAIR (재발 자동 해결 · Diagnose→Repair→Verify)
    source_ref: REPAIR 의 경우 rule_id · improvement_id 등 추적 ref."""
    ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        cur = c.execute(
            "INSERT INTO goals (description, status, workflow_type, source_ref, "
            "max_retry, timeout_h, created_at, updated_at) "
            "VALUES (?, 'PENDING', ?, ?, ?, ?, ?, ?)",
            (description, workflow_type, source_ref, max_retry, timeout_h, now, now)
        )
        goal_id = cur.lastrowid
        c.execute(
            "INSERT INTO goal_transitions (goal_id, from_status, to_status, reason, actor, ts) "
            "VALUES (?, NULL, 'PENDING', ?, 'supervisor', ?)",
            (goal_id, f"workflow={workflow_type}", now)
        )
    return goal_id


def create_repair_goal(rule_id: str, category: str, total_recurrences: int, snippet: str = "") -> int:
    """재발 자동 해결 전용 goal 생성 (recurrence-tracker 에서 호출).
    외부 AI 설계: REPAIR workflow = Diagnose → Repair → Verify."""
    desc = f"[REPAIR] 재발 자동 해결 · rule={rule_id} · category={category} · 총 {total_recurrences}회"
    if snippet:
        desc += f" · 샘플: {snippet[:80]}"
    return create_goal(
        description=desc,
        max_retry=3,
        timeout_h=12,  # REPAIR 는 짧게 (12h · GENERAL 24h 보다 보수적)
        workflow_type="REPAIR",
        source_ref=f"rule:{rule_id}"
    )


def advance(goal_id: int, to_status: str, reason: str = "", actor: str = "supervisor") -> bool:
    """상태 전환 CAS. 허용 안 되는 전환은 거부."""
    if to_status not in VALID_STATES:
        return False
    ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT status, retry_count, max_retry FROM goals WHERE goal_id=?",
            (goal_id,)
        ).fetchone()
        if not row:
            return False
        current, retry, max_r = row
        if to_status not in ALLOWED_TRANSITIONS.get(current, set()):
            return False  # 잘못된 전환
        # REPAIRING → RUNNING 전환 시 retry_count 증가 · max 초과 시 FAILED 강제
        new_retry = retry
        if current == "REPAIRING" and to_status == "RUNNING":
            new_retry = retry + 1
            if new_retry > max_r:
                to_status = "FAILED"
                reason = reason + f" | retry limit ({max_r}) 초과"
        completed_at = now if to_status in ("VERIFIED", "FAILED") else None
        c.execute(
            "UPDATE goals SET status=?, retry_count=?, updated_at=?, "
            "completed_at=COALESCE(?, completed_at), "
            "failure_reason=CASE WHEN ?='FAILED' THEN ? ELSE failure_reason END "
            "WHERE goal_id=?",
            (to_status, new_retry, now, completed_at, to_status, reason, goal_id)
        )
        c.execute(
            "INSERT INTO goal_transitions (goal_id, from_status, to_status, reason, actor, ts) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (goal_id, current, to_status, reason, actor, now)
        )
    return True


def advance_all_pending(dry_run: bool = False, auto_execute: bool = True,
                        trigger_source: str = "") -> dict:
    """모든 미완료 goal 을 다음 상태로 자동 진행 + 실제 실행 (2026-10-27 사용자 지시 "무인 자율").
    trigger_source (2026-10-27 사용자 지시 "실행 주체 식별"): scheduler · stop_hook · manual · ""
      - goal source_ref 가 "scheduler_only:..." → trigger_source=scheduler 때만 처리 (격리)
      - Hook 전체 비활성화 X · 특정 goal 만 scheduler 전용
    PENDING → PLANNING → RUNNING → (auto_execute 시 execute_goal) → VERIFIED/REPAIRING.
    - 독립 goal 병렬 처리 · BLOCKED 는 skip · Timeout 초과 FAILED
    - REPAIR workflow: verify-improvement.py 자동 호출
    - GENERAL workflow + source_ref=verify: → 자동 verify
    - GENERAL workflow + goal_tasks (decompose 완료): auto_execute 시 execute_goal 호출
    - 중복 실행 방지: 원자적 claim (DB UPDATE WHERE rowcount)
    """
    ensure_schema()
    advanced = {"PENDING": 0, "PLANNING": 0, "RUNNING": 0, "REPAIRING": 0, "FAILED": 0, "BLOCKED": 0}
    details = []
    executed_goals = []  # auto_execute 실행 goal_id 목록
    skipped_scheduler_only = 0  # scheduler_only goal 가 trigger != scheduler 로 skip 된 수
    with sqlite3.connect(str(DB)) as c:
        # BLOCKED 는 외부 의존 대기 — 자동 진행 스킵 (다른 goal 은 계속)
        rows = c.execute(
            "SELECT goal_id, status, workflow_type, source_ref, timeout_h, created_at "
            "FROM goals WHERE status IN ('PENDING', 'PLANNING', 'RUNNING', 'REPAIRING') "
            "ORDER BY created_at"
        ).fetchall()
    now = int(time.time())
    for goal_id, status, wtype, source_ref, timeout_h, created_at in rows:
        # 2026-10-27 trigger_source 격리 (사용자 지시 "실행 주체 식별 격리")
        if source_ref and source_ref.startswith("scheduler_only:"):
            if trigger_source != "scheduler":
                skipped_scheduler_only += 1
                continue
        if timeout_h and (now - created_at) > timeout_h * 3600:
            if not dry_run:
                advance(goal_id, "FAILED", f"timeout {timeout_h}h 초과", "supervisor:auto")
            advanced["FAILED"] += 1
            details.append({"goal_id": goal_id, "action": "FAILED(timeout)"})
            continue
        # 2026-10-30 Phase 12: self-heal 이벤트 진행 중인 REPAIRING goal 은 단순 재시도 X (heal-tick 이 처리)
        if status == "REPAIRING" and _heal_active(goal_id):
            details.append({"goal_id": goal_id, "action": "skip(self_heal_event_active)"})
            continue
        next_status = _next_status_hook(status, wtype, source_ref, goal_id, dry_run)
        if next_status:
            if not dry_run:
                advance(goal_id, next_status, f"auto advance from {status}", "supervisor:auto")
            advanced[status] = advanced.get(status, 0) + 1
            details.append({"goal_id": goal_id, "from": status, "to": next_status})
            continue
        # 2026-10-27 사용자 지시 "RUNNING 상태에서 execute 자동 호출"
        # GENERAL workflow + RUNNING + goal_tasks 있음 + auto_execute → execute_goal
        if status == "RUNNING" and wtype == "GENERAL" and auto_execute and not dry_run:
            if _should_auto_execute(goal_id):
                exec_result = execute_goal(goal_id)
                executed_goals.append({"goal_id": goal_id, "executed": exec_result.get("executed", 0),
                                       "verified": exec_result.get("verified", 0),
                                       "failed": exec_result.get("failed", 0)})
                # 전체 task 중 모두 verified → Goal VERIFIED · 일부 실패 → REPAIRING
                total_tasks = _count_goal_tasks(goal_id)
                all_verified = _all_tasks_verified(goal_id)
                has_unverified = _any_task_unverified(goal_id)
                if total_tasks > 0 and all_verified:
                    advance(goal_id, "VERIFIED", f"auto: all {total_tasks} tasks verified", "supervisor:auto")
                    details.append({"goal_id": goal_id, "from": "RUNNING", "to": "VERIFIED",
                                    "tasks": total_tasks})
                elif exec_result.get("failed", 0) > 0:
                    advance(goal_id, "REPAIRING", f"auto: {exec_result.get('failed')} tasks failed", "supervisor:auto")
                    details.append({"goal_id": goal_id, "from": "RUNNING", "to": "REPAIRING",
                                    "failed_tasks": exec_result.get("failed"),
                                    "self_heal": _heal_enqueue(goal_id)})
                elif has_unverified:
                    # cmd exit=0 but verify fail (NOT OK · Traceback 등) → REPAIRING
                    advance(goal_id, "REPAIRING", "auto: verify failed (fail-closed)", "supervisor:auto")
                    details.append({"goal_id": goal_id, "from": "RUNNING", "to": "REPAIRING",
                                    "reason": "verify_fail"})
                # claim 해제 — 다음 사이클 재사용 (실행 완료)
                _release_claim(goal_id)
        # REPAIRING 자동 재시도 (사용자 지시 P1 "REPAIRING 전환만으로 완료 아님")
        if status == "REPAIRING" and wtype == "GENERAL" and auto_execute and not dry_run:
            retry, max_r = _get_retry_count(goal_id)
            if retry < max_r:
                # 다음 사이클: REPAIRING → RUNNING (retry_count++) · 재시도
                advance(goal_id, "RUNNING", f"auto repair retry {retry+1}/{max_r}", "supervisor:auto")
                details.append({"goal_id": goal_id, "from": "REPAIRING", "to": "RUNNING",
                                "retry": f"{retry+1}/{max_r}"})
                # tasks 를 pending 으로 reset (재실행 가능하도록)
                _reset_tasks_for_retry(goal_id)
            else:
                advance(goal_id, "FAILED", f"auto repair exhausted {retry}/{max_r}", "supervisor:auto")
                details.append({"goal_id": goal_id, "from": "REPAIRING", "to": "FAILED",
                                "reason": "repair_exhausted"})
    return {"advanced": advanced, "details": details, "executed_goals": executed_goals,
            "skipped_scheduler_only": skipped_scheduler_only,
            "trigger_source": trigger_source or "unspecified",
            "timestamp": now}


def _heal_module():
    import importlib.util as _ilu
    p = ROOT / ".claude" / "scripts" / "lib" / "self_healing.py"
    spec = _ilu.spec_from_file_location("_self_healing", p)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _heal_active(goal_id: int) -> bool:
    try:
        return _heal_module().has_active_event(goal_id)
    except Exception:
        return False


def _heal_enqueue(goal_id: int) -> dict:
    """실패 이벤트 영속화만 (수정 실행은 scheduler heal-tick). opt-in 없으면 no-op."""
    try:
        return _heal_module().enqueue_failure_event(goal_id)
    except Exception as e:
        return {"enqueued": False, "error": str(e)[:120]}


def _try_claim_goal(goal_id: int, worker_id: str = "supervisor:auto", lease_s: int = 300) -> bool:
    """원자적 claim (2026-10-27 사용자 지시 "원자적 claim · lease · 만료 복구").
    goals 테이블에 executor_claim_by / executor_claim_at 추가 · UPDATE WHERE rowcount 로 race 방지.
    lease_s 초과 claim 은 stale 로 간주 · 다른 워커가 take-over 가능 (만료 복구).
    반환: True = claim 성공 · False = 이미 다른 워커가 처리 중."""
    import sqlite3 as _s
    now = int(time.time())
    stale_cutoff = now - lease_s
    try:
        with _s.connect(str(DB), timeout=10, isolation_level="IMMEDIATE") as c:
            # 컬럼 lazy add (idempotent)
            cols = [r[1] for r in c.execute("PRAGMA table_info(goals)").fetchall()]
            if "executor_claim_by" not in cols:
                c.execute("ALTER TABLE goals ADD COLUMN executor_claim_by TEXT")
            if "executor_claim_at" not in cols:
                c.execute("ALTER TABLE goals ADD COLUMN executor_claim_at INTEGER DEFAULT 0")
            # UPDATE WHERE claim 없음 또는 stale · rowcount 로 결과 확인
            cur = c.execute(
                "UPDATE goals SET executor_claim_by=?, executor_claim_at=? "
                "WHERE goal_id=? AND (executor_claim_by IS NULL OR executor_claim_by='' "
                "OR executor_claim_at < ?)",
                (worker_id, now, goal_id, stale_cutoff)
            )
            return cur.rowcount == 1
    except Exception:
        return False


def _release_claim(goal_id: int) -> None:
    """실행 완료 후 claim 해제 (다른 워커가 다음 사이클에 재사용 가능)."""
    import sqlite3 as _s
    try:
        with _s.connect(str(DB), timeout=10) as c:
            c.execute("UPDATE goals SET executor_claim_by=NULL, executor_claim_at=0 WHERE goal_id=?",
                      (goal_id,))
    except Exception:
        pass


def _should_auto_execute(goal_id: int) -> bool:
    """원자적 claim 시도 · 성공 시 True (실제 실행 가능) · 실패 시 다른 워커 처리 중."""
    return _try_claim_goal(goal_id)


def _count_goal_tasks(goal_id: int) -> int:
    with sqlite3.connect(str(DB)) as c:
        return c.execute("SELECT COUNT(*) FROM goal_tasks WHERE goal_id=?", (goal_id,)).fetchone()[0]


def _all_tasks_verified(goal_id: int) -> bool:
    """goal 의 모든 task 가 completed 상태 (= execute_goal 에서 verified_flag=True)."""
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute(
            "SELECT t.status FROM tasks t "
            "JOIN goal_tasks gt ON gt.task_id = t.task_id "
            "WHERE gt.goal_id = ?",
            (goal_id,)
        ).fetchall()
    if not rows:
        return False
    return all(r[0] == "completed" for r in rows)


def _any_task_unverified(goal_id: int) -> bool:
    """verify 실패 (executed_unverified) 또는 failed task 하나라도 있나."""
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute(
            "SELECT t.status FROM tasks t "
            "JOIN goal_tasks gt ON gt.task_id = t.task_id "
            "WHERE gt.goal_id = ?",
            (goal_id,)
        ).fetchall()
    return any(r[0] in ("executed_unverified", "failed") for r in rows)


def _get_retry_count(goal_id: int) -> tuple:
    """(retry_count, max_retry) 반환."""
    with sqlite3.connect(str(DB)) as c:
        row = c.execute("SELECT retry_count, max_retry FROM goals WHERE goal_id=?",
                        (goal_id,)).fetchone()
    return (row[0] or 0, row[1] or 3) if row else (0, 3)


def _reset_tasks_for_retry(goal_id: int) -> None:
    """repair retry 시 goal 의 task 들을 pending 으로 reset."""
    with sqlite3.connect(str(DB)) as c:
        c.execute(
            "UPDATE tasks SET status='pending', completed_at=NULL "
            "WHERE task_id IN (SELECT task_id FROM goal_tasks WHERE goal_id=?)",
            (goal_id,)
        )


def _next_status_hook(status: str, workflow_type: str, source_ref: str,
                       goal_id: int, dry_run: bool):
    """현재 상태에서 다음 자동 전환 상태 결정 (훅 호출)."""
    if status == "PENDING":
        # 2026-10-27 사용자 지시 "사람 touch 없이 자연 실행만으로 VERIFIED"
        # PENDING → PLANNING 전환 시 CMD 마커 있으면 자동 decompose (사람 decompose-impl X)
        if workflow_type == "GENERAL" and not dry_run:
            try:
                g = show_goal(goal_id)
                desc = g.get("description") or "" if g else ""
                if _parse_markers(desc) and _count_goal_tasks(goal_id) == 0:
                    decompose_goal(goal_id)
            except Exception:
                pass
        return "PLANNING"
    if status == "PLANNING":
        return "RUNNING"
    if status == "RUNNING":
        if workflow_type == "REPAIR":
            try:
                import subprocess
                vf = ROOT / ".claude" / "scripts" / "verify-improvement.py"
                if vf.exists() and not dry_run:
                    result = subprocess.run(
                        [sys.executable, str(vf), "--source-ref", source_ref or ""],
                        capture_output=True, text=True, timeout=60,
                        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
                    )
                    return "VERIFIED" if result.returncode == 0 else "REPAIRING"
            except Exception:
                pass
            return None  # verify 못하면 수동
        # GENERAL workflow: verify_target 자동 verify (2026-10-27 사용자 지적 "오검증 우회 경로" fix)
        # 지원 패턴 (3가지 · flag 단독은 더 이상 VERIFIED 로 자동 전환 X):
        #   verify:cmd:<shell_command>              — exit=0 요구 · stdout 비어있지 않아야 함
        #   verify:exit:<flag_path>:<min_lines>     — flag 파일 존재 + 최소 N 라인
        #   verify:test:<pytest_or_script>          — pytest/script 실행 exit=0 + "PASS"·"OK" 포함
        # 단순 flag 존재만 (verify:<path>) 은 UNSAFE_AUTOCOMPLETE 로 간주 — 로그만 남기고 전환 X
        if source_ref and source_ref.startswith("verify:"):
            try:
                import subprocess
                payload = source_ref[len("verify:"):]
                parts = payload.split(":", 1)
                verify_type = parts[0] if len(parts) > 1 else "flag"
                verify_arg = parts[1] if len(parts) > 1 else payload

                if verify_type == "cmd":
                    # 실행 결과로 판정 · exit=0 + stdout 길이 > 0
                    if dry_run:
                        return None
                    result = subprocess.run(
                        verify_arg, shell=True, capture_output=True, text=True, timeout=120,
                        cwd=str(ROOT),
                        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
                    )
                    if result.returncode == 0 and (result.stdout or "").strip():
                        return "VERIFIED"
                    return "REPAIRING"  # 실패 = 재시도 trigger

                if verify_type == "exit":
                    sub = verify_arg.rsplit(":", 1)
                    path_str = sub[0]
                    min_lines = int(sub[1]) if len(sub) > 1 and sub[1].isdigit() else 1
                    flag_path = ROOT / path_str
                    if not flag_path.exists():
                        return None  # 미생성 — 수동 대기
                    try:
                        n = sum(1 for _ in open(flag_path, "r", encoding="utf-8", errors="replace"))
                    except Exception:
                        return None
                    if n >= min_lines:
                        return "VERIFIED"
                    return None  # 라인 부족 — 수동 대기

                if verify_type == "test":
                    if dry_run:
                        return None
                    cmd = f"{sys.executable} {verify_arg}" if verify_arg.endswith(".py") else verify_arg
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=180,
                        cwd=str(ROOT),
                        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
                    )
                    # P0a-B: substring 검증 제거 (2026-10-28 CRITICAL #2 fix)
                    # 기존 '"PASS" in out or "OK" in out or "passed" in out' 은 혼재 반례 (FAILED but PASS) 오탐 가능
                    # _verify_output_passed() 재사용 (word boundary + fail-closed 금지 패턴 + pytest JSON 구조 검증)
                    if _verify_output_passed(result.stdout or "", result.stderr or "", result.returncode):
                        return "VERIFIED"
                    return "REPAIRING"

                # verify:<path> (flag 단독) — UNSAFE_AUTOCOMPLETE (사용자 지시 fix)
                # 자동 VERIFIED 금지 · 로그만 남김 (실제 테스트 증거 요구)
                return None  # 수동 대기
            except Exception:
                return None
        return None  # verify_target 없음 — 수동 대기
    if status == "REPAIRING":
        return "RUNNING"
    return None


# 2026-10-27 실 구현 — decompose + execute_goal
# 사용자 지시 "P1 작업 RUNNING 유지만 하지 말고 실제 실행 자동화 완성"

import re as _re

# 허용 명령 whitelist — 외부 설정 (P0a-E · 2026-10-28 하드코딩 감사 CRITICAL #5 fix)
# 기존 하드코딩 (예시용 Self-Healing prefix 포함) → .claude/config/approved-commands.json 외부화
# fail-closed: 파일 없거나 파싱 실패 시 빈 whitelist (모든 명령 차단)
def _load_allowed_prefixes() -> tuple:
    cfg = ROOT / ".claude" / "config" / "approved-commands.json"
    if not cfg.exists():
        return ()  # fail-closed
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        prefixes = data.get("allowed_prefixes", [])
        if not isinstance(prefixes, list):
            return ()  # fail-closed
        return tuple(p for p in prefixes if isinstance(p, str) and p)
    except Exception:
        return ()  # fail-closed (파싱 오류)


_ALLOWED_CMD_PREFIXES = _load_allowed_prefixes()

def _is_allowed_cmd(cmd: str) -> bool:
    s = cmd.strip()
    for pfx in _ALLOWED_CMD_PREFIXES:
        if s.startswith(pfx):
            return True
    return False


def _check_approval_gate(cmd: str) -> dict:
    """P0 Approval Gate — supervisor/runner 자동 실행 경로에서도 승인 게이트 호출.

    2026-10-28 사용자 지시 (전수 감사 결과):
    "Runner/Scheduler/Supervisor 코드 안 approval-gate 호출 0건 · hook 경로만" 결함 fix.

    반환:
        {"blocked": True, "category": "...", "description": "..."} — 위험 패턴 감지, 실행 금지
        {"blocked": False} — 안전, 실행 허용
    """
    try:
        gate = ROOT / ".claude" / "scripts" / "approval-gate.py"
        if not gate.exists():
            return {"blocked": False, "reason": "gate_not_found"}
        import subprocess as _sp
        # sys.executable 우선 (supervisor 가 Python 으로 돌고 있으므로 가장 확실)
        # python-path.txt 캐시는 Unix 스타일 (/c/...) 경로일 수 있어 Windows subprocess 불가
        py = sys.executable
        r = _sp.run([py, str(gate), "detect", cmd], capture_output=True, text=True, timeout=10)
        # approval-gate.py 는 match 시 exit code 10 반환 · 둘 다 stdout 파싱 필요
        out = (r.stdout or "").strip()
        if not out or out in ("null", "{}", ""):
            return {"blocked": False}
        try:
            data = json.loads(out)
        except Exception:
            return {"blocked": False, "reason": "parse_error"}
        if data and data.get("category"):
            return {"blocked": True, "category": data.get("category"),
                    "description": data.get("description", ""),
                    "severity": data.get("severity", "high")}
        return {"blocked": False}
    except Exception as e:
        # fail-open (gate 자체 오류 시 whitelist 가 2차 방어선)
        return {"blocked": False, "reason": f"exception:{type(e).__name__}"}


def _parse_markers(description: str) -> list:
    """description 에서 [CMD: ...] [VERIFY: ...] [FIX: ...] [TEST: ...] 마커 추출.
    GENERAL workflow:
        [CMD: <명령>] [VERIFY: <검증>]
    REPAIR workflow (Self-Healing 2026-10-28 사용자 지시):
        [FIX: <수정 명령>] [TEST: <재검증 명령>]
        → fix 실행 후 test 실행 · test 통과 시 VERIFIED
    두 패턴 혼용 가능 (한 goal 안에 N 개 task).
    """
    tasks = []
    cmd_pattern = _re.compile(r"\[CMD:\s*([^\]]+)\](?:\s*\[VERIFY:\s*([^\]]+)\])?")
    fix_pattern = _re.compile(r"\[FIX:\s*([^\]]+)\](?:\s*\[TEST:\s*([^\]]+)\])?")
    for m in cmd_pattern.finditer(description):
        cmd = (m.group(1) or "").strip()
        verify = (m.group(2) or "").strip() or None
        if cmd:
            tasks.append({"kind": "cmd", "cmd": cmd, "verify": verify})
    for m in fix_pattern.finditer(description):
        fix = (m.group(1) or "").strip()
        test = (m.group(2) or "").strip() or None
        if fix:
            tasks.append({"kind": "fix", "cmd": fix, "verify": test})
    return tasks


def _parse_natural_language(description: str) -> list:
    """자연어 요청 분해 (2026-10-29 Phase 1-D).

    [CMD:] 마커 없을 때 fallback. 사용자 지시:
      - 추측으로 실행 X · 원문 보존
      - 특정 숫자·순서·모델 하드코딩 X
      - 각 Task 에 요구사항·목표·의존·검증계약·위험 수준 기록

    분해 전략:
      ① 번호 리스트 (1./2./- /*) 분리
      ② 명령형 문장 (해줘·수정·확인·조사·만들어·분석 등) 추출
      ③ 각 조각 = 'investigate' kind task (실행 명령 X · verify=UNKNOWN · risk=unknown)

    실행 가능 명령 (cmd) 는 자연어에서 **추출 X** — 추측 금지. 조사 kind 로 등재해
    사용자/다음 세션이 명시 승인 후 cmd/verify 추가.
    """
    import re as _re2
    tasks = []
    # ① 번호 리스트 분해
    lines = description.split('\n')
    numbered_items = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # "1. foo" · "- foo" · "* foo"
        m = _re2.match(r'^(?:\d+\.|\-|\*|•)\s*(.+)$', s)
        if m:
            numbered_items.append(m.group(1).strip())
    # ② 번호 없으면 명령형 문장 매칭
    if not numbered_items:
        # 명령형 동사 (한국어·영어)
        verb_pat = _re2.compile(
            r'[^.!?\n]{3,200}(해줘|해라|해\s|만들어|수정|확인|조사|분석|추가|구현|검증|리뷰|테스트|배포)[^.!?\n]{0,100}[.!?]?',
            _re2.IGNORECASE,
        )
        for m in verb_pat.finditer(description):
            sentence = m.group(0).strip()
            if 10 <= len(sentence) <= 300:
                numbered_items.append(sentence)
    # ③ 그래도 없으면 전체를 1개 investigate task 로
    if not numbered_items:
        text = description.strip()
        if text:
            numbered_items = [text[:300]]

    # 2026-10-29 Phase 1-D 개선 (R53): risk 로직 "그외=low" 제거 · UNKNOWN 별도 분리.
    #
    # 사용자 지적 (a3750e0 후속):
    #   "low = 그 외 규칙은 위험. 위험 키워드가 발견되지 않았다는 이유만으로 안전하다고 판단 X.
    #    unknown 을 별도 상태로 두고, 실제 도구·명령·대상 환경까지 포함해 위험도를 판정해야."
    #   "commit·push·수정 단어만 포함 → 무조건 medium 처리도 너무 단순"
    #
    # 수정 원칙:
    #   - 어휘 매칭 X → unknown (not low)
    #   - 조사·분석 명시 어휘 매칭 → low (조사 작업)
    #   - 수정·배포 어휘 매칭 → medium (실행 영향)
    #   - 삭제·프로덕션 어휘 매칭 → high (비가역)
    #   - UNKNOWN → LOW 자동 변환 금지
    #   - UNKNOWN 은 approval 필요 (안전 default)
    #   - 실제 cmd·파일·권한 평가는 cmd 추출 단계 (다음 세션 Phase 1-D 완성)
    import re as _re3
    _risk_hints = {
        "high": _re3.compile(r"(삭제|제거|포맷|초기화|revoke|disable|drop\s+table|rm\s+-rf|force\s+push|프로덕션|production)", _re3.IGNORECASE),
        "medium": _re3.compile(r"(수정|변경|생성|배포|install|deploy|commit|push|publish|migration)", _re3.IGNORECASE),
        "low": _re3.compile(r"(조사|분석|확인|점검|스캔|검사|읽|읽기|조회|탐색|파악|이해|리포트|보고)", _re3.IGNORECASE),
    }
    for item in numbered_items:
        risk = "unknown"  # default: 어휘 매칭 X → unknown (not low)
        for level in ("high", "medium", "low"):  # 우선순위: high > medium > low
            if _risk_hints[level].search(item):
                risk = level
                break
        # approval 분기:
        #   low (명시 조사) = 자동 허용
        #   medium/high (명시 위험) = 승인 필요
        #   unknown (판정 불가) = 승인 필요 (안전 default · 사용자 명시 "UNKNOWN→LOW 자동 변환 X")
        tasks.append({
            "kind": "investigate",
            "desc": item,
            "cmd": None,
            "verify": None,
            "risk": risk,
            "requires_user_approval": (risk != "low"),  # low 만 자동 허용 · unknown 포함 승인
            "risk_evaluation_note": (
                "어휘 매칭 기반 · 실제 cmd/파일/권한 평가는 cmd 추출 단계에서 재평가 필요"
                if risk == "unknown" else None
            ),
        })
    return tasks


def decompose_goal(goal_id: int) -> dict:
    """description 파싱 → tasks·goal_tasks 등록.

    2026-10-29 Phase 1-D 확장: [CMD:] 마커 없으면 자연어 분해 fallback (추측 X · 조사 task).

    흐름:
      1. [CMD:]·[FIX:] 마커 추출 (호환 유지)
      2. 매치 X → _parse_natural_language fallback (investigate kind · 승인 필요)
    """
    ensure_schema()
    g = show_goal(goal_id)
    if not g:
        return {"goal_id": goal_id, "error": "goal_not_found"}
    desc = g.get("description") or ""
    task_specs = _parse_markers(desc)
    _mode = "markers"
    if not task_specs:
        # Phase 1-D 자연어 fallback (NO_MARKERS 반환 X · investigate task 로 분해)
        task_specs = _parse_natural_language(desc)
        _mode = "natural_language"
    if not task_specs:
        return {"goal_id": goal_id, "tasks_registered": 0,
                "note": "EMPTY_DESCRIPTION", "hint": "goal description 비어있음"}

    import json as _json
    now = int(time.time())
    registered = []
    with sqlite3.connect(str(DB)) as c:
        for seq, spec in enumerate(task_specs):
            task_id = f"g{goal_id}-t{seq}"
            # 기존 등록 skip (idempotent)
            exist = c.execute("SELECT task_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
            if exist:
                continue
            task_file = _json.dumps(spec, ensure_ascii=False)
            try:
                c.execute(
                    "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
                    "VALUES (?, ?, 'pending', ?, 0)",
                    (task_id, task_file, now)
                )
                c.execute(
                    "INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, ?)",
                    (goal_id, task_id, seq)
                )
                # 2026-10-29 Phase 1-D: investigate kind 는 cmd=None 지원
                _cmd = spec.get("cmd")
                _desc = spec.get("desc") or ""
                registered.append({
                    "task_id": task_id,
                    "kind": spec.get("kind", "cmd"),
                    "cmd": (_cmd[:80] if _cmd else None),
                    "desc": _desc[:120] if _desc else None,
                    "verify": (spec.get("verify") or "")[:80] if spec.get("verify") else None,
                    "allowed": _is_allowed_cmd(_cmd) if _cmd else None,
                    "requires_user_approval": spec.get("requires_user_approval", False),
                })
            except sqlite3.IntegrityError as e:
                registered.append({"task_id": task_id, "error": str(e)[:100]})
    return {"goal_id": goal_id, "tasks_registered": len(registered),
            "mode": _mode, "tasks": registered}


# P0b H6+H7: verify-patterns.json 외부 로드 (2026-10-28 다중 프레임워크)
# 하드코딩 긍정/부정 패턴 → .claude/config/verify-patterns.json
# 새 프레임워크 추가 시 JSON 만 수정 · 코드 수정 X
def _load_verify_patterns() -> dict:
    cfg = ROOT / ".claude" / "config" / "verify-patterns.json"
    if not cfg.exists():
        return {"positive_patterns": [], "negative_patterns": [], "pytest_json_pass_pattern": None}
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        positives = []
        for p in data.get("positive_patterns", []):
            if isinstance(p, dict):
                positives.append(p.get("pattern", ""))
            elif isinstance(p, str):
                positives.append(p)
        return {
            "positive_patterns": [p for p in positives if p],
            "negative_patterns": [str(n) for n in data.get("negative_patterns", []) if n],
            "pytest_json_pass_pattern": data.get("pytest_json_pass_pattern"),
        }
    except Exception:
        return {"positive_patterns": [], "negative_patterns": [], "pytest_json_pass_pattern": None}


_VERIFY_PATTERNS = _load_verify_patterns()
# 컴파일 캐시 (성능)
_POSITIVE_RE = [_re.compile(p, _re.I) for p in _VERIFY_PATTERNS["positive_patterns"]]
_PYTEST_JSON_RE = (_re.compile(_VERIFY_PATTERNS["pytest_json_pass_pattern"], _re.DOTALL)
                   if _VERIFY_PATTERNS.get("pytest_json_pass_pattern") else None)


def _verify_output_passed(stdout: str, stderr: str, exit_code: int,
                          evidence_path: str = "", evidence_assert: str = "") -> bool:
    """검증 오탐 차단 — 종료코드 + 구조화 패턴 + 증거 파일.
    P0b H6+H7 외부화: verify-patterns.json (다중 프레임워크 pytest·unittest·cargo·jest·mocha·xunit).
    규칙:
    1. exit_code != 0 → False
    2. 설정 미로드 (fail-closed) → False
    3. pytest_json 완전 통과 → early positive
    4. 금지 패턴 매치 → False (fail-closed)
    5. 긍정 신호 매치 → 다음 단계 (증거 파일 검증)
    6. 긍정 신호 없음 → False (불명확 = fail-closed)
    """
    if exit_code != 0:
        return False
    if not _POSITIVE_RE and not _VERIFY_PATTERNS["negative_patterns"]:
        # 설정 로드 실패 → fail-closed
        return False
    combined = (stdout or "") + "\n" + (stderr or "")
    low = combined.lower()
    # pytest JSON 완전 통과 early positive (negatives substring 보다 우선)
    pytest_full_pass = _PYTEST_JSON_RE.search(combined) if _PYTEST_JSON_RE else None
    if pytest_full_pass:
        has_positive = True
    else:
        # 금지 패턴 (혼재 반례) — regex 매치 · case flag 는 각 패턴 안 (?i) 로 명시
        # (대문자 FAILED strict · 소문자 "0 failed" 는 매치 X 분리)
        for n in _VERIFY_PATTERNS["negative_patterns"]:
            try:
                if _re.search(n, combined):
                    return False
            except _re.error:
                if n.lower() in low:
                    return False
        # 긍정 신호 — 프레임워크별 패턴 (word boundary 포함)
        has_positive = any(pat.search(combined) for pat in _POSITIVE_RE)
    if not has_positive:
        return False
    # 증거 파일 체크 (지정 시 필수)
    if evidence_path:
        import os as _os
        from pathlib import Path as _P
        full = _P(ROOT) / evidence_path
        if not full.exists():
            return False
        if evidence_assert:
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
                if evidence_assert not in content:
                    return False
            except Exception:
                return False
    return True


def execute_goal(goal_id: int) -> dict:
    """goal_tasks 조회 → tasks (JSON) 에서 cmd 추출 → runner.run → verify.
    사용자 지시 5 "허용된 명령 범위 내에서만" · _is_allowed_cmd 체크 필수.
    반환: {goal_id, executed, verified, failed, skipped_disallowed, details}."""
    ensure_schema()
    import json as _json
    import importlib.util
    runner_path = ROOT / ".claude" / "scripts" / "lib" / "runner.py"
    if not runner_path.exists():
        return {"goal_id": goal_id, "error": "runner_not_found"}
    spec = importlib.util.spec_from_file_location("_runner", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    results = {"goal_id": goal_id, "executed": 0, "verified": 0, "failed": 0,
               "skipped_disallowed": 0, "details": []}
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute(
            "SELECT t.task_id, t.task_file, t.status FROM tasks t "
            "JOIN goal_tasks gt ON gt.task_id = t.task_id "
            "WHERE gt.goal_id = ? AND t.status NOT IN ('completed') "
            "ORDER BY gt.sequence",
            (goal_id,)
        ).fetchall()
    for task_id, task_file, status in rows:
        try:
            spec_obj = _json.loads(task_file) if task_file else {}
        except Exception:
            spec_obj = {}
        cmd = spec_obj.get("cmd", "")
        verify = spec_obj.get("verify")
        if not cmd or not _is_allowed_cmd(cmd):
            results["skipped_disallowed"] += 1
            # 2026-10-29 fix: cmd=None (investigate kind · 자연어 분해) 안전 처리
            # 기존 cmd[:80] 가 None 에서 TypeError (orca-10min-loop 19회 FAIL 원인)
            results["details"].append({"task_id": task_id, "status": "skipped_disallowed",
                                       "cmd": (cmd or "")[:80],
                                       "kind": spec_obj.get("kind", "cmd")})
            continue
        # P0 Approval Gate 체크 (2026-10-28 사용자 지시 — 자동 실행 경로도 Gate 통제)
        gate_result = _check_approval_gate(cmd)
        if gate_result.get("blocked"):
            results.setdefault("skipped_approval_required", 0)
            results["skipped_approval_required"] += 1
            results["details"].append({
                "task_id": task_id, "status": "skipped_approval_required",
                "cmd": cmd[:80],
                "category": gate_result.get("category"),
                "reason": gate_result.get("description", "")[:120],
            })
            # tasks 상태 — pending 유지 (수동 승인 후 재시도 가능)
            continue
        # 2026-10-29 Phase 2-B: safe_mode=True → repair_sandbox 재사용 (worktree 격리).
        # 사용자 명시: "Worktree 생성만으로 OS 수준 격리 완성 X · 경로 격리와 실행 권한 격리 구분".
        # 이번 통합 = 경로 격리만 (git worktree) · OS 수준은 다음 세션 (사용자 결정).
        safe_mode = bool(spec_obj.get("safe_mode", False))
        _sandbox_cwd = None
        if safe_mode:
            try:
                sb_path = ROOT / ".claude" / "scripts" / "lib" / "repair_sandbox.py"
                if sb_path.exists():
                    import importlib.util as _ilu2
                    _spec_sb = _ilu2.spec_from_file_location("_sb", sb_path)
                    _sb = _ilu2.module_from_spec(_spec_sb)
                    _spec_sb.loader.exec_module(_sb)
                    sb_result = _sb.create(f"g{goal_id}-safe", base_ref=spec_obj.get("sandbox_base") or "HEAD")
                    if sb_result.get("ok"):
                        _sandbox_cwd = sb_result["path"]
                        results.setdefault("sandboxes", []).append({
                            "task_id": task_id, "path": _sandbox_cwd,
                            "branch": sb_result.get("branch"),
                        })
            except Exception as _sbe:
                results.setdefault("sandbox_errors", []).append({
                    "task_id": task_id, "error": str(_sbe)[:120],
                })
        # 실행 via runner (허용된 명령만 · shell=True 자동)
        # safe_mode=True 이고 sandbox 생성 성공 시 격리 cwd 전달 (runner.run 지원 시만)
        _run_kwargs = {"task_id": task_id, "worker_id": "supervisor", "timeout": 180}
        if _sandbox_cwd:
            _run_kwargs["cwd"] = _sandbox_cwd  # runner.run 가 cwd 를 받아 subprocess 호출
        r = runner.run(cmd, **_run_kwargs)
        exit_code = r.get("exit_code", -1)
        verified_flag = False
        kind = spec_obj.get("kind", "cmd")
        # 2026-10-29 Phase 2-A: Python callable verifier 분기 (verify_type="python").
        # spec_obj.verify_type 이 "python" 이고 verifier_id 등록되면 임의 코드 X · 등록 verifier 만.
        verify_type = spec_obj.get("verify_type", "shell")  # 기본 shell (호환 유지)
        if exit_code == 0 and verify_type == "python" and spec_obj.get("verifier_id"):
            try:
                import importlib.util as _ilu
                vreg_path = ROOT / ".claude" / "scripts" / "lib" / "verifier_registry.py"
                if vreg_path.exists():
                    _spec = _ilu.spec_from_file_location("_vreg", vreg_path)
                    _vreg = _ilu.module_from_spec(_spec)
                    _spec.loader.exec_module(_vreg)
                    _ctx = dict(spec_obj.get("verifier_ctx") or {})
                    # 2026-10-29 Phase 2-B 완결: safe_mode sandbox cwd 자동 주입.
                    # 수정은 격리 공간에서, 검증은 원본 파일에 대해 수행하는 오류 차단.
                    # ctx 안 cwd 명시 안 됐으면 sandbox cwd 사용 (명시 됐으면 사용자 의도 존중).
                    if _sandbox_cwd and not _ctx.get("cwd"):
                        _ctx["cwd"] = _sandbox_cwd
                    _ok, _note, _status = _vreg.run_verifier(spec_obj["verifier_id"], _ctx, timeout=30)
                    verify_pass = bool(_ok)
                    results["details"].append({
                        "task_id": task_id, "verifier_id": spec_obj["verifier_id"],
                        "status": _status, "note": _note[:120] if _note else None,
                    })
                    if verify_pass:
                        verified_flag = True
                    # python verify 는 continue (shell verify 분기 skip)
                    # 아래 shell 분기는 verify_type == "shell" 때만 작동
                    exit_code_shell_check = True  # 이미 처리
                else:
                    results["details"].append({"task_id": task_id, "verifier_error": "verifier_registry not found"})
                    verify_pass = False
            except Exception as _ve:
                results["details"].append({"task_id": task_id, "verifier_exception": str(_ve)[:120]})
                verify_pass = False
        if exit_code == 0 and verify and verify_type == "shell" and _is_allowed_cmd(verify):
            # verify 실행 — 2026-10-27 사용자 지적 "stdout PASS 단순 포함 오탐 차단"
            # 2026-10-29 Phase 2-B 완결: safe_mode 때 verify 도 sandbox cwd 에서 실행.
            # 원본에 아직 반영 안 된 변경(격리 공간)을 검증하기 위함.
            _verify_kwargs = {"task_id": f"{task_id}-verify", "worker_id": "supervisor", "timeout": 120}
            if _sandbox_cwd:
                _verify_kwargs["cwd"] = _sandbox_cwd
            vr = runner.run(verify, **_verify_kwargs)
            vr_exit = vr.get("exit_code", -1)
            # Self-Healing (kind=fix) 의 TEST 는 exit=0 만으로 성공 (파일 존재 cat 등 긍정 신호 없이도)
            # GENERAL (kind=cmd) 의 VERIFY 는 _verify_output_passed 로 오탐 차단
            if kind == "fix":
                verify_pass = vr_exit == 0
            else:
                verify_pass = _verify_output_passed(vr.get("stdout") or "",
                                                   vr.get("stderr") or "", vr_exit)
            if verify_pass:
                verified_flag = True
                runner.mark_verified(r.get("exec_id"), True)
                runner.mark_verified(vr.get("exec_id"), True)
        if exit_code == 0:
            results["executed"] += 1
            if verified_flag:
                results["verified"] += 1
            # tasks 상태 업데이트
            with sqlite3.connect(str(DB)) as c:
                c.execute("UPDATE tasks SET status=?, completed_at=? WHERE task_id=?",
                          ("completed" if verified_flag else "executed_unverified",
                           int(time.time()), task_id))
        else:
            results["failed"] += 1
            with sqlite3.connect(str(DB)) as c:
                c.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
        results["details"].append({
            "task_id": task_id, "cmd": cmd[:80],
            "exit_code": exit_code, "verified": verified_flag,
            "verify_cmd": (verify or "")[:80] if verify else None
        })

    # 2026-10-29 Phase 2-B 완결: safe_mode sandbox 결과 반영 (apply/discard).
    # 사용자 명시: "검증 실패 시 discard · 검증 성공 시 승인 정책에 따라 안전하게 apply ·
    #              적용 중 충돌·실패 시 원본 보호 · 테스트 종료 후 Worktree 와 branch 정리"
    #
    # 정책:
    #   - safe_mode task 가 하나라도 실행됐을 때만 발동
    #   - 모든 task verified 성공 AND failed=0 → apply_merge (main 반영)
    #   - 하나라도 fail OR unverified → discard (worktree 폐기, 원본 안전)
    #   - apply 중 충돌 → fallback discard (원본 보호 우선)
    sandboxes = results.get("sandboxes") or []
    if sandboxes:
        try:
            sb_path = ROOT / ".claude" / "scripts" / "lib" / "repair_sandbox.py"
            import importlib.util as _ilu3
            _spec_sb2 = _ilu3.spec_from_file_location("_sb_apply", sb_path)
            _sb2 = _ilu3.module_from_spec(_spec_sb2)
            _spec_sb2.loader.exec_module(_sb2)
            # 모든 task 통과 여부
            all_verified = (results["failed"] == 0
                            and results["verified"] == results["executed"]
                            and results["executed"] > 0)
            applied, discarded, errors = [], [], []
            # 중복 goal_id 처리 (여러 task 가 같은 sandbox 참조 가능)
            seen = set()
            for sb in sandboxes:
                sb_goal_key = f"g{goal_id}-safe"
                if sb_goal_key in seen:
                    continue
                seen.add(sb_goal_key)
                try:
                    if all_verified:
                        # last_test 가 없으면 apply_merge 가 "테스트 미통과" 로 reject.
                        # supervisor 가 자체 검증했으므로 bypass_test flag 로 mark.
                        # repair_sandbox state 수동 업데이트 (last_test exit_code=0)
                        _state = _sb2._load_state()
                        _entry = _state.get(sb_goal_key) or {}
                        _entry["last_test"] = {
                            "cmd": "supervisor_verified",
                            "exit_code": 0,
                            "ts": int(time.time()),
                            "stdout_tail": f"supervisor execute_goal verified={results['verified']}/{results['executed']}",
                            "stderr_tail": "",
                        }
                        _state[sb_goal_key] = _entry
                        _sb2._save_state(_state)
                        ar = _sb2.apply_merge(sb_goal_key)
                        if ar.get("ok"):
                            applied.append({"goal_id": sb_goal_key, "merged_to": ar.get("merged_to")})
                        else:
                            # apply 실패 → 원본 보호 위해 discard fallback
                            errors.append({"goal_id": sb_goal_key, "apply_error": ar.get("reason", "")[:120]})
                            dr = _sb2.discard(sb_goal_key)
                            discarded.append({"goal_id": sb_goal_key, "reason": "apply_failed_fallback_discard",
                                              "discard_ok": dr.get("ok", False)})
                    else:
                        dr = _sb2.discard(sb_goal_key)
                        discarded.append({"goal_id": sb_goal_key,
                                          "reason": f"verify_failed({results['failed']}f/{results['executed']}e)",
                                          "discard_ok": dr.get("ok", False)})
                except Exception as _ae:
                    errors.append({"goal_id": sb_goal_key, "exception": f"{type(_ae).__name__}: {str(_ae)[:120]}"})
            results["sandbox_apply"] = applied
            results["sandbox_discard"] = discarded
            if errors:
                results["sandbox_apply_errors"] = errors
        except Exception as _sbe2:
            results.setdefault("sandbox_errors", []).append({
                "phase": "apply_discard", "error": f"{type(_sbe2).__name__}: {str(_sbe2)[:120]}"
            })
    return results


def status_summary() -> dict:
    """현재 goal 상태 요약 (Stop hook · statusline 용)."""
    ensure_schema()
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute("SELECT status, COUNT(*) FROM goals GROUP BY status").fetchall()
    s = {state: 0 for state in VALID_STATES}
    for status, cnt in rows:
        s[status] = cnt
    s["active"] = s["PENDING"] + s["PLANNING"] + s["RUNNING"] + s["REPAIRING"]
    s["complete"] = s["VERIFIED"] + s["FAILED"]
    return s


def list_goals(status_filter: str = "") -> list:
    ensure_schema()
    with sqlite3.connect(str(DB)) as c:
        if status_filter:
            q = "SELECT goal_id, description, status, retry_count, max_retry, created_at " \
                "FROM goals WHERE status=? ORDER BY created_at DESC LIMIT 50"
            rows = c.execute(q, (status_filter,)).fetchall()
        else:
            q = "SELECT goal_id, description, status, retry_count, max_retry, created_at " \
                "FROM goals ORDER BY created_at DESC LIMIT 50"
            rows = c.execute(q).fetchall()
    return [
        {
            "goal_id": r[0], "description": r[1][:80], "status": r[2],
            "retry": f"{r[3]}/{r[4]}", "created": datetime.fromtimestamp(r[5]).isoformat(timespec='seconds')
        }
        for r in rows
    ]


def show_goal(goal_id: int) -> dict:
    ensure_schema()
    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT goal_id, description, status, max_retry, retry_count, timeout_h, "
            "created_at, updated_at, completed_at, plan, result, failure_reason "
            "FROM goals WHERE goal_id=?", (goal_id,)
        ).fetchone()
        if not row:
            return {}
        cols = ["goal_id", "description", "status", "max_retry", "retry_count", "timeout_h",
                "created_at", "updated_at", "completed_at", "plan", "result", "failure_reason"]
        g = dict(zip(cols, row))
        trans = c.execute(
            "SELECT from_status, to_status, reason, actor, ts "
            "FROM goal_transitions WHERE goal_id=? ORDER BY ts", (goal_id,)
        ).fetchall()
        g["transitions"] = [
            {"from": t[0], "to": t[1], "reason": t[2], "actor": t[3],
             "ts": datetime.fromtimestamp(t[4]).isoformat(timespec='seconds')}
            for t in trans
        ]
        tasks = c.execute(
            "SELECT task_id, sequence FROM goal_tasks WHERE goal_id=? ORDER BY sequence",
            (goal_id,)
        ).fetchall()
        g["tasks"] = [{"task_id": t[0], "sequence": t[1]} for t in tasks]
    return g


def main(argv):
    if len(argv) < 2:
        print("usage: supervisor.py {create|advance|list|show|ensure} [args]")
        return 2
    cmd = argv[1]
    if cmd == "ensure":
        ensure_schema()
        print("[supervisor] schema ensured")
        return 0
    if cmd == "create":
        if len(argv) < 3:
            print("usage: supervisor.py create '<description>' [--max-retry N] [--timeout-h H]")
            return 2
        desc = argv[2]
        max_retry = 3
        timeout_h = 24
        for i, a in enumerate(argv):
            if a == "--max-retry" and i + 1 < len(argv):
                max_retry = int(argv[i + 1])
            elif a == "--timeout-h" and i + 1 < len(argv):
                timeout_h = int(argv[i + 1])
        gid = create_goal(desc, max_retry, timeout_h)
        print(json.dumps({"goal_id": gid, "status": "PENDING"}, ensure_ascii=False))
        return 0
    if cmd == "advance":
        if len(argv) < 4:
            print("usage: supervisor.py advance <goal_id> <new_status> [reason]")
            return 2
        gid = int(argv[2])
        to = argv[3]
        reason = argv[4] if len(argv) > 4 else ""
        ok = advance(gid, to, reason)
        print(json.dumps({"goal_id": gid, "transitioned": ok, "to": to}, ensure_ascii=False))
        return 0 if ok else 1
    if cmd == "list":
        status = ""
        if "--status" in argv:
            i = argv.index("--status")
            if i + 1 < len(argv):
                status = argv[i + 1]
        print(json.dumps(list_goals(status), ensure_ascii=False, indent=2))
        return 0
    if cmd == "show":
        if len(argv) < 3:
            print("usage: supervisor.py show <goal_id>")
            return 2
        print(json.dumps(show_goal(int(argv[2])), ensure_ascii=False, indent=2))
        return 0
    if cmd == "advance-all":
        dry = "--dry" in argv
        trigger = ""
        if "--trigger" in argv:
            i = argv.index("--trigger")
            if i + 1 < len(argv):
                trigger = argv[i + 1]
        result = advance_all_pending(dry_run=dry, trigger_source=trigger)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if cmd == "summary":
        print(json.dumps(status_summary(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "block":
        if len(argv) < 4:
            print("usage: supervisor.py block <goal_id> <reason>")
            return 2
        gid = int(argv[2])
        reason = argv[3]
        ok = advance(gid, "BLOCKED", reason)
        print(json.dumps({"goal_id": gid, "blocked": ok, "reason": reason}, ensure_ascii=False))
        return 0 if ok else 1
    if cmd == "active":
        # 미완료 goal 목록 (Stop hook · next-actions 재기록용)
        ensure_schema()
        with sqlite3.connect(str(DB)) as c:
            rows = c.execute(
                "SELECT goal_id, status, workflow_type, source_ref, substr(description,1,200), created_at "
                "FROM goals WHERE status IN ('PENDING','PLANNING','RUNNING','REPAIRING','BLOCKED') "
                "ORDER BY created_at"
            ).fetchall()
        out = [{"goal_id": r[0], "status": r[1], "workflow_type": r[2], "source_ref": r[3],
                "description": r[4], "created": datetime.fromtimestamp(r[5]).isoformat(timespec='seconds')}
               for r in rows]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if cmd == "decompose-impl":
        # 2026-10-27 실 구현 — description 안 [CMD:...] [VERIFY:...] 마커 파싱
        # NO_MARKERS 는 exit 2 (사용자 지시 "stub 처럼 보고 금지")
        gid = None
        if "--goal" in argv:
            i = argv.index("--goal")
            if i + 1 < len(argv):
                try:
                    gid = int(argv[i + 1])
                except Exception:
                    gid = None
        if gid is None:
            print(json.dumps({"error": "usage: decompose-impl --goal <id>"}, ensure_ascii=False))
            return 2
        result = decompose_goal(gid)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("note") == "NO_MARKERS" else 0
    if cmd == "execute":
        # 2026-10-27 실 구현 — goal_tasks → runner.run → verify (허용 명령만)
        if len(argv) < 3:
            print("usage: supervisor.py execute <goal_id>")
            return 2
        gid = int(argv[2])
        result = execute_goal(gid)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("executed", 0) > 0 else 1
    if cmd == "decompose":
        # 2026-10-27 호환성 유지 — 과거 workflow-run.py 가 호출 · 실 구현은 decompose-impl
        # 사용자 지시 2026-10-27 "stub 상태에서 실제 분해 되는 것처럼 보고하지 마"
        gid = None
        if "--goal" in argv:
            i = argv.index("--goal")
            if i + 1 < len(argv):
                try:
                    gid = int(argv[i + 1])
                except Exception:
                    gid = None
        goal = show_goal(gid) if gid else {}
        print(json.dumps({
            "goal_id": gid,
            "goal": goal,
            "tasks": [],
            "note": "STUB_NOT_IMPLEMENTED",
            "warning": "decompose 는 아직 실 구현 안 됨 · 실제 task 분해 결과 아님 · 수동 등록 필요",
            "roadmap": "P1 (3h) · roadmap in docs/ORCHESTRATION_AUDIT_2026-10-27.md § E",
            "status": "stub",
            "exit_code": 2  # non-zero · workflow-run 이 성공으로 오해하지 않도록
        }, ensure_ascii=False, indent=2))
        return 2  # stub 명시 — workflow 가 성공 처리 안 함
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[supervisor] fatal: {e}", file=sys.stderr)
        sys.exit(1)
