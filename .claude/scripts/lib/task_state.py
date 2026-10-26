"""task_state.py — 2026-10-26 P1-1 완결용 상태머신 helper.

워커 .bat (codex-auto·gemini-auto·haiku-auto) 가 task pick-up / 완료 / 실패 시 호출.
orca.db.tasks 테이블 상태 전환: pending → locked → completed / failed.

사용:
  python task_state.py update <task_id> locked [worker_id]
  python task_state.py update <task_id> completed
  python task_state.py update <task_id> failed

best-effort: DB 없거나 UPDATE 실패해도 silently return (워커 자체는 방해 X).
"""
from __future__ import annotations
import sys
import os
import sqlite3
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"


def update(task_id: str, status: str, worker_id: str = "") -> bool:
    """Returns True if row affected, False if no-op or error.
    2026-10-26 CAS: locked 는 pending 상태에서만 성공 (race condition 방지)."""
    if not DB.exists() or not task_id:
        return False
    now = int(time.time())
    try:
        with sqlite3.connect(str(DB)) as c:
            if status == "locked":
                # CAS (compare-and-swap): pending → locked 만 허용 · 이미 locked/completed 면 no-op
                cur = c.execute(
                    "UPDATE tasks SET status=?, worker_id=?, locked_at=? "
                    "WHERE task_id=? AND status='pending'",
                    (status, worker_id or "unknown", now, task_id),
                )
                return cur.rowcount > 0
            elif status in ("completed", "failed"):
                cur = c.execute(
                    "UPDATE tasks SET status=?, completed_at=? WHERE task_id=?",
                    (status, now, task_id),
                )
                return cur.rowcount > 0
            else:
                cur = c.execute(
                    "UPDATE tasks SET status=? WHERE task_id=?",
                    (status, task_id),
                )
                return cur.rowcount > 0
    except Exception:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(0)  # best-effort — silent
    cmd = sys.argv[1]
    task_id = sys.argv[2]
    status = sys.argv[3]
    worker_id = sys.argv[4] if len(sys.argv) > 4 else ""
    if cmd == "update":
        update(task_id, status, worker_id)
    sys.exit(0)
