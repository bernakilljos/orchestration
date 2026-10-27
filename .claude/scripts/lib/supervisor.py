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


def advance_all_pending(dry_run: bool = False) -> dict:
    """모든 미완료 goal 을 다음 상태로 자동 진행 (사용자 지시 '10개 중 2개 멈추지 마' fix).
    PENDING → PLANNING → RUNNING → VERIFIED 자동 루프.
    - 독립 goal 병렬 처리 (하나 FAIL 해도 나머지 계속)
    - Timeout 초과 goal 은 FAILED
    - REPAIR workflow 는 verify-improvement.py 자동 호출
    - GENERAL workflow 는 PLANNING/RUNNING 전환만 (실제 agent dispatch 는 호출자 책임)
    """
    ensure_schema()
    advanced = {"PENDING": 0, "PLANNING": 0, "RUNNING": 0, "REPAIRING": 0, "FAILED": 0, "BLOCKED": 0}
    details = []
    with sqlite3.connect(str(DB)) as c:
        # BLOCKED 는 외부 의존 대기 — 자동 진행 스킵 (다른 goal 은 계속)
        rows = c.execute(
            "SELECT goal_id, status, workflow_type, source_ref, timeout_h, created_at "
            "FROM goals WHERE status IN ('PENDING', 'PLANNING', 'RUNNING', 'REPAIRING') "
            "ORDER BY created_at"
        ).fetchall()
    now = int(time.time())
    for goal_id, status, wtype, source_ref, timeout_h, created_at in rows:
        if timeout_h and (now - created_at) > timeout_h * 3600:
            if not dry_run:
                advance(goal_id, "FAILED", f"timeout {timeout_h}h 초과", "supervisor:auto")
            advanced["FAILED"] += 1
            details.append({"goal_id": goal_id, "action": "FAILED(timeout)"})
            continue
        next_status = _next_status_hook(status, wtype, source_ref, goal_id, dry_run)
        if next_status:
            if not dry_run:
                advance(goal_id, next_status, f"auto advance from {status}", "supervisor:auto")
            advanced[status] = advanced.get(status, 0) + 1
            details.append({"goal_id": goal_id, "from": status, "to": next_status})
    return {"advanced": advanced, "details": details, "timestamp": now}


def _next_status_hook(status: str, workflow_type: str, source_ref: str,
                       goal_id: int, dry_run: bool):
    """현재 상태에서 다음 자동 전환 상태 결정 (훅 호출)."""
    if status == "PENDING":
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
                    out = (result.stdout or "") + (result.stderr or "")
                    if result.returncode == 0 and ("PASS" in out or "OK" in out or "passed" in out):
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
        result = advance_all_pending(dry_run=dry)
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
    if cmd == "decompose":
        # 2026-10-27 workflow-run.py 04-plan 지원 · stub (실 구현 미완)
        # 사용자 지적 2026-10-27 "stub 상태에서 실제 분해 되는 것처럼 보고하지 마"
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
