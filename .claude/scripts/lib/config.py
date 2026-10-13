#!/usr/bin/env python3
"""
Configuration & Constants — Central SoT for all kit scripts.

Consolidates hardcoded values, magic numbers, TTLs, timeouts, buffer sizes, PATH defaults.
Environment variables can override with prefix CLAUDE_KIT_*.
"""

import os
from pathlib import Path

def _get_env_int(key: str, default: int) -> int:
    """Helper: get integer from env, fallback to default."""
    env_key = f"CLAUDE_KIT_{key.upper()}"
    try:
        return int(os.getenv(env_key, default))
    except ValueError:
        return default

# ============ LOGGING & I/O ============
BUFFER_SIZE = _get_env_int("buffer_size", 4096)
LOG_RETENTION_DAYS = _get_env_int("log_retention_days", 14)
MAX_LOG_LINES = _get_env_int("max_log_lines", 10000)

# ============ CACHING & TTL ============
RULE_ADHERENCE_TTL_SEC = _get_env_int("rule_adherence_ttl_sec", 600)
SNAPSHOT_RETENTION_DAYS = _get_env_int("snapshot_retention_days", 30)

# ============ FILE LOCKING ============
FILE_LOCK_POLL_INTERVAL_SEC = _get_env_int("file_lock_poll_interval_sec", 2)
FILE_LOCK_MAX_WAIT_SEC = _get_env_int("file_lock_max_wait_sec", 60)

# ============ TASK & PROCESSING ============
TASK_TIMEOUT_SEC = _get_env_int("task_timeout_sec", 3600)
TASK_RETRY_MAX_ATTEMPTS = _get_env_int("task_retry_max_attempts", 3)
CODEX_HALLUCINATION_THRESHOLD_ATTEMPTS = _get_env_int("codex_hallucination_threshold", 3)

# ============ WATCHDOG ============
WATCHDOG_HEARTBEAT_INTERVAL_SEC = _get_env_int("watchdog_heartbeat_interval_sec", 300)
WATCHDOG_STALE_WORKER_THRESHOLD_SEC = _get_env_int("watchdog_stale_threshold_sec", 600)

# ============ RULE ADHERENCE ============
RULE_ADHERENCE_WINDOW_DAYS = _get_env_int("rule_adherence_window_days", 30)

# ============ ARTIFACT FRESHNESS ============
ARTIFACT_DOCX_MAX_AGE_DAYS = _get_env_int("artifact_docx_max_age_days", 90)
ARTIFACT_PPTX_MAX_AGE_DAYS = _get_env_int("artifact_pptx_max_age_days", 60)
ARTIFACT_MD_MAX_AGE_DAYS = _get_env_int("artifact_md_max_age_days", 45)

# ============ CLEANUP ============
CLEANUP_DONE_TASK_AGE_DAYS = _get_env_int("cleanup_done_task_age_days", 30)
CLEANUP_TEMP_FILE_AGE_DAYS = _get_env_int("cleanup_temp_file_age_days", 3)
CLEANUP_LOG_AGE_DAYS = _get_env_int("cleanup_log_age_days", 14)

# ============ DEBUG ============
DEBUG_MODE = os.getenv("CLAUDE_KIT_DEBUG", "0").lower() in ("1", "true")
