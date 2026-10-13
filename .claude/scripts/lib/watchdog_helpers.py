"""Helper functions for watchdog.py.

Provides database queries and worker spawning logic for the watchdog monitoring process.
"""

import csv
import io
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from state_db import (
    tx, get_all_registered_workers_raw, get_workers_by_status,
    register_worker, update_heartbeat
)
from backoff import compute_backoff

# Optional psutil — fallback to OS tools if missing
try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


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


# --- Memory / lifetime monitoring ---------------------------------

def _get_rss_via_psutil(pid: int) -> Optional[int]:
    """Return RSS in MB via psutil, None if pid dead/inaccessible."""
    try:
        p = psutil.Process(pid)
        rss_bytes = p.memory_info().rss
        # Add child processes (Claude/Codex CLI spawns Node/Python children)
        try:
            for child in p.children(recursive=True):
                rss_bytes += child.memory_info().rss
        except psutil.Error:
            pass
        return rss_bytes // (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
        return None


def _get_rss_via_tasklist(pid: int) -> Optional[int]:
    """Windows fallback: parse `tasklist /FI` output for RSS in MB."""
    if platform.system() != "Windows":
        return None
    try:
        # /NH = no header, /FO CSV for stable parsing
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="ignore").strip()
        if not out or "No tasks" in out:
            return None
        # Use csv.reader — mem column "14,516 K" contains a comma inside quotes
        row = next(csv.reader(io.StringIO(out)), None)
        if not row or len(row) < 5:
            return None
        mem_str = row[4].replace(" K", "").replace(",", "").strip()
        if not mem_str.isdigit():
            return None
        return int(mem_str) // 1024
    except (subprocess.SubprocessError, OSError, ValueError):
        return None


def _get_rss_via_ps(pid: int) -> Optional[int]:
    """Unix fallback: `ps -o rss=` returns KB."""
    if platform.system() == "Windows":
        return None
    try:
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(pid)],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="ignore").strip()
        if not out.isdigit():
            return None
        return int(out) // 1024
    except (subprocess.SubprocessError, OSError, ValueError):
        return None


def get_worker_rss_mb(pid: int) -> Optional[int]:
    """Return resident memory (MB) of pid + descendants. None if pid dead.

    Order: psutil -> tasklist (Windows) -> ps (Unix).
    """
    if not pid or pid <= 0:
        return None
    if _HAS_PSUTIL:
        rss = _get_rss_via_psutil(pid)
        if rss is not None:
            return rss
    return _get_rss_via_tasklist(pid) or _get_rss_via_ps(pid)


def get_worker_uptime_sec(worker: Dict[str, Any]) -> int:
    """Uptime in seconds since started_at."""
    return int(time.time()) - int(worker.get("started_at") or 0)


def should_restart_worker(
    worker: Dict[str, Any],
    max_rss_mb: int,
    max_uptime_sec: int,
) -> Optional[str]:
    """Return reason string if worker should be restarted, else None.

    Only restarts workers in idle/running status (not dead, not quota_wait).
    """
    if worker.get("status") not in ("idle", "running"):
        return None

    pid = worker.get("pid")
    if not pid:
        return None

    uptime = get_worker_uptime_sec(worker)
    if uptime >= max_uptime_sec:
        return f"max_uptime exceeded ({uptime}s >= {max_uptime_sec}s)"

    rss = get_worker_rss_mb(pid)
    if rss is None:
        # Pid is dead but DB says alive -> let detect_dead_workers handle via heartbeat
        return None
    if rss >= max_rss_mb:
        return f"max_rss exceeded ({rss}MB >= {max_rss_mb}MB)"

    return None


def kill_worker_tree(pid: int, dry_run: bool = False) -> bool:
    """Kill pid + all descendants. Returns True on success."""
    if not pid or pid <= 0:
        return False
    if dry_run:
        return True

    if _HAS_PSUTIL:
        try:
            p = psutil.Process(pid)
            children = []
            try:
                children = p.children(recursive=True)
            except psutil.Error:
                pass
            for child in children:
                try:
                    child.terminate()
                except psutil.Error:
                    pass
            try:
                p.terminate()
            except psutil.Error:
                pass
            # Wait briefly then force-kill stragglers
            gone, alive = psutil.wait_procs([p] + children, timeout=3)
            for proc in alive:
                try:
                    proc.kill()
                except psutil.Error:
                    pass
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    # No psutil: OS-level tree kill
    try:
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        else:
            # Send SIGTERM to process group, then SIGKILL after grace
            try:
                os.killpg(os.getpgid(pid), 15)  # SIGTERM
                time.sleep(2)
                os.killpg(os.getpgid(pid), 9)   # SIGKILL
            except (ProcessLookupError, PermissionError):
                pass
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def get_running_workers() -> List[Dict[str, Any]]:
    """All workers with pid set and status in (idle, running)."""
    with tx() as conn:
        rows = conn.execute(
            "SELECT worker_id, ai_type, pid, status, started_at, last_heartbeat "
            "FROM workers WHERE pid IS NOT NULL AND status IN ('idle','running') "
            "ORDER BY worker_id"
        ).fetchall()
    return [dict(r) for r in rows]


def mark_worker_restart(worker_id: str, reason: str) -> None:
    """Set worker status to 'restarting' with reason note in DB."""
    now = int(time.time())
    with tx() as conn:
        conn.execute(
            "UPDATE workers SET status = 'dead', last_heartbeat = ? WHERE worker_id = ?",
            (now, worker_id),
        )
