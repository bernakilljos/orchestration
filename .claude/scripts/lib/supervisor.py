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

VALID_STATES = ("PENDING", "PLANNING", "RUNNING", "VERIFIED", "REPAIRING", "FAILED")

# 허용되는 상태 전환 (A → B)
ALLOWED_TRANSITIONS = {
    "PENDING":   {"PLANNING", "FAILED"},
    "PLANNING":  {"RUNNING", "FAILED"},
    "RUNNING":   {"VERIFIED", "REPAIRING", "FAILED"},
    "REPAIRING": {"RUNNING", "FAILED"},
    "VERIFIED":  set(),  # 종결
    "FAILED":    set(),  # 종결
}


def ensure_schema() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB)) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS goals (
          goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
          description TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PENDING',
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


def create_goal(description: str, max_retry: int = 3, timeout_h: int = 24) -> int:
    ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        cur = c.execute(
            "INSERT INTO goals (description, status, max_retry, timeout_h, created_at, updated_at) "
            "VALUES (?, 'PENDING', ?, ?, ?, ?)",
            (description, max_retry, timeout_h, now, now)
        )
        goal_id = cur.lastrowid
        c.execute(
            "INSERT INTO goal_transitions (goal_id, from_status, to_status, actor, ts) "
            "VALUES (?, NULL, 'PENDING', 'supervisor', ?)",
            (goal_id, now)
        )
    return goal_id


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
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[supervisor] fatal: {e}", file=sys.stderr)
        sys.exit(1)
