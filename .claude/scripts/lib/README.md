# State DB Library

SQLite-based state management for orchestration_v1 kit. Replaces legacy file-flag system with atomic transactions, WAL mode, and 24-hour safe concurrent access.

## Files

- `state_db.py` — Main library (27 functions, ~450 lines)
- `README.md` — This file

## Installation

Copy `state_db.py` to `.claude/scripts/lib/`. No external dependencies beyond Python 3.8+ stdlib.

## Quick Start

```python
from lib.state_db import init_schema, register_worker, try_lock_task

# Initialize database (idempotent)
init_schema()

# Register a worker
register_worker("codex-1", "codex", pid=12345)

# Atomically lock a task
if try_lock_task("task-001", "/path/to/task.md", "codex-1", ttl_sec=1800):
    # Do work...
    release_task_lock("task-001", "done")
else:
    print("Task already locked by another worker")
```

## Core Functions

### Worker Management

- `register_worker(worker_id, ai_type, pid)` — Register or update worker
- `update_heartbeat(worker_id)` — Update last_heartbeat timestamp
- `mark_worker_dead(worker_id, reason=None)` — Mark worker as dead
- `get_live_workers(max_age_sec=300)` — List workers with recent heartbeat
- `set_worker_quota_wait(worker_id, backoff_sec)` — Set quota backoff period

### Task Locking

All operations are atomic via `BEGIN IMMEDIATE` transactions.

- `try_lock_task(task_id, task_file, worker_id, ttl_sec=1800)` — **Returns bool**. Atomically acquire lock. Returns `False` if locked by another worker with non-expired TTL.
- `release_task_lock(task_id, final_status)` — Release lock, set final status
- `expire_stale_locks()` — Cleanup locks past their TTL. **Returns count freed**

Lock TTL defaults to 30 minutes. Auto-expires; can be manually freed.

### Metrics

- `record_metric(ai, model_id, tokens_in, tokens_out, cost_usd, latency_ms, success, task_id=None, cache_hit=False, error_class=None)` — Record API call
- `get_metrics_summary(hours=24)` — Get aggregated stats (AI → count, success_rate, cost, latency, cache_hits, tokens)

Fields:
- `ai` — "claude-opus", "codex", "gemini", "claude-haiku"
- `error_class` — "quota", "rate_limit", "timeout", "5xx", "parse", "other" (null if success)

### Quota Management

- `set_quota_exceeded(ai, expires_at, error_msg)` — Mark AI quota-exceeded until epoch
- `is_quota_exceeded(ai)` — **Returns bool**. Auto-clears if expired
- `clear_quota(ai)` — Manually clear quota flag

### Budget Management

- `add_spend(cost_usd)` — Add to today's spend. **Returns new total**. Auto-rolls over daily
- `check_daily_rollover()` — Reset spend if date changed
- `is_breaker_tripped()` — **Returns bool**. Check budget breaker state
- `trip_breaker(reason=None)` — Manually trip breaker
- `reset_breaker()` — Reset breaker

### Session Management

- `update_claude_heartbeat()` — Update Claude Code heartbeat
- `is_claude_alive(max_age_sec=300)` — **Returns bool**. Check if Claude session alive
- `set_orca_enabled(enabled, reason=None)` — Enable/disable orca auto

## Schema

### workers
Track all active workers (Codex, Gemini, Claude, etc.)

```sql
CREATE TABLE workers (
  worker_id TEXT PRIMARY KEY,        -- "codex-1", "gemini-2"
  ai_type TEXT NOT NULL,             -- codex|gemini|claude|haiku
  pid INTEGER,
  started_at INTEGER NOT NULL,       -- unix epoch
  last_heartbeat INTEGER NOT NULL,
  status TEXT NOT NULL,              -- running|idle|dead|quota_wait
  quota_backoff_until INTEGER,
  quota_retry_count INTEGER DEFAULT 0
);
```

### tasks
Task lifecycle + atomic locking

```sql
CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  task_file TEXT NOT NULL,           -- file path
  ai_assigned TEXT,
  worker_id TEXT,                    -- FK workers, NULL if unlocked
  status TEXT NOT NULL,              -- pending|locked|running|done|failed|verified
  locked_at INTEGER,
  locked_until INTEGER,              -- auto-expire if past
  created_at INTEGER NOT NULL,
  completed_at INTEGER,
  retry_count INTEGER DEFAULT 0
);
```

### metrics
All API calls (Codex, Gemini, Claude, local LLM)

```sql
CREATE TABLE metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT,                      -- nullable; some calls unrelated to tasks
  ai TEXT NOT NULL,
  model_id TEXT,
  tokens_in INTEGER NOT NULL DEFAULT 0,
  tokens_out INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL,
  latency_ms INTEGER NOT NULL,
  success INTEGER NOT NULL,          -- 0|1
  cache_hit INTEGER DEFAULT 0,
  retry INTEGER DEFAULT 0,
  recorded_at INTEGER NOT NULL,
  error_class TEXT
);

CREATE INDEX idx_metrics_recorded ON metrics(recorded_at);
CREATE INDEX idx_metrics_ai ON metrics(ai);
CREATE INDEX idx_metrics_task_id ON metrics(task_id);
```

### quota
Per-AI quota state

```sql
CREATE TABLE quota (
  ai TEXT PRIMARY KEY,
  exceeded INTEGER NOT NULL DEFAULT 0,
  exceeded_since INTEGER,
  expires_at INTEGER,
  last_error TEXT,
  updated_at INTEGER NOT NULL
);
```

### budget
Daily spend ceiling + breaker

```sql
CREATE TABLE budget (
  id INTEGER PRIMARY KEY DEFAULT 1,
  daily_limit_usd REAL,              -- NULL = unlimited
  today_spent_usd REAL DEFAULT 0,
  today_date TEXT NOT NULL,          -- "2026-04-23"
  breaker_tripped INTEGER DEFAULT 0,
  breaker_tripped_at INTEGER,
  updated_at INTEGER NOT NULL,
  CHECK (id = 1)
);
```

### session
Claude Code heartbeat + orca state

```sql
CREATE TABLE session (
  id INTEGER PRIMARY KEY DEFAULT 1,
  orca_enabled INTEGER DEFAULT 1,
  orca_stopped_reason TEXT,
  claude_heartbeat INTEGER NOT NULL,  -- unix epoch
  CHECK (id = 1)
);
```

## Configuration

Database location: `.claude/state/orca.db` (relative to project root)

Detected from `$ORCHESTRATION_ROOT` env var or walking up from script location.

WAL mode enabled by default for 24-hour safe concurrent writes.

## Migration (Phase 1)

See `init-state-db.py`:

1. Creates `.claude/state/orca.db` if missing
2. Migrates `token-usage.jsonl` → metrics table (renames to `.jsonl.migrated`)
3. Migrates `*-quota-exceeded` flags → quota table (renames to `.json.migrated`)
4. Migrates `.hb` heartbeat files → workers table (renames to `.hb.migrated`)

Backward compatible: legacy files left on disk (renamed), not deleted.

## Phase 2 (Future)

Worker scripts (`.bat`, `.sh`) will transition to SQLite:
- Register via `register_worker()` on startup
- Periodic `update_heartbeat()` calls (e.g., every 60s)
- Lock tasks via `try_lock_task()` atomically
- Record metrics via `record_metric()` on completion

## Concurrency & Safety

- **WAL mode**: Multiple readers + single writer simultaneously
- **BEGIN IMMEDIATE**: Reader-writer conflicts resolved atomically
- **Thread lock**: Python-level lock for multiprocess safety on Windows
- **TTL**: Stale locks auto-expire; can be freed manually

## Error Handling

Errors logged to `.claude/state/state-db-errors.log` (JSON lines).

## Testing

Run `test-state-db.py`:

```bash
python .claude/scripts/test-state-db.py
```

All 15 tests cover: init, workers, locking, lock expiry, metrics, quota, budget, session, orca state.

## Performance

- **Single row insert**: ~1-2ms
- **Lock contention**: ~5-10ms (BEGIN IMMEDIATE overhead)
- **Large queries (24h summary)**: ~10-20ms
- **DB size**: ~1MB per 10k metrics

## Backward Compatibility

**Not breaking**: Legacy file-based state (`orca-enabled`, `orca-stopped`, `.hb` files, quota flags) remains on disk. Phase 1 reads from files, Phase 2 will migrate writes to SQLite.

## Future Extensions

- Distributed locking (add `lock_version` for fencing)
- Metrics export (Prometheus, InfluxDB)
- Budget alerts (webhooks)
- Task replay/recovery (add `replay_log` table)
