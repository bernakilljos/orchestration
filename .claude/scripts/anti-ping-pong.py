#!/usr/bin/env python
"""
Anti-Ping-Pong Detector (P1-C) — 같은 수정 3회+ 반복 감지 시 체인 중단

근거:
- 외부 감사 docs/ORCHESTRATION_AUDIT_1027.md § E Self-Healing (Anti-Ping-Pong 미구현)
- 2026-10-27 statusline 핑퐁 24회+ 사례 (사용자 "너무 힘들다")
- Operating Principles § 3 최소 변경 · § 8 재발 = 품질 실패

로직:
1. file_audit 테이블에서 최근 24h 수정 조회
2. (path, hunk_hash) 기준 반복 횟수 집계
3. 3회+ 반복 감지 → exit 2 (block) + 경고 메시지
4. 5회+ → auto-rollback 제안 (실행은 사용자 승인)

CLI:
  python anti-ping-pong.py check --file <path>
  python anti-ping-pong.py check --goal <goal_id>
  python anti-ping-pong.py stats --days 7
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
# R375 Hook 응답성 (2026-11-28 실측): 훅 응답 경로에서 orca.db 잠금 시 기본 5초 대기 × 여러 문장 = Edit 마다 약 7.5초 정지
#   → 기록 전용 연결은 짧게 기다리고 못 잡으면 기록 생략 (ORCA_HOOK_DB_TIMEOUT 초 · 기본 0.5)
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import state_db as _sdb  # noqa: E402 — 훅 기록 정본 (전체 마감 · 스풀)
_DB_TIMEOUT = _sdb.hook_db_budget()
_PP_SETUP = ("""CREATE TABLE IF NOT EXISTS ping_pong_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP, path TEXT NOT NULL,
            hunk_hash TEXT NOT NULL, goal_id INTEGER, session_id TEXT, diff_preview TEXT)""",
             "CREATE INDEX IF NOT EXISTS idx_pp_path_hash ON ping_pong_tracker(path, hunk_hash)")
LOG = ROOT / ".claude" / "logs" / "anti-ping-pong.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

THRESHOLD_WARN = 3        # 3회 → 경고 + exit 1
THRESHOLD_BLOCK = 5       # 5회 → exit 2 + rollback 제안
WINDOW_HOURS = 24


def _ensure_table() -> None:
    """ping_pong_tracker 테이블 자동 생성."""
    if not DB.exists():
        DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB), timeout=_DB_TIMEOUT)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ping_pong_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            path TEXT NOT NULL,
            hunk_hash TEXT NOT NULL,
            goal_id INTEGER,
            session_id TEXT,
            diff_preview TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pp_path_hash ON ping_pong_tracker(path, hunk_hash)")
    conn.commit()
    conn.close()


def record(path: str, diff: str, goal_id: int | None = None, session_id: str | None = None) -> int:
    """수정 기록. hunk_hash = SHA-256(path + diff first 500 chars)."""
    # R375 6차 검토: 연결·SQL·commit 전부 전체 마감 안 (state_db.bounded_insert) · 못 쓰면 스풀 · 예외에도 close
    if not DB.exists():
        DB.parent.mkdir(parents=True, exist_ok=True)
        sqlite3.connect(str(DB)).close()
    hunk = hashlib.sha256(f"{path}:{diff[:500]}".encode()).hexdigest()[:16]
    r = _sdb.bounded_insert(DB, "ping_pong_tracker", [(
        "INSERT INTO ping_pong_tracker (path, hunk_hash, goal_id, session_id, diff_preview) VALUES (?, ?, ?, ?, ?)",
        [path, hunk, goal_id, session_id, diff[:200]])], setup=_PP_SETUP)
    if not r.startswith("ok"):
        return 0                                   # 스풀됨 = 횟수 미확인 (호출부는 0 을 경고 없음으로 처리)
    sess = None
    try:                                           # 같은 hunk 반복 횟수 — 짧은 마감 안에서만
        sess = _sdb.BoundedSession(DB, min(0.2, _DB_TIMEOUT))
        cur = sess.sql(f"SELECT COUNT(*) FROM ping_pong_tracker WHERE path = ? AND hunk_hash = ? "
                       f"AND ts > datetime('now', '-{WINDOW_HOURS} hours')", (path, hunk))
        return int(cur.fetchone()[0])
    except Exception:  # noqa: BLE001
        return 0
    finally:
        if sess is not None:
            sess.close()


def check(path: str | None = None, goal_id: int | None = None) -> dict:
    """반복 수정 조회."""
    _ensure_table()
    conn = sqlite3.connect(str(DB), timeout=_DB_TIMEOUT)
    if path:
        cur = conn.execute(
            f"""SELECT path, hunk_hash, COUNT(*) as n, MAX(ts) as last_ts
                FROM ping_pong_tracker
                WHERE path = ? AND ts > datetime('now', '-{WINDOW_HOURS} hours')
                GROUP BY path, hunk_hash
                HAVING n >= {THRESHOLD_WARN}
                ORDER BY n DESC""",
            (path,),
        )
    elif goal_id:
        cur = conn.execute(
            f"""SELECT path, hunk_hash, COUNT(*) as n, MAX(ts) as last_ts
                FROM ping_pong_tracker
                WHERE goal_id = ? AND ts > datetime('now', '-{WINDOW_HOURS} hours')
                GROUP BY path, hunk_hash
                HAVING n >= {THRESHOLD_WARN}
                ORDER BY n DESC""",
            (goal_id,),
        )
    else:
        cur = conn.execute(
            f"""SELECT path, hunk_hash, COUNT(*) as n, MAX(ts) as last_ts
                FROM ping_pong_tracker
                WHERE ts > datetime('now', '-{WINDOW_HOURS} hours')
                GROUP BY path, hunk_hash
                HAVING n >= {THRESHOLD_WARN}
                ORDER BY n DESC"""
        )
    rows = [dict(zip(("path", "hunk_hash", "count", "last_ts"), r)) for r in cur.fetchall()]
    conn.close()
    status = "ok"
    exit_code = 0
    for r in rows:
        if r["count"] >= THRESHOLD_BLOCK:
            status = "block"
            exit_code = 2
            break
        elif r["count"] >= THRESHOLD_WARN:
            status = "warn"
            exit_code = max(exit_code, 1)
    return {"status": status, "exit_code": exit_code, "repeats": rows}


def stats(days: int = 7) -> dict:
    _ensure_table()
    conn = sqlite3.connect(str(DB), timeout=_DB_TIMEOUT)
    cur = conn.execute(
        f"""SELECT path, COUNT(*) as total, COUNT(DISTINCT hunk_hash) as distinct_hunks
            FROM ping_pong_tracker
            WHERE ts > datetime('now', '-{days} days')
            GROUP BY path
            HAVING total >= {THRESHOLD_WARN}
            ORDER BY total DESC
            LIMIT 20"""
    )
    rows = [dict(zip(("path", "total", "distinct_hunks"), r)) for r in cur.fetchall()]
    conn.close()
    return {"days": days, "paths": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description="Anti-Ping-Pong detector")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_rec = sub.add_parser("record", help="수정 기록 (hook 에서 호출)")
    p_rec.add_argument("--file", required=True)
    p_rec.add_argument("--diff", default="")
    p_rec.add_argument("--goal", type=int, default=None)
    p_rec.add_argument("--session", default=None)

    p_chk = sub.add_parser("check", help="반복 감지")
    p_chk.add_argument("--file", default=None)
    p_chk.add_argument("--goal", type=int, default=None)

    p_st = sub.add_parser("stats", help="최근 N일 통계")
    p_st.add_argument("--days", type=int, default=7)

    args = ap.parse_args()
    try:
        if args.cmd == "record":
            n = record(args.file, args.diff, args.goal, args.session)
            print(json.dumps({"path": args.file, "count": n}, ensure_ascii=False))
            if n >= THRESHOLD_BLOCK:
                return 2
            if n >= THRESHOLD_WARN:
                return 1
            return 0
        elif args.cmd == "check":
            r = check(args.file, args.goal)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return r["exit_code"]
        elif args.cmd == "stats":
            r = stats(args.days)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
