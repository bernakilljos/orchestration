#!/usr/bin/env python3
"""
hook-profile.py ??SessionStart/SessionEnd ??hook ?ㅽ뻾 ?쒓컙 痢≪젙
1. 媛?hook ?ㅽ뻾 ?쒓컙 (ms) 湲곕줉
2. 500ms+ warning 쨌 5s+ systemMessage ?뚮┝
3. orca.db.hook_profile ?뚯씠釉붿뿉 ???
洹쇨굅: .claude/rules/auto-optimization.md
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ?섍꼍 蹂??湲곕컲 ?숈쟻 寃쎈줈
ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = ROOT / ".claude" / "logs"
DB = ROOT / ".claude" / "state" / "orca.db"
LOGS.mkdir(parents=True, exist_ok=True)

# 濡쒓퉭
LOG_FILE = LOGS / "hook-profile.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def ensure_table() -> None:
    """hook_profile ?뚯씠釉??앹꽦 (?덉쑝硫?skip)."""
    if not DB.exists():
        logger.warning("orca.db not found, skipping table creation")
        return

    try:
        with sqlite3.connect(str(DB)) as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS hook_profile (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  session_id TEXT,
                  hook_name TEXT NOT NULL,
                  duration_ms INTEGER NOT NULL,
                  status TEXT CHECK(status IN ('ok', 'warn', 'error')),
                  error_msg TEXT
                )
                """
            )
            c.commit()
        logger.info("hook_profile table ensured")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.error(f"failed to create table: {e}")


def record_hook(
    hook_name: str, duration_ms: int, session_id: Optional[str] = None, error_msg: Optional[str] = None
) -> None:
    """Hook ?ㅽ뻾 ?쒓컙 湲곕줉."""
    if not DB.exists():
        logger.warning("orca.db not found, skipping record")
        return

    # ?곹깭 ?먯젙
    if error_msg:
        status = "error"
    elif duration_ms >= 5000:
        status = "warn"
    else:
        status = "ok"

    try:
        with sqlite3.connect(str(DB)) as c:
            c.execute(
                """
                INSERT INTO hook_profile (session_id, hook_name, duration_ms, status, error_msg)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, hook_name, duration_ms, status, error_msg),
            )
            c.commit()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.error(f"failed to record hook {hook_name}: {e}")


def profile_hook(hook_name: str, hook_func, session_id: Optional[str] = None, *args, **kwargs) -> tuple:
    """Hook ?⑥닔 ?ㅽ뻾 ?쒓컙 痢≪젙 諛?湲곕줉."""
    start = time.time()
    error_msg = None
    result = None

    try:
        result = hook_func(*args, **kwargs)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        error_msg = str(e)
        logger.error(f"hook {hook_name} failed: {e}")

    duration_ms = int((time.time() - start) * 1000)

    # 湲곕줉
    record_hook(hook_name, duration_ms, session_id, error_msg)

    # 濡쒓렇 諛??뚮┝
    if duration_ms >= 5000:
        logger.warning(
            f"SLOW HOOK: {hook_name} ??{duration_ms}ms (threshold 5000ms)"
        )
    elif duration_ms >= 500:
        logger.info(f"hook {hook_name}: {duration_ms}ms")

    return result, duration_ms


def generate_report(hours: int = 24) -> dict:
    """理쒓렐 N?쒓컙 hook profile 由ы룷???앹꽦."""
    if not DB.exists():
        return {}

    try:
        with sqlite3.connect(str(DB)) as c:
            # 理쒓렐 24?쒓컙
            rows = c.execute(
                """
                SELECT hook_name, duration_ms, status, COUNT(*) as count, AVG(duration_ms) as avg_ms
                FROM hook_profile
                WHERE ts > datetime('now', '-' || ? || ' hours')
                GROUP BY hook_name, status
                ORDER BY avg_ms DESC
                """,
                (hours,),
            ).fetchall()

        report = {
            "generated": datetime.now().isoformat(),
            "period_hours": hours,
            "hooks": [],
        }

        for hook_name, duration_ms, status, count, avg_ms in rows:
            report["hooks"].append(
                {
                    "name": hook_name,
                    "count": count,
                    "avg_ms": round(avg_ms, 1),
                    "last_ms": duration_ms,
                    "status": status,
                }
            )

        return report
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.error(f"failed to generate report: {e}")
        return {}


def main(
    hook_name: str = "test-hook",
    duration_ms: int = 0,
    session_id: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """CLI ?뚯뒪??"""
    logger.info("=== hook-profile start ===")

    if dry_run:
        logger.info(f"[DRY] would record: {hook_name} = {duration_ms}ms")
        return 0

    # ?뚯씠釉??앹꽦
    ensure_table()

    # ?덉퐫??異붽?
    if duration_ms > 0:
        record_hook(hook_name, duration_ms, session_id)
        logger.info(f"recorded: {hook_name} = {duration_ms}ms")

    # 由ы룷??    report = generate_report(hours=24)
    if report:
        logger.info(f"recent report: {len(report.get('hooks', []))} hooks")
        print(json.dumps(report, indent=2))

    logger.info("=== done ===")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Profile hook execution times")
    parser.add_argument("--hook-name", default="test", help="Hook name to record")
    parser.add_argument("--duration-ms", type=int, default=0, help="Duration in ms")
    parser.add_argument("--session-id", default=None, help="Session ID (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no DB write)")
    parser.add_argument("--report", action="store_true", help="Generate report only")

    args = parser.parse_args()

    if args.report:
        ensure_table()
        report = generate_report(hours=24)
        print(json.dumps(report, indent=2))
        sys.exit(0)

    sys.exit(
        main(
            hook_name=args.hook_name,
            duration_ms=args.duration_ms,
            session_id=args.session_id,
            dry_run=args.dry_run,
        )
    )

