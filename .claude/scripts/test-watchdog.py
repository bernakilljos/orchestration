#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test suite for watchdog + backoff system.

Tests:
1. Backoff schedule correctness
2. Stale worker detection
3. Quota-aware backoff extension
4. Worker spawn dry-run
"""

import sys
import time
import os
from pathlib import Path

# Force UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from backoff import compute_backoff, format_duration
from state_db import (
    init_schema, register_worker, update_heartbeat, mark_worker_dead,
    get_live_workers, is_quota_exceeded, set_quota_exceeded, clear_quota,
    tx
)
from watchdog_helpers import (
    get_all_registered_workers, get_workers_ready_to_revive,
    get_dead_workers_to_retry, spawn_worker
)


def test_backoff_schedule():
    """Verify exponential backoff: [600, 1200, 2400, 7200, ...]"""
    expected = [600, 1200, 2400, 7200, 7200, 7200]
    actual = [compute_backoff(i) for i in range(6)]

    if actual == expected:
        print("✓ Backoff schedule correct:", actual)
        return True
    else:
        print("✗ Backoff schedule wrong. Expected:", expected, "Got:", actual)
        return False


def test_format_duration():
    """Verify human-readable duration formatting."""
    tests = [
        (60, "1m"),
        (600, "10m"),
        (1200, "20m"),
        (2400, "40m"),
        (7200, "2h"),
    ]
    all_pass = True
    for sec, expected in tests:
        actual = format_duration(sec)
        if actual == expected:
            print(f"  ✓ {sec}s -> '{actual}'")
        else:
            print(f"  ✗ {sec}s -> expected '{expected}', got '{actual}'")
            all_pass = False
    return all_pass


def test_stale_worker_detection():
    """Create stale worker, verify it's detected as dead."""
    init_schema()

    # Register worker with very old heartbeat
    old_time = int(time.time()) - 600  # 10 min ago
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workers "
            "(worker_id, ai_type, pid, started_at, last_heartbeat, status) "
            "VALUES (?, ?, ?, ?, ?, 'idle')",
            ("test-stale-1", "codex", 0, old_time, old_time),
        )

    # Check that it's NOT in live workers (stale)
    live = get_live_workers(max_age_sec=300)
    live_ids = {w["worker_id"] for w in live}

    if "test-stale-1" not in live_ids:
        print("✓ Stale worker correctly excluded from live workers")

        # Cleanup
        with tx() as conn:
            conn.execute("DELETE FROM workers WHERE worker_id = 'test-stale-1'")
        return True
    else:
        print("✗ Stale worker should not be in live workers list")
        return False


def test_quota_aware_backoff():
    """Test quota-blocked worker detection and backoff extension."""
    init_schema()

    # Register a worker in quota_wait
    now = int(time.time())
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workers "
            "(worker_id, ai_type, pid, started_at, last_heartbeat, status, "
            "quota_backoff_until, quota_retry_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("test-quota-1", "gemini", 0, now, now, "quota_wait", now - 60, 1),
        )

    # Should be in ready_to_revive (backoff_until is in past)
    ready = get_workers_ready_to_revive()
    ready_ids = {w["worker_id"] for w in ready}

    if "test-quota-1" in ready_ids:
        print("✓ Quota-backoff-expired worker detected as ready to revive")

        # Cleanup
        with tx() as conn:
            conn.execute("DELETE FROM workers WHERE worker_id = 'test-quota-1'")
        return True
    else:
        print("✗ Quota-backoff-expired worker should be in ready_to_revive")
        return False


def test_dead_worker_retry_limit():
    """Verify dead workers with retry_count >= 3 are skipped."""
    init_schema()

    now = int(time.time())

    # Worker 1: retry_count = 2 (should be retried)
    with tx() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workers "
            "(worker_id, ai_type, pid, started_at, last_heartbeat, status, "
            "quota_retry_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test-dead-2", "codex", 0, now, now, "dead", 2),
        )
        # Worker 2: retry_count = 3 (should NOT be retried)
        conn.execute(
            "INSERT OR REPLACE INTO workers "
            "(worker_id, ai_type, pid, started_at, last_heartbeat, status, "
            "quota_retry_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("test-dead-3", "codex", 0, now, now, "dead", 3),
        )

    dead_to_retry = get_dead_workers_to_retry()
    dead_ids = {w["worker_id"] for w in dead_to_retry}

    success = True
    if "test-dead-2" in dead_ids:
        print("✓ Dead worker with retry_count=2 included in retry list")
    else:
        print("✗ Dead worker with retry_count=2 should be in retry list")
        success = False

    if "test-dead-3" not in dead_ids:
        print("✓ Dead worker with retry_count=3 excluded from retry list")
    else:
        print("✗ Dead worker with retry_count=3 should NOT be in retry list")
        success = False

    # Cleanup
    with tx() as conn:
        conn.execute("DELETE FROM workers WHERE worker_id IN ('test-dead-2', 'test-dead-3')")

    return success


def test_spawn_worker_dry_run():
    """Test worker spawn with dry_run=True (no actual process)."""
    try:
        result = spawn_worker("codex", "codex-5", dry_run=True)
        if result:
            print("✓ Spawn worker dry_run succeeded (printed command)")
            return True
        else:
            print("✗ Spawn worker dry_run should return True")
            return False
    except Exception as e:
        print(f"✗ Spawn worker dry_run raised exception: {e}")
        return False


def test_quota_exceeded_flag():
    """Test quota exceeded flag set/clear."""
    init_schema()

    # Clear any existing flag
    clear_quota("test-ai")

    # Set quota exceeded
    expires_at = int(time.time()) + 3600
    set_quota_exceeded("test-ai", expires_at, "test error")

    if is_quota_exceeded("test-ai"):
        print("✓ Quota exceeded flag set correctly")
    else:
        print("✗ Quota exceeded flag not set")
        return False

    # Clear it
    clear_quota("test-ai")

    if not is_quota_exceeded("test-ai"):
        print("✓ Quota exceeded flag cleared correctly")
        return True
    else:
        print("✗ Quota exceeded flag should be cleared")
        return False


def main():
    """Run all tests."""
    print("\n=== Watchdog + Backoff Smoke Tests ===\n")

    tests = [
        ("Backoff schedule", test_backoff_schedule),
        ("Format duration", test_format_duration),
        ("Stale worker detection", test_stale_worker_detection),
        ("Quota-aware backoff", test_quota_aware_backoff),
        ("Dead worker retry limit", test_dead_worker_retry_limit),
        ("Spawn worker dry-run", test_spawn_worker_dry_run),
        ("Quota exceeded flag", test_quota_exceeded_flag),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n=== Summary ===")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED\n")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED\n")
        for name, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
