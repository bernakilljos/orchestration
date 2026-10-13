#!/usr/bin/env python3
"""Smoke tests for state_db.py library."""

import sys
import time
from pathlib import Path

# Add lib to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / "lib"))

from state_db import (
    init_schema, get_db_path, get_db,
    register_worker, update_heartbeat, mark_worker_dead, get_live_workers,
    try_lock_task, release_task_lock, expire_stale_locks,
    record_metric, get_metrics_summary,
    set_quota_exceeded, is_quota_exceeded, clear_quota,
    add_spend, is_breaker_tripped, trip_breaker, reset_breaker,
    check_daily_rollover, update_claude_heartbeat, is_claude_alive,
    set_orca_enabled
)


class TestRunner:
  def __init__(self):
    self.passed = 0
    self.failed = 0
    self.tests = []

  def test(self, name: str, fn):
    """Run a test function."""
    try:
      fn()
      self.tests.append((name, "PASS"))
      self.passed += 1
      print(f"  [PASS] {name}")
    except AssertionError as e:
      self.tests.append((name, f"FAIL: {e}"))
      self.failed += 1
      print(f"  [FAIL] {name}: {e}")
    except Exception as e:
      self.tests.append((name, f"ERROR: {e}"))
      self.failed += 1
      print(f"  [ERROR] {name}: {e}")

  def summary(self):
    """Print summary."""
    total = self.passed + self.failed
    print(f"\n{'='*60}")
    print(f"Test Results: {self.passed}/{total} PASSED")
    if self.failed > 0:
      print(f"\nFailed tests:")
      for name, result in self.tests:
        if "FAIL" in result or "ERROR" in result:
          print(f"  {name}: {result}")
    print(f"{'='*60}\n")
    return 0 if self.failed == 0 else 1


def test_db_init():
  """Test database initialization."""
  init_schema()
  db_path = get_db_path()
  assert db_path.exists(), f"Database not created at {db_path}"


def test_worker_registration():
  """Test worker registration and heartbeat."""
  register_worker("test-worker-1", "claude", 12345)
  time.sleep(0.1)
  update_heartbeat("test-worker-1")

  workers = get_live_workers(max_age_sec=60)
  assert any(w["worker_id"] == "test-worker-1" for w in workers), \
    "Worker not found in live workers"


def test_worker_dead():
  """Test marking worker dead."""
  register_worker("test-worker-2", "codex", 12346)
  mark_worker_dead("test-worker-2", "test death")

  workers = get_live_workers(max_age_sec=60)
  assert not any(w["worker_id"] == "test-worker-2" for w in workers), \
    "Dead worker should not be in live workers"


def test_task_lock_single():
  """Test single task lock."""
  locked = try_lock_task("task-001", "/path/to/task.md", "worker-1", ttl_sec=60)
  assert locked is True, "First lock should succeed"

  # Try to lock same task again
  locked = try_lock_task("task-001", "/path/to/task.md", "worker-2", ttl_sec=60)
  assert locked is False, "Second lock by different worker should fail"


def test_task_lock_parallel():
  """Test concurrent lock attempts (simulated via transactions)."""
  # Note: Windows multiprocessing has limitations. Test via rapid sequential locks instead.
  # First worker locks
  locked1 = try_lock_task("task-parallel", "/path/to/task.md", "worker-p1", ttl_sec=60)
  assert locked1 is True, "First lock should succeed"

  # Immediate second attempt should fail
  locked2 = try_lock_task("task-parallel", "/path/to/task.md", "worker-p2", ttl_sec=60)
  assert locked2 is False, "Second lock should fail - task already locked"


def test_task_release():
  """Test task lock release."""
  try_lock_task("task-002", "/path/to/task2.md", "worker-1", ttl_sec=60)
  release_task_lock("task-002", "done")

  # Try to lock same task again - should succeed now
  locked = try_lock_task("task-002", "/path/to/task2.md", "worker-2", ttl_sec=60)
  assert locked is True, "Lock should succeed after release"


def test_lock_expiry():
  """Test stale lock expiration."""
  try_lock_task("task-003", "/path/to/task3.md", "worker-1", ttl_sec=1)  # Expires in 1 sec
  time.sleep(1.5)  # Wait for expiry

  count = expire_stale_locks()
  assert count >= 1, f"Stale lock should be expired, got count={count}"

  # Now lock should succeed
  locked = try_lock_task("task-003", "/path/to/task3.md", "worker-2", ttl_sec=60)
  assert locked is True, "Lock should succeed on expired task"


def test_metrics_record():
  """Test metric recording."""
  record_metric(
    ai="claude-opus",
    model_id="claude-opus-4-7",
    tokens_in=100,
    tokens_out=50,
    cost_usd=0.015,
    latency_ms=1200,
    success=True,
    task_id="task-metrics-001",
    cache_hit=False,
    error_class=None
  )

  summary = get_metrics_summary(hours=1)
  assert "claude-opus" in summary, "Metric should be in summary"
  assert summary["claude-opus"]["count"] >= 1, "Count should be >= 1"


def test_metrics_summary():
  """Test metrics aggregation."""
  record_metric("codex", "codex-model-x", 200, 100, 0.02, 500, True, error_class=None)
  record_metric("codex", "codex-model-x", 150, 75, 0.015, 450, True, error_class=None)
  record_metric("gemini", "gemini-2.0", 300, 150, 0.01, 800, False, error_class="timeout")

  summary = get_metrics_summary(hours=1)
  assert "codex" in summary, "Codex should be in summary"
  assert "gemini" in summary, "Gemini should be in summary"
  assert summary["codex"]["count"] >= 2, "Codex count >= 2"
  assert summary["gemini"]["count"] >= 1, "Gemini count >= 1"


def test_quota_exceeded():
  """Test quota management."""
  expire_time = int(time.time()) + 3600
  set_quota_exceeded("codex", expire_time, "Rate limit: 429")

  assert is_quota_exceeded("codex") is True, "Codex should be marked exceeded"
  assert is_quota_exceeded("gemini") is False, "Gemini should not be exceeded"

  clear_quota("codex")
  assert is_quota_exceeded("codex") is False, "Codex should be cleared"


def test_quota_auto_expire():
  """Test automatic quota expiration."""
  expire_time = int(time.time()) - 1  # Already expired
  set_quota_exceeded("test-ai", expire_time, "old error")

  # Should auto-clear when checking
  assert is_quota_exceeded("test-ai") is False, "Quota should auto-clear if expired"


def test_budget_spend():
  """Test budget tracking."""
  check_daily_rollover()
  initial = add_spend(1.5)
  assert initial >= 1.5, f"Spend should be >= 1.5, got {initial}"

  second = add_spend(0.5)
  assert second > initial, "Second spend should increase total"


def test_budget_breaker():
  """Test budget breaker."""
  reset_breaker()
  assert is_breaker_tripped() is False, "Breaker should not be tripped initially"

  trip_breaker("test breach")
  assert is_breaker_tripped() is True, "Breaker should be tripped"

  reset_breaker()
  assert is_breaker_tripped() is False, "Breaker should be reset"


def test_session_heartbeat():
  """Test Claude session heartbeat."""
  update_claude_heartbeat()
  assert is_claude_alive(max_age_sec=60) is True, "Claude should be alive after heartbeat"

  # Simulate stale heartbeat
  import sqlite3
  conn = sqlite3.connect(str(get_db_path()))
  conn.execute("UPDATE session SET claude_heartbeat = ? WHERE id = 1",
               (int(time.time()) - 400,))
  conn.commit()
  conn.close()

  assert is_claude_alive(max_age_sec=300) is False, "Claude should be dead if old heartbeat"


def test_orca_enabled():
  """Test orca enabled/disabled state."""
  set_orca_enabled(True)
  update_claude_heartbeat()

  set_orca_enabled(False, "test stop reason")
  update_claude_heartbeat()

  set_orca_enabled(True)
  update_claude_heartbeat()
  # Just verify no errors


def main():
  """Run all tests."""
  print("\n" + "="*60)
  print("State DB Library Tests")
  print("="*60 + "\n")

  # Clean up test database
  db_path = get_db_path()
  if db_path.exists():
    try:
      db_path.unlink()
      print(f"[*] Cleaned up old database at {db_path}\n")
    except:
      pass

  runner = TestRunner()

  print("Database Initialization")
  runner.test("init_schema", test_db_init)

  print("\nWorker Management")
  runner.test("register_worker", test_worker_registration)
  runner.test("mark_worker_dead", test_worker_dead)

  print("\nTask Locking")
  runner.test("single_lock", test_task_lock_single)
  runner.test("concurrent_locks", test_task_lock_parallel)
  runner.test("lock_release", test_task_release)
  runner.test("lock_expiry", test_lock_expiry)

  print("\nMetrics")
  runner.test("record_metric", test_metrics_record)
  runner.test("metrics_summary", test_metrics_summary)

  print("\nQuota Management")
  runner.test("quota_exceeded", test_quota_exceeded)
  runner.test("quota_auto_expire", test_quota_auto_expire)

  print("\nBudget Management")
  runner.test("budget_spend", test_budget_spend)
  runner.test("budget_breaker", test_budget_breaker)

  print("\nSession Management")
  runner.test("session_heartbeat", test_session_heartbeat)
  runner.test("orca_enabled", test_orca_enabled)

  return runner.summary()


if __name__ == "__main__":
  sys.exit(main())
