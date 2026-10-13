#!/usr/bin/env python3
"""Watchdog process for orchestration_v1 — monitors and revives dead workers.

Runs as a background process, checking every 2 minutes for:
1. Stale worker heartbeats (>5 min old) -> mark dead
2. Quota-blocked workers whose backoff expired -> retry with exponential delay
3. Dead workers -> restart (max 3 retries)
4. Claude Code session alive -> if dead, shutdown watchdog

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
    update_worker_status, mark_worker_as_revived,
    get_running_workers, should_restart_worker, kill_worker_tree,
    mark_worker_restart, get_worker_rss_mb,
)
from backoff import format_duration


# Default policy — overridable via CLI flags or env vars
DEFAULT_MAX_RSS_MB = int(os.environ.get("WATCHDOG_MAX_RSS_MB", "2048"))
DEFAULT_MAX_UPTIME_HOURS = int(os.environ.get("WATCHDOG_MAX_UPTIME_HOURS", "6"))
LOG_BACKUP_COUNT = 5


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

    def rotate_if_needed(self, max_size_mb: int = 10, backup_count: int = LOG_BACKUP_COUNT) -> None:
        """Rotate log if > max_size_mb, keeping `backup_count` historical backups.

        Naming: watchdog.log.1 (newest) ... watchdog.log.N (oldest, deleted on next rotate).
        """
        try:
            if not self.log_path.exists():
                return
            size_mb = self.log_path.stat().st_size / (1024 * 1024)
            if size_mb <= max_size_mb:
                return

            base = self.log_path
            # Shift .N -> .(N+1), dropping the oldest
            for i in range(backup_count, 0, -1):
                src = base.parent / f"{base.name}.{i}"
                if not src.exists():
                    continue
                if i == backup_count:
                    src.unlink()
                else:
                    dst = base.parent / f"{base.name}.{i+1}"
                    src.rename(dst)
            base.rename(base.parent / f"{base.name}.1")
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


def enforce_worker_limits(
    logger: WatchdogLogger,
    max_rss_mb: int,
    max_uptime_sec: int,
    dry_run: bool = False,
) -> None:
    """Restart workers exceeding memory or lifetime limits.

    For each running worker:
    - RSS (incl. child processes) >= max_rss_mb -> kill tree + respawn
    - Uptime >= max_uptime_sec -> kill tree + respawn (preempts memory leak)
    """
    for w in get_running_workers():
        reason = should_restart_worker(w, max_rss_mb, max_uptime_sec)
        if not reason:
            continue

        worker_id = w["worker_id"]
        ai_type = w["ai_type"]
        pid = w.get("pid")
        rss = get_worker_rss_mb(pid) if pid else None

        if dry_run:
            logger.log(
                "info",
                f"[DRY-RUN] Would restart {worker_id}: {reason}",
                {"ai_type": ai_type, "pid": pid, "rss_mb": rss},
            )
            continue

        killed = kill_worker_tree(pid) if pid else False
        mark_worker_restart(worker_id, reason)
        spawned = spawn_worker(ai_type, worker_id, dry_run=False)
        if spawned:
            mark_worker_as_revived(worker_id)
        logger.log(
            "warn",
            f"Restarted {worker_id} ({reason})",
            {
                "ai_type": ai_type,
                "pid_killed": pid,
                "rss_mb_before": rss,
                "kill_success": killed,
                "respawn_success": spawned,
            },
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


def run_once(
    project_root: Path,
    logger: WatchdogLogger,
    dry_run: bool = False,
    max_rss_mb: int = DEFAULT_MAX_RSS_MB,
    max_uptime_sec: int = DEFAULT_MAX_UPTIME_HOURS * 3600,
) -> None:
    """Run watchdog checks once.

    Args:
        project_root: Root of orchestration_v1 project
        logger: WatchdogLogger instance
        dry_run: If True, don't spawn workers
        max_rss_mb: RSS threshold per worker (incl. children)
        max_uptime_sec: Worker max uptime before forced restart
    """
    # 1. Claude session liveness — log only, never auto-shutdown watchdog.
    #    Workers must outlive the IDE session; explicit stop is via /orcauto-stop.
    if not is_claude_alive(max_age_sec=300):
        logger.log("info", "Claude session heartbeat stale (>5min) — keeping workers alive")

    # 2. Check orca enabled (explicit stop flag honored)
    if not check_orca_enabled(project_root):
        return  # Silently idle if disabled

    # 3. Detect dead workers (stale heartbeat)
    detect_dead_workers(logger)

    # 4. Revive quota-blocked workers
    revive_quota_blocked_workers(logger, dry_run=dry_run)

    # 5. Revive other dead workers
    revive_dead_workers(logger, dry_run=dry_run)

    # 6. Enforce RSS / uptime limits (memory-leak guard)
    enforce_worker_limits(
        logger,
        max_rss_mb=max_rss_mb,
        max_uptime_sec=max_uptime_sec,
        dry_run=dry_run,
    )

    logger.log("info", "Watchdog cycle complete")


def run_loop(
    project_root: Path,
    logger: WatchdogLogger,
    check_interval_sec: int = 120,
    max_rss_mb: int = DEFAULT_MAX_RSS_MB,
    max_uptime_sec: int = DEFAULT_MAX_UPTIME_HOURS * 3600,
) -> None:
    """Run infinite watchdog loop.

    Sleeps check_interval_sec between iterations.
    """
    logger.log(
        "info",
        "Watchdog started",
        {"max_rss_mb": max_rss_mb, "max_uptime_sec": max_uptime_sec, "interval": check_interval_sec},
    )

    try:
        while True:
            logger.rotate_if_needed(max_size_mb=10)
            run_once(
                project_root, logger, dry_run=False,
                max_rss_mb=max_rss_mb, max_uptime_sec=max_uptime_sec,
            )
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
    parser.add_argument(
        "--max-rss-mb", type=int, default=DEFAULT_MAX_RSS_MB,
        help=f"Worker RSS+children threshold in MB (default {DEFAULT_MAX_RSS_MB})",
    )
    parser.add_argument(
        "--max-uptime-hours", type=int, default=DEFAULT_MAX_UPTIME_HOURS,
        help=f"Worker max uptime in hours (default {DEFAULT_MAX_UPTIME_HOURS})",
    )

    args = parser.parse_args()
    max_uptime_sec = args.max_uptime_hours * 3600

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
        run_once(
            project_root, logger, dry_run=args.dry_run,
            max_rss_mb=args.max_rss_mb, max_uptime_sec=max_uptime_sec,
        )
        print("[OK] Test run complete")
        return 0
    else:
        run_loop(
            project_root, logger, check_interval_sec=args.interval,
            max_rss_mb=args.max_rss_mb, max_uptime_sec=max_uptime_sec,
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
