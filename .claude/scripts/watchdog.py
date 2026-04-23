#!/usr/bin/env python3
"""Watchdog process for orchestration_v1 — monitors and revives dead workers.

Runs as a background process, checking every 2 minutes for:
1. Stale worker heartbeats (>5 min old) → mark dead
2. Quota-blocked workers whose backoff expired → retry with exponential delay
3. Dead workers → restart (max 3 retries)
4. Claude Code session alive → if dead, shutdown watchdog

Quota-aware: if quota still exceeded, extends backoff exponentially instead of restarting.

Usage:
    python watchdog.py                # Run watchdog loop (infinite)
    python watchdog.py --test         # Run once and exit
    python watchdog.py --dry-run      # Print actions but don't execute
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Setup path for lib imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from state_db import (
    init_schema, get_live_workers, is_claude_alive, set_orca_enabled,
    is_quota_exceeded, tx
)
from watchdog_helpers import (
    get_all_registered_workers, get_workers_ready_to_revive,
    get_dead_workers_to_retry, spawn_worker, extend_quota_backoff,
    update_worker_status, mark_worker_as_revived
)
from backoff import format_duration


class WatchdogLogger:
    """Simple JSON line logger for watchdog events."""

    def __init__(self, log_path: Path):
        """Initialize logger with log file path."""
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level: str, msg: str, extra: Dict[str, Any] = None) -> None:
        """Write JSON line to log.

        Args:
            level: 'info', 'warn', 'error'
            msg: Log message
            extra: Optional dict of additional fields
        """
        entry = {
            "ts": int(time.time()),
            "level": level,
            "msg": msg,
        }
        if extra:
            entry.update(extra)

        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def rotate_if_needed(self, max_size_mb: int = 10) -> None:
        """Rotate log if larger than max_size_mb."""
        try:
            if self.log_path.exists():
                size_mb = self.log_path.stat().st_size / (1024 * 1024)
                if size_mb > max_size_mb:
                    backup = self.log_path.parent / f"{self.log_path.name}.1"
                    self.log_path.rename(backup)
        except Exception:
            pass


def get_project_root() -> Path:
    """Detect project root from script location."""
    if "ORCHESTRATION_ROOT" in os.environ:
        return Path(os.environ["ORCHESTRATION_ROOT"])

    # Walk up from .claude/scripts/watchdog.py
    current = Path(__file__).parent
    while current != current.parent:
        if (current / ".claude" / "scripts").exists():
            return current
        current = current.parent

    return Path.cwd()


def check_orca_enabled(project_root: Path) -> bool:
    """Check if orca is enabled via .claude/orca-enabled flag or DB."""
    # Check legacy file flag
    if (project_root / ".claude" / "orca-stopped").exists():
        return False

    # Check DB state
    from state_db import tx
    with tx() as conn:
        row = conn.execute(
            "SELECT orca_enabled FROM session WHERE id = 1"
        ).fetchone()
        if row:
            return row["orca_enabled"] == 1

    return True


def detect_dead_workers(logger: WatchdogLogger, max_age_sec: int = 300) -> None:
    """Find workers with stale heartbeats and mark them dead.

    Args:
        logger: WatchdogLogger instance
        max_age_sec: Heartbeat older than this = dead (default 5 min)
    """
    now = int(time.time())
    live_ids = {w["worker_id"] for w in get_live_workers(max_age_sec=max_age_sec)}
    all_workers = get_all_registered_workers()

    for w in all_workers:
        if w["worker_id"] not in live_ids and w["status"] != "quota_wait":
            last_hb_ago = now - w["last_heartbeat"]
            update_worker_status(w["worker_id"], "dead")
            logger.log(
                "warn",
                f"Worker marked dead (heartbeat {last_hb_ago}s old)",
                {"worker_id": w["worker_id"], "ai_type": w["ai_type"]},
            )


def revive_quota_blocked_workers(logger: WatchdogLogger, dry_run: bool = False) -> None:
    """Attempt to revive workers waiting for quota recovery.

    For each quota_wait worker whose backoff expired:
    - If quota still exceeded: extend backoff exponentially (cap 2h)
    - If quota recovered: spawn worker

    Args:
        logger: WatchdogLogger instance
        dry_run: If True, don't actually spawn
    """
    for w in get_workers_ready_to_revive():
        worker_id = w["worker_id"]
        ai_type = w["ai_type"]
        retry_count = w["quota_retry_count"]

        if is_quota_exceeded(ai_type):
            # Quota still exceeded — extend backoff
            new_backoff = extend_quota_backoff(worker_id, retry_count)
            logger.log(
                "info",
                f"Quota still exceeded for {ai_type}, extending backoff to {format_duration(new_backoff)}",
                {"worker_id": worker_id, "retry_count": retry_count},
            )
        else:
            # Quota recovered — revive worker
            success = spawn_worker(ai_type, worker_id, dry_run=dry_run)
            if success:
                mark_worker_as_revived(worker_id)
                logger.log(
                    "info",
                    f"Revived quota-blocked worker {worker_id}",
                    {"ai_type": ai_type},
                )
            else:
                logger.log(
                    "error",
                    f"Failed to revive worker {worker_id}",
                    {"ai_type": ai_type},
                )


def revive_dead_workers(logger: WatchdogLogger, dry_run: bool = False) -> None:
    """Restart dead workers that haven't exceeded retry limit.

    For each dead worker with quota_retry_count < 3:
    - Spawn worker
    - Update status to idle

    Args:
        logger: WatchdogLogger instance
        dry_run: If True, don't actually spawn
    """
    for w in get_dead_workers_to_retry():
        worker_id = w["worker_id"]
        ai_type = w["ai_type"]
        retry_count = w["quota_retry_count"]

        success = spawn_worker(ai_type, worker_id, dry_run=dry_run)
        if success:
            mark_worker_as_revived(worker_id)
            logger.log(
                "info",
                f"Restarted dead worker {worker_id} (attempt {retry_count + 1}/3)",
                {"ai_type": ai_type},
            )
        else:
            logger.log(
                "error",
                f"Failed to restart worker {worker_id}",
                {"ai_type": ai_type, "attempt": retry_count + 1},
            )


def run_once(project_root: Path, logger: WatchdogLogger, dry_run: bool = False) -> None:
    """Run watchdog checks once.

    Args:
        project_root: Root of orchestration_v1 project
        logger: WatchdogLogger instance
        dry_run: If True, don't spawn workers
    """
    # 1. Check Claude Code alive
    if not is_claude_alive(max_age_sec=300):
        logger.log("info", "Claude Code session dead. Shutting down watchdog.")
        set_orca_enabled(False, reason="claude session dead")
        return

    # 2. Check orca enabled
    if not check_orca_enabled(project_root):
        return  # Silently idle if disabled

    # 3. Detect dead workers
    detect_dead_workers(logger)

    # 4. Revive quota-blocked workers
    revive_quota_blocked_workers(logger, dry_run=dry_run)

    # 5. Revive other dead workers
    revive_dead_workers(logger, dry_run=dry_run)

    logger.log("info", "Watchdog cycle complete")


def run_loop(project_root: Path, logger: WatchdogLogger, check_interval_sec: int = 120) -> None:
    """Run infinite watchdog loop.

    Sleeps check_interval_sec between iterations.

    Args:
        project_root: Root of orchestration_v1 project
        logger: WatchdogLogger instance
        check_interval_sec: Sleep duration between checks (default 2 min)
    """
    logger.log("info", "Watchdog started")

    try:
        while True:
            logger.rotate_if_needed(max_size_mb=10)
            run_once(project_root, logger, dry_run=False)
            time.sleep(check_interval_sec)
    except KeyboardInterrupt:
        logger.log("info", "Watchdog interrupted by user")
    except Exception as e:
        logger.log("error", f"Watchdog fatal error: {e}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Watchdog monitor for orchestration_v1 workers"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run once and exit (test mode)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print actions but don't execute"
    )
    parser.add_argument(
        "--interval", type=int, default=120, help="Check interval in seconds"
    )

    args = parser.parse_args()

    # Initialize
    project_root = get_project_root()
    log_path = project_root / ".claude" / "state" / "watchdog.log"
    logger = WatchdogLogger(log_path)

    # Ensure DB schema exists
    try:
        init_schema()
    except Exception as e:
        logger.log("error", f"Failed to initialize schema: {e}")
        return 1

    # Run test mode or loop
    if args.test:
        run_once(project_root, logger, dry_run=args.dry_run)
        print("[OK] Test run complete")
        return 0
    else:
        run_loop(project_root, logger, check_interval_sec=args.interval)
        return 0


if __name__ == "__main__":
    sys.exit(main())
