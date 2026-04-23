"""SQLite state management library for orchestration_v1 kit.

Provides atomic transaction handling, worker tracking, task locking, metrics,
and quota management via WAL-enabled SQLite.
"""

import sqlite3
import os
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, List, Any
import threading

# Thread-local lock to prevent concurrent DB access issues on Windows
_db_lock = threading.Lock()


def get_db_path() -> Path:
  """Return path to orca.db, creating .claude/state if needed."""
  project_root = _get_project_root()
  state_dir = project_root / ".claude" / "state"
  state_dir.mkdir(parents=True, exist_ok=True)
  return state_dir / "orca.db"


def _get_project_root() -> Path:
  """Get project root from env or by walking up from script location."""
  if "ORCHESTRATION_ROOT" in os.environ:
    return Path(os.environ["ORCHESTRATION_ROOT"])
  # Walk up from .claude/scripts/lib/state_db.py
  current = Path(__file__).parent
  while current != current.parent:
    if (current / ".claude" / "scripts").exists():
      return current
    current = current.parent
  # Fallback
  return Path.cwd()


def get_db() -> sqlite3.Connection:
  """Open connection to orca.db with WAL and busy timeout."""
  db_path = get_db_path()
  conn = sqlite3.connect(str(db_path), timeout=30.0)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA synchronous=NORMAL")
  conn.execute("PRAGMA busy_timeout=5000")
  return conn


@contextmanager
def tx():
  """Context manager for atomic transactions with IMMEDIATE locking."""
  with _db_lock:
    conn = get_db()
    try:
      conn.execute("BEGIN IMMEDIATE")
      yield conn
      conn.commit()
    except Exception as e:
      conn.rollback()
      raise
    finally:
      conn.close()


def init_schema() -> None:
  """Initialize database schema if missing. Idempotent."""
  with tx() as conn:
    # Check schema version
    try:
      cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
      if cur.fetchone():
        return  # Already initialized
    except sqlite3.OperationalError:
      pass

    # Create tables
    conn.executescript("""
      CREATE TABLE IF NOT EXISTS workers (
        worker_id TEXT PRIMARY KEY,
        ai_type TEXT NOT NULL,
        pid INTEGER,
        started_at INTEGER NOT NULL,
        last_heartbeat INTEGER NOT NULL,
        status TEXT NOT NULL,
        quota_backoff_until INTEGER,
        quota_retry_count INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        task_file TEXT NOT NULL,
        ai_assigned TEXT,
        worker_id TEXT,
        status TEXT NOT NULL,
        locked_at INTEGER,
        locked_until INTEGER,
        created_at INTEGER NOT NULL,
        completed_at INTEGER,
        retry_count INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        ai TEXT NOT NULL,
        model_id TEXT,
        tokens_in INTEGER NOT NULL DEFAULT 0,
        tokens_out INTEGER NOT NULL DEFAULT 0,
        cost_usd REAL,
        latency_ms INTEGER NOT NULL,
        success INTEGER NOT NULL,
        cache_hit INTEGER DEFAULT 0,
        retry INTEGER DEFAULT 0,
        recorded_at INTEGER NOT NULL,
        error_class TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_metrics_recorded
        ON metrics(recorded_at);
      CREATE INDEX IF NOT EXISTS idx_metrics_ai
        ON metrics(ai);
      CREATE INDEX IF NOT EXISTS idx_metrics_task_id
        ON metrics(task_id);

      CREATE TABLE IF NOT EXISTS quota (
        ai TEXT PRIMARY KEY,
        exceeded INTEGER NOT NULL DEFAULT 0,
        exceeded_since INTEGER,
        expires_at INTEGER,
        last_error TEXT,
        updated_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY DEFAULT 1,
        daily_limit_usd REAL,
        today_spent_usd REAL DEFAULT 0,
        today_date TEXT NOT NULL,
        breaker_tripped INTEGER DEFAULT 0,
        breaker_tripped_at INTEGER,
        updated_at INTEGER NOT NULL,
        CHECK (id = 1)
      );

      CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY DEFAULT 1,
        orca_enabled INTEGER DEFAULT 1,
        orca_stopped_reason TEXT,
        claude_heartbeat INTEGER NOT NULL,
        CHECK (id = 1)
      );

      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at INTEGER
      );
    """)

    # Insert initial records
    now = int(time.time())
    today = time.strftime("%Y-%m-%d", time.gmtime(now))

    conn.execute(
      "INSERT OR IGNORE INTO budget (id, today_spent_usd, today_date, updated_at) "
      "VALUES (1, 0, ?, ?)",
      (today, now)
    )
    conn.execute(
      "INSERT OR IGNORE INTO session (id, orca_enabled, claude_heartbeat) "
      "VALUES (1, 1, ?)",
      (now,)
    )
    conn.execute(
      "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, ?)",
      (now,)
    )


# Worker management
def register_worker(worker_id: str, ai_type: str, pid: int) -> None:
  """Register or update worker. Creates entry if missing."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT OR REPLACE INTO workers "
      "(worker_id, ai_type, pid, started_at, last_heartbeat, status) "
      "VALUES (?, ?, ?, ?, ?, 'idle')",
      (worker_id, ai_type, pid, now, now)
    )


def update_heartbeat(worker_id: str) -> None:
  """Update worker's last_heartbeat timestamp."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET last_heartbeat = ? WHERE worker_id = ?",
      (now, worker_id)
    )


def mark_worker_dead(worker_id: str, reason: str = None) -> None:
  """Mark worker as dead."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET status = 'dead', last_heartbeat = ? "
      "WHERE worker_id = ?",
      (now, worker_id)
    )


def get_live_workers(max_age_sec: int = 300) -> List[Dict[str, Any]]:
  """Return list of workers with recent heartbeat."""
  now = int(time.time())
  cutoff = now - max_age_sec
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status FROM workers "
      "WHERE last_heartbeat >= ? AND status != 'dead' "
      "ORDER BY worker_id",
      (cutoff,)
    ).fetchall()
  return [dict(row) for row in rows]


def set_worker_quota_wait(worker_id: str, backoff_sec: int) -> None:
  """Set worker quota backoff until timestamp."""
  until = int(time.time()) + backoff_sec
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET quota_backoff_until = ?, quota_retry_count = quota_retry_count + 1 "
      "WHERE worker_id = ?",
      (until, worker_id)
    )


# Task + lock management
def try_lock_task(task_id: str, task_file: str, worker_id: str, ttl_sec: int = 1800) -> bool:
  """Atomically lock task for worker. Returns True if successful."""
  now = int(time.time())
  locked_until = now + ttl_sec
  with tx() as conn:
    # Check if already locked by someone else
    row = conn.execute(
      "SELECT worker_id, locked_until FROM tasks WHERE task_id = ?",
      (task_id,)
    ).fetchone()

    if row:
      if row["worker_id"] and row["locked_until"] and row["locked_until"] > now:
        return False  # Already locked by another worker
      # Stale lock, take over
      conn.execute(
        "UPDATE tasks SET worker_id = ?, locked_at = ?, locked_until = ?, status = 'locked' "
        "WHERE task_id = ?",
        (worker_id, now, locked_until, task_id)
      )
      return True

    # New task, insert lock
    conn.execute(
      "INSERT INTO tasks "
      "(task_id, task_file, ai_assigned, worker_id, status, locked_at, locked_until, created_at) "
      "VALUES (?, ?, NULL, ?, 'locked', ?, ?, ?)",
      (task_id, task_file, worker_id, now, locked_until, now)
    )
  return True


def release_task_lock(task_id: str, final_status: str) -> None:
  """Release task lock and set final status."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE tasks SET status = ?, worker_id = NULL, locked_at = NULL, "
      "locked_until = NULL, completed_at = ? WHERE task_id = ?",
      (final_status, now, task_id)
    )


def expire_stale_locks() -> int:
  """Free locks that exceed TTL. Returns count freed."""
  now = int(time.time())
  with tx() as conn:
    cur = conn.execute(
      "UPDATE tasks SET worker_id = NULL, status = 'pending' "
      "WHERE locked_until IS NOT NULL AND locked_until < ? AND status = 'locked'",
      (now,)
    )
  return cur.rowcount


# Metrics
def record_metric(
  ai: str,
  model_id: str,
  tokens_in: int,
  tokens_out: int,
  cost_usd: Optional[float],
  latency_ms: int,
  success: bool,
  task_id: Optional[str] = None,
  cache_hit: bool = False,
  error_class: Optional[str] = None,
) -> None:
  """Record API call metric."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT INTO metrics "
      "(task_id, ai, model_id, tokens_in, tokens_out, cost_usd, latency_ms, "
      "success, cache_hit, recorded_at, error_class) "
      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      (task_id, ai, model_id, tokens_in, tokens_out, cost_usd, latency_ms,
       1 if success else 0, 1 if cache_hit else 0, now, error_class)
    )


def get_metrics_summary(hours: int = 24) -> Dict[str, Any]:
  """Return aggregated metrics for last N hours."""
  since = int(time.time()) - (hours * 3600)
  with tx() as conn:
    rows = conn.execute(
      "SELECT ai, COUNT(*) as count, SUM(success) as successes, "
      "SUM(tokens_in) as total_tokens_in, SUM(tokens_out) as total_tokens_out, "
      "SUM(cost_usd) as total_cost, AVG(latency_ms) as avg_latency, "
      "SUM(cache_hit) as cache_hits "
      "FROM metrics WHERE recorded_at >= ? GROUP BY ai ORDER BY ai",
      (since,)
    ).fetchall()

  summary = {}
  for row in rows:
    ai = row["ai"]
    summary[ai] = {
      "count": row["count"],
      "success_rate": (row["successes"] or 0) / (row["count"] or 1),
      "tokens_in": row["total_tokens_in"] or 0,
      "tokens_out": row["total_tokens_out"] or 0,
      "total_cost_usd": row["total_cost"] or 0.0,
      "avg_latency_ms": row["avg_latency"] or 0,
      "cache_hits": row["cache_hits"] or 0,
    }
  return summary


# Quota management
def set_quota_exceeded(ai: str, expires_at: int, error_msg: str) -> None:
  """Mark AI as quota-exceeded until expires_at."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT OR REPLACE INTO quota "
      "(ai, exceeded, exceeded_since, expires_at, last_error, updated_at) "
      "VALUES (?, 1, ?, ?, ?, ?)",
      (ai, now, expires_at, error_msg, now)
    )


def is_quota_exceeded(ai: str) -> bool:
  """Check if AI is quota-exceeded. Auto-clears if expired."""
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT exceeded, expires_at FROM quota WHERE ai = ?",
      (ai,)
    ).fetchone()

    if not row:
      return False

    if row["exceeded"] == 0:
      return False

    if row["expires_at"] and row["expires_at"] < now:
      # Expired, clear it
      conn.execute("UPDATE quota SET exceeded = 0, expires_at = NULL WHERE ai = ?", (ai,))
      return False

  return True


def clear_quota(ai: str) -> None:
  """Manually clear quota exceeded flag."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE quota SET exceeded = 0, expires_at = NULL, updated_at = ? WHERE ai = ?",
      (now, ai)
    )


# Budget management
def add_spend(cost_usd: float) -> float:
  """Add to today's spend, return new total."""
  check_daily_rollover()
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET today_spent_usd = today_spent_usd + ? WHERE id = 1",
      (cost_usd,)
    )
    row = conn.execute(
      "SELECT today_spent_usd FROM budget WHERE id = 1"
    ).fetchone()
  return row["today_spent_usd"] if row else cost_usd


def is_breaker_tripped() -> bool:
  """Check if budget breaker is tripped."""
  with tx() as conn:
    row = conn.execute(
      "SELECT breaker_tripped, daily_limit_usd FROM budget WHERE id = 1"
    ).fetchone()
  if not row:
    return False
  return row["breaker_tripped"] == 1


def trip_breaker(reason: str = None) -> None:
  """Manually trip the budget breaker."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET breaker_tripped = 1, breaker_tripped_at = ? WHERE id = 1",
      (now,)
    )


def reset_breaker() -> None:
  """Reset the budget breaker."""
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET breaker_tripped = 0, breaker_tripped_at = NULL WHERE id = 1"
    )


def check_daily_rollover() -> None:
  """Reset today_spent_usd if date changed."""
  today = time.strftime("%Y-%m-%d", time.gmtime(int(time.time())))
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT today_date FROM budget WHERE id = 1"
    ).fetchone()
    if row and row["today_date"] != today:
      conn.execute(
        "UPDATE budget SET today_spent_usd = 0, today_date = ?, updated_at = ? WHERE id = 1",
        (today, now)
      )


# Session management
def update_claude_heartbeat() -> None:
  """Update Claude Code session heartbeat."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE session SET claude_heartbeat = ? WHERE id = 1",
      (now,)
    )


def is_claude_alive(max_age_sec: int = 300) -> bool:
  """Check if Claude Code session is alive."""
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT claude_heartbeat FROM session WHERE id = 1"
    ).fetchone()
  if not row:
    return False
  return (now - row["claude_heartbeat"]) <= max_age_sec


def set_orca_enabled(enabled: bool, reason: str = None) -> None:
  """Set orca enabled/disabled state."""
  now = int(time.time())
  reason_text = reason if reason else ("enabled" if enabled else "stopped")
  with tx() as conn:
    conn.execute(
      "UPDATE session SET orca_enabled = ?, orca_stopped_reason = ? WHERE id = 1",
      (1 if enabled else 0, reason_text if not enabled else None)
    )


def get_all_registered_workers_raw() -> List[Dict[str, Any]]:
  """Return all workers from database (no filtering)."""
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status, quota_backoff_until, "
      "quota_retry_count, started_at, last_heartbeat FROM workers "
      "ORDER BY worker_id"
    ).fetchall()
  return [dict(row) for row in rows]


def get_workers_by_status(status: str) -> List[Dict[str, Any]]:
  """Return workers with a specific status."""
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status, quota_retry_count "
      "FROM workers WHERE status = ? ORDER BY worker_id",
      (status,)
    ).fetchall()
  return [dict(row) for row in rows]
