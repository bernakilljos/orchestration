#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test-router.py — Smoke tests for routing and budget system.

Runs:
1. Budget breaker tripped → route() returns BREAKER
2. All quota OK → DESIGN task → Opus 4.7 + thinking
3. Claude quota exceeded → fallback to Codex
4. All quota exceeded → WAIT
5. pricing.estimate_cost() calculations
6. register_outcome() updates metrics

Exit code 0 = PASS, 1 = FAIL
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from router import route, TaskType, AiChoice, register_outcome
from pricing import estimate_cost
from state_db import (
    init_schema,
    trip_breaker,
    reset_breaker,
    set_quota_exceeded,
    clear_quota,
    is_quota_exceeded,
    get_metrics_summary,
    record_metric,
)


def test_breaker_tripped():
    """Test 1: Budget breaker returns BREAKER."""
    print("Test 1: Budget breaker tripped...")
    init_schema()
    reset_breaker()
    trip_breaker("test")

    decision = route(TaskType.DESIGN, 5000)
    assert decision.ai == AiChoice.BREAKER, f"Expected BREAKER, got {decision.ai}"
    assert decision.wait_seconds > 0

    reset_breaker()
    print("  [PASS]")


def test_design_opus():
    """Test 2: DESIGN task → Opus 4.7 with thinking."""
    print("Test 2: DESIGN task routes to Opus 4.7 with thinking...")
    init_schema()
    reset_breaker()
    clear_quota("claude-opus-4-7")
    clear_quota("claude-sonnet-4-6")
    clear_quota("claude-haiku-4-5")

    decision = route(TaskType.DESIGN, 5000)
    assert decision.ai == AiChoice.CLAUDE_OPUS_4_7, f"Expected Opus, got {decision.ai}"
    assert decision.use_thinking is True, "Expected thinking enabled"
    assert decision.thinking_budget == 8000, f"Expected budget 8000, got {decision.thinking_budget}"

    print("  [PASS]")


def test_fallback_on_quota():
    """Test 3: Claude quota exceeded → fallback to Codex."""
    print("Test 3: Claude quota exceeded → fallback...")
    init_schema()
    reset_breaker()
    clear_quota("claude-opus-4-7")
    clear_quota("codex")

    # Exceed Opus quota
    expires_at = int(time.time()) + 3600
    set_quota_exceeded("claude-opus-4-7", expires_at, "test")

    decision = route(TaskType.IMPLEMENT, 100_000)
    # Should fallback to Codex or others since Opus is exceeded
    assert decision.ai != AiChoice.CLAUDE_OPUS_4_7, "Should not use Opus when exceeded"

    clear_quota("claude-opus-4-7")
    print("  [PASS]")


def test_all_exceeded_wait():
    """Test 4: All quotas exceeded → WAIT."""
    print("Test 4: All quotas exceeded → WAIT...")
    init_schema()
    reset_breaker()

    expires_at = int(time.time()) + 3600
    for ai in ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5", "codex", "gemini"]:
        set_quota_exceeded(ai, expires_at, "test")

    decision = route(TaskType.SIMPLE, 100)
    assert decision.ai == AiChoice.WAIT, f"Expected WAIT, got {decision.ai}"
    assert decision.wait_seconds > 0

    # Cleanup
    for ai in ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5", "codex", "gemini"]:
        clear_quota(ai)

    print("  [PASS]")


def test_pricing():
    """Test 5: Pricing calculations."""
    print("Test 5: Pricing calculations...")

    # Opus: 1000 in + 500 out
    cost = estimate_cost("claude-opus-4-7", 1000, 500)
    expected = (1000 / 1_000_000 * 15.0) + (500 / 1_000_000 * 75.0)
    assert abs(cost - expected) < 0.000001, f"Expected {expected}, got {cost}"

    # Sonnet: 1000 in + 500 out
    cost = estimate_cost("claude-sonnet-4-6", 1000, 500)
    expected = (1000 / 1_000_000 * 3.0) + (500 / 1_000_000 * 15.0)
    assert abs(cost - expected) < 0.000001, f"Expected {expected}, got {cost}"

    # With cache hit
    cost = estimate_cost(
        "claude-opus-4-7",
        tokens_in=1000,
        tokens_out=500,
        cache_hit_tokens=500,
    )
    # 500 regular input + 500 cache hit + 500 output
    expected = (500 / 1_000_000 * 15.0) + (500 / 1_000_000 * 1.5) + (500 / 1_000_000 * 75.0)
    assert abs(cost - expected) < 0.000001, f"Cache pricing failed: {cost} vs {expected}"

    print("  [PASS]")


def test_register_outcome():
    """Test 6: register_outcome updates metrics."""
    print("Test 6: register_outcome records metrics...")
    init_schema()

    decision = route(TaskType.SIMPLE, 100)

    # Record outcome
    register_outcome(
        decision=decision,
        tokens_in=100,
        tokens_out=50,
        success=True,
        cost_usd=0.001,
        cache_hit=False,
        error_class=None,
        task_id="test-task-123",
    )

    # Check metrics recorded
    metrics = get_metrics_summary(hours=1)
    assert len(metrics) > 0, "No metrics recorded"
    assert decision.ai.value in metrics, f"AI {decision.ai} not in metrics"

    print("  [PASS]")


def test_simple_task_routing():
    """Test 7: SIMPLE task → Sonnet or Haiku."""
    print("Test 7: SIMPLE task routing...")
    init_schema()
    reset_breaker()
    clear_quota("claude-sonnet-4-6")

    decision = route(TaskType.SIMPLE, 50)
    assert decision.ai in (
        AiChoice.CLAUDE_SONNET_4_6,
        AiChoice.CLAUDE_HAIKU_4_5,
    ), f"Expected Sonnet/Haiku, got {decision.ai}"
    assert decision.use_thinking is False, "SIMPLE should not use thinking"

    print("  [PASS]")


def test_verify_task_routing():
    """Test 8: VERIFY task → Haiku by default."""
    print("Test 8: VERIFY task routing...")
    init_schema()
    reset_breaker()
    clear_quota("claude-haiku-4-5")

    decision = route(TaskType.VERIFY, 10_000)
    assert decision.ai == AiChoice.CLAUDE_HAIKU_4_5, f"Expected Haiku, got {decision.ai}"

    print("  [PASS]")


def main():
    """Run all tests."""
    print("=== Router & Budget System Tests ===\n")

    tests = [
        test_breaker_tripped,
        test_design_opus,
        test_fallback_on_quota,
        test_all_exceeded_wait,
        test_pricing,
        test_register_outcome,
        test_simple_task_routing,
        test_verify_task_routing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL]: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR]: {e}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
