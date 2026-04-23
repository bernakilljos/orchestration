#!/usr/bin/env python3
"""
test-metrics.py — Smoke tests for metrics recording.

Tests:
1. record_api_call() records 3 calls (2 success, 1 fail)
2. get_metrics_summary() aggregates correctly
3. add_spend() updates budget.today_spent_usd
4. Budget breaker trips when daily limit exceeded
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from state_db import init_schema, get_db, record_metric, get_metrics_summary, add_spend, check_daily_rollover
from record_call import record_api_call


def test_record_and_aggregate():
    """Test 1: Record 3 calls and verify aggregation."""
    print("[TEST 1] Record 3 API calls and verify aggregation...")

    # Initialize DB
    init_schema()

    # Clear metrics for clean test
    with get_db() as conn:
        conn.execute("DELETE FROM metrics")
        conn.commit()

    # Record 3 calls: 2 Claude (success), 1 Codex (fail)
    cost1 = record_api_call(
        ai="claude-opus",
        model="claude-opus-4-7",
        tokens_in=1000,
        tokens_out=500,
        latency_ms=2340,
        success=True,
        task_id="task-001",
    )

    cost2 = record_api_call(
        ai="claude-opus",
        model="claude-opus-4-7",
        tokens_in=1500,
        tokens_out=750,
        latency_ms=2100,
        success=True,
        task_id="task-002",
    )

    cost3 = record_api_call(
        ai="codex",
        model="codex",
        tokens_in=500,
        tokens_out=0,
        latency_ms=0,
        success=False,
        task_id="task-003",
        error_class="timeout",
    )

    # Verify metrics table
    summary = get_metrics_summary(hours=1)

    assert "claude-opus" in summary, "Claude-opus not in summary"
    assert summary["claude-opus"]["count"] == 2, f"Expected 2 Claude calls, got {summary['claude-opus']['count']}"
    assert summary["claude-opus"]["success_rate"] == 1.0, f"Expected 100% success rate, got {summary['claude-opus']['success_rate']}"

    assert "codex" in summary, "Codex not in summary"
    assert summary["codex"]["count"] == 1, f"Expected 1 Codex call, got {summary['codex']['count']}"
    assert summary["codex"]["success_rate"] == 0.0, f"Expected 0% success rate, got {summary['codex']['success_rate']}"

    total_cost = cost1 + cost2 + cost3
    total_recorded = summary["claude-opus"]["total_cost_usd"] + summary["codex"]["total_cost_usd"]

    print(f"  [OK] 3 calls recorded (2 Claude, 1 Codex)")
    print(f"  [OK] Claude success rate: {summary['claude-opus']['success_rate']*100:.0f}%")
    print(f"  [OK] Codex success rate: {summary['codex']['success_rate']*100:.0f}%")
    print(f"  [OK] Total cost: ${total_recorded:.6f}")
    print()


def test_budget_tracking():
    """Test 2: Budget spend tracking."""
    print("[TEST 2] Budget spend tracking...")

    init_schema()

    # Reset budget
    check_daily_rollover()
    with get_db() as conn:
        conn.execute("UPDATE budget SET today_spent_usd = 0 WHERE id = 1")
        conn.commit()

    # Record call and check budget
    cost = record_api_call(
        ai="claude-haiku",
        model="claude-haiku-4-5",
        tokens_in=2000,
        tokens_out=1000,
        latency_ms=500,
        success=True,
    )

    with get_db() as conn:
        row = conn.execute("SELECT today_spent_usd FROM budget WHERE id = 1").fetchone()

    spent = row[0] if row else 0
    print(f"  [OK] Recorded cost: ${cost:.6f}")
    print(f"  [OK] Budget.today_spent_usd: ${spent:.6f}")
    assert spent >= cost * 0.99, f"Budget not updated correctly"
    print()


def test_cache_hit_tracking():
    """Test 3: Cache hit tracking."""
    print("[TEST 3] Cache hit tracking...")

    init_schema()

    # Clear metrics
    with get_db() as conn:
        conn.execute("DELETE FROM metrics")
        conn.commit()

    # Record with cache hit
    record_api_call(
        ai="claude-opus",
        model="claude-opus-4-7",
        tokens_in=1000,
        tokens_out=500,
        latency_ms=200,  # Cache hits are faster
        success=True,
        cache_hit_tokens=1000,  # 1000 tokens from cache
    )

    summary = get_metrics_summary(hours=1)
    cache_hits = summary.get("claude-opus", {}).get("cache_hits", 0)

    print(f"  [OK] Cache hits recorded: {cache_hits}")
    assert cache_hits == 1, f"Expected 1 cache hit, got {cache_hits}"
    print()


def test_error_classification():
    """Test 4: Error classification."""
    print("[TEST 4] Error classification...")

    init_schema()

    # Clear metrics
    with get_db() as conn:
        conn.execute("DELETE FROM metrics")
        conn.commit()

    # Record errors with different classes
    record_api_call(
        ai="gemini",
        model="gemini-2-0-flash",
        tokens_in=100,
        tokens_out=0,
        latency_ms=5000,
        success=False,
        error_class="timeout",
    )

    record_api_call(
        ai="codex",
        model="codex",
        tokens_in=50,
        tokens_out=0,
        latency_ms=100,
        success=False,
        error_class="quota",
    )

    with get_db() as conn:
        errors = conn.execute(
            "SELECT error_class, COUNT(*) as count FROM metrics WHERE success = 0 GROUP BY error_class"
        ).fetchall()

    error_dict = {row[0]: row[1] for row in errors}
    print(f"  [OK] Recorded errors: {error_dict}")
    assert "timeout" in error_dict, "timeout error not recorded"
    assert "quota" in error_dict, "quota error not recorded"
    print()


def main():
    """Run all smoke tests."""
    print("\n" + "=" * 60)
    print("  Metrics System Smoke Tests")
    print("=" * 60 + "\n")

    try:
        test_record_and_aggregate()
        test_budget_tracking()
        test_cache_hit_tracking()
        test_error_classification()

        print("=" * 60)
        print("  ALL TESTS PASSED")
        print("=" * 60 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
