#!/usr/bin/env python3
"""Initialize or upgrade SQLite state database. Migrates from legacy file flags."""

import sys
import json
import os
import time
from pathlib import Path

# Add lib to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "lib"))

from state_db import (
    get_db_path, init_schema, register_worker, set_quota_exceeded,
    record_metric, add_spend, update_claude_heartbeat, _get_project_root
)


def migrate_token_usage_jsonl() -> int:
  """Migrate token-usage.jsonl to metrics table."""
  project_root = _get_project_root()
  jsonl_path = project_root / ".claude" / "state" / "token-usage.jsonl"

  if not jsonl_path.exists():
    return 0

  count = 0
  errors = []
  with open(jsonl_path, "r") as f:
    for line_num, line in enumerate(f, 1):
      line = line.strip()
      if not line:
        continue
      try:
        obj = json.loads(line)
        # Only migrate metrics lines (with 'tokens' or 'event' = 'api_call')
        if "tokens" in obj or obj.get("event") == "api_call":
          ts = obj.get("ts")
          if ts:
            # Parse ISO timestamp to epoch
            try:
              recorded_at = int(time.mktime(
                time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
              ))
            except (ValueError, TypeError):
              recorded_at = int(time.time())

            tokens = obj.get("tokens", {})
            tokens_in = tokens.get("input", 0) or 0
            tokens_out = tokens.get("output", 0) or 0
            cost = obj.get("est_cost_usd")

            ai = obj.get("ai", "unknown")
            model_id = obj.get("model", obj.get("model_id", "unknown"))
            success = obj.get("success", 1) == 1
            error_class = obj.get("error_class")

            record_metric(
              ai=ai,
              model_id=model_id,
              tokens_in=int(tokens_in),
              tokens_out=int(tokens_out),
              cost_usd=float(cost) if cost else None,
              latency_ms=int(obj.get("latency_ms", 0)),
              success=success,
              task_id=obj.get("task_id"),
              cache_hit=obj.get("cache_hit", 0) == 1,
              error_class=error_class
            )
            count += 1
      except Exception as e:
        errors.append(f"Line {line_num}: {str(e)}")

  if errors and len(errors) <= 10:
    for err in errors:
      print(f"Warning: {err}", file=sys.stderr)

  # Rename original file
  migrated_path = jsonl_path.with_suffix(".jsonl.migrated")
  try:
    jsonl_path.rename(migrated_path)
    print(f"[OK] Migrated {count} metrics. Original renamed to {migrated_path.name}")
  except Exception as e:
    print(f"[WARN] Could not rename {jsonl_path.name}: {e}", file=sys.stderr)

  return count


def migrate_quota_flags() -> int:
  """Migrate quota exceeded flag files to quota table."""
  project_root = _get_project_root()
  state_dir = project_root / ".claude" / "state"

  count = 0
  for ai_name in ["codex", "gemini"]:
    flag_path = state_dir / f"{ai_name}-quota-exceeded"
    if flag_path.exists():
      try:
        with open(flag_path, "r") as f:
          obj = json.load(f)
        expire_epoch = obj.get("expire_epoch", int(time.time()) + 3*3600)
        error_msg = obj.get("retry_hint", f"{ai_name} quota exceeded")
        set_quota_exceeded(ai_name, expire_epoch, error_msg)
        count += 1

        # Rename original
        migrated = flag_path.with_suffix(".json.migrated")
        flag_path.rename(migrated)
        print(f"[OK] Migrated {ai_name} quota flag -> {migrated.name}")
      except Exception as e:
        print(f"[WARN] Failed to migrate {ai_name} quota: {e}", file=sys.stderr)

  return count


def migrate_heartbeat_files() -> int:
  """Migrate .hb worker heartbeat files to workers table."""
  project_root = _get_project_root()
  workers_dir = project_root / ".claude" / "state" / "workers"

  if not workers_dir.exists():
    return 0

  count = 0
  for hb_file in workers_dir.glob("*.hb"):
    try:
      worker_id = hb_file.stem  # e.g., "codex-1" from "codex-1.hb"
      ai_type = worker_id.split("-")[0]  # "codex" from "codex-1"
      mtime = int(hb_file.stat().st_mtime)

      # Register as idle with old heartbeat
      register_worker(worker_id, ai_type, None)
      count += 1

      # Rename original
      migrated = hb_file.with_suffix(".hb.migrated")
      hb_file.rename(migrated)
    except Exception as e:
      print(f"[WARN] Failed to migrate {hb_file.name}: {e}", file=sys.stderr)

  if count:
    print(f"[OK] Migrated {count} worker heartbeat files")
  return count


def check_existing_db() -> bool:
  """Check if DB already initialized."""
  db_path = get_db_path()
  if not db_path.exists():
    return False

  # Try to query schema_version
  try:
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row is not None
  except sqlite3.OperationalError:
    return False


def main() -> int:
  """Initialize database and run migrations."""
  try:
    # Check if already initialized
    if check_existing_db():
      print("[OK] Database already initialized with schema v1")
      return 0

    print("[*] Initializing orca.db...")
    init_schema()
    print(f"[OK] Created database at {get_db_path()}")

    # Update Claude heartbeat
    update_claude_heartbeat()
    print("[OK] Set Claude heartbeat")

    # Run migrations
    print("[*] Running migrations...")
    metrics_count = migrate_token_usage_jsonl()
    quota_count = migrate_quota_flags()
    worker_count = migrate_heartbeat_files()

    print(f"\n[SUMMARY]")
    print(f"  Metrics imported: {metrics_count}")
    print(f"  Quota flags migrated: {quota_count}")
    print(f"  Worker heartbeats migrated: {worker_count}")
    print(f"  Database: {get_db_path()}")

    return 0

  except Exception as e:
    print(f"[ERROR] {str(e)}", file=sys.stderr)
    # Log to error file
    error_log = _get_project_root() / ".claude" / "state" / "state-db-errors.log"
    try:
      with open(error_log, "a") as f:
        f.write(json.dumps({
          "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "error": str(e),
          "script": "init-state-db.py"
        }) + "\n")
    except:
      pass
    return 1


if __name__ == "__main__":
  sys.exit(main())
