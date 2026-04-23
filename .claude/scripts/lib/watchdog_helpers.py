"""Helper functions for watchdog.py.

Provides database queries and worker spawning logic for the watchdog monitoring process.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
from state_db import (
    tx, get_all_registered_workers_raw, get_workers_by_status,
    register_worker, update_heartbeat
)
from backoff import compute_backoff


def get_all_registered_workers() -> List[Dict[str, Any]]:
    """Fetch all workers from database.

    Returns:
        List of worker dicts with keys: worker_id, ai_type, pid, status,
        quota_backoff_until, quota_retry_count, started_at, last_heartbeat
    """
    with tx() as conn:
        rows = conn.execute(
            "SELECT worker_id, ai_type, pid, status, quota_backoff_until, "
            "quota_retry_count, started_at, last_heartbeat FROM workers "
            "ORDER BY worker_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_workers_ready_to_revive() -> List[Dict[str, Any]]:
    """Get workers in quota_wait whose backoff period expired.

    Returns:
        List of workers ready for revive attempt
    """
    now = int(time.time())
    with tx() as conn:
        rows = conn.execute(
            "SELECT worker_id, ai_type, quota_retry_count, quota_backoff_until "
            "FROM workers WHERE status = 'quota_wait' "
            "AND quota_backoff_until IS NOT NULL AND quota_backoff_until <= ? "
            "ORDER BY worker_id",
            (now,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_dead_workers_to_retry() -> List[Dict[str, Any]]:
    """Get dead workers (non-quota failures) that haven't exceeded retry limit.

    Returns:
        List of dead workers with retry_count < 3
    """
    with tx() as conn:
        rows = conn.execute(
            "SELECT worker_id, ai_type, quota_retry_count FROM workers "
            "WHERE status = 'dead' AND quota_retry_count < 3 "
            "ORDER BY worker_id"
        ).fetchall()
    return [dict(row) for row in rows]


def spawn_worker(ai_type: str, worker_id: str, dry_run: bool = False) -> bool:
    """Spawn a worker process for the given AI type.

    Maps ai_type to corresponding executable and extracts child number from worker_id.

    Args:
        ai_type: One of 'codex', 'gemini', 'haiku', 'claude'
        worker_id: Identifier like 'codex-1', 'gemini-2'
        dry_run: If True, print command but don't execute

    Returns:
        True if spawn succeeded (or dry_run), False if error
    """
    # Extract child number from worker_id (e.g., "codex-3" -> "3")
    parts = worker_id.split('-')
    if len(parts) != 2 or not parts[1].isdigit():
        return False

    child_num = parts[1]

    # Map AI type to command
    cmd_map = {
        'codex': f'codex-auto --child {child_num}',
        'gemini': f'gemini-auto --child {child_num}',
        'haiku': f'haiku-auto --child {child_num}',
        'claude': f'claude-auto --child {child_num}',
    }

    if ai_type not in cmd_map:
        return False

    cmd = cmd_map[ai_type]

    if dry_run:
        print(f"[DRY-RUN] Would spawn: {cmd}")
        return True

    try:
        # Windows: use start /min cmd /c to launch in background
        full_cmd = f'start /min cmd /c "{cmd}"'
        subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000  # CREATE_NO_WINDOW on Windows
        )
        return True
    except Exception:
        return False


def extend_quota_backoff(worker_id: str, retry_count: int) -> int:
    """Extend quota backoff with exponential increase.

    Computes new backoff based on retry_count and updates worker in DB.

    Args:
        worker_id: The worker to update
        retry_count: Current quota_retry_count

    Returns:
        New backoff duration in seconds
    """
    new_backoff = compute_backoff(retry_count)

    with tx() as conn:
        conn.execute(
            "UPDATE workers SET quota_backoff_until = ? WHERE worker_id = ?",
            (int(time.time()) + new_backoff, worker_id)
        )

    return new_backoff


def update_worker_status(worker_id: str, status: str) -> None:
    """Update worker status in DB.

    Args:
        worker_id: Worker identifier
        status: One of 'idle', 'running', 'dead', 'quota_wait'
    """
    with tx() as conn:
        conn.execute(
            "UPDATE workers SET status = ? WHERE worker_id = ?",
            (status, worker_id)
        )


def mark_worker_as_revived(worker_id: str) -> None:
    """Mark worker status as idle after revive attempt.

    Resets quota_backoff_until to NULL and status to 'idle'.
    """
    with tx() as conn:
        conn.execute(
            "UPDATE workers SET status = 'idle', quota_backoff_until = NULL WHERE worker_id = ?",
            (worker_id,)
        )
