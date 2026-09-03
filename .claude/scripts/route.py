#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route.py — CLI tool for routing decisions and budget management.

Usage:
    python route.py [--task-type TYPE] [--estimated-tokens N] [--ambiguous] [--status]
    python route.py --set-daily-limit USD
    python route.py --clear-quota AI_TYPE
    python route.py --trip-breaker
    python route.py --reset-breaker
    python route.py --metrics [--hours N]

Examples:
    # Get routing decision
    python route.py --task-type design --estimated-tokens 5000

    # Check system status
    python route.py --status

    # Set daily budget limit
    python route.py --set-daily-limit 50.00

    # View 24-hour metrics
    python route.py --metrics --hours 24
"""

import sys
import argparse
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from router import route, TaskType, AiChoice
from state_db import (
    init_schema,
    get_metrics_summary,
    is_breaker_tripped,
    is_quota_exceeded,
    trip_breaker,
    reset_breaker,
    clear_quota,
    check_daily_rollover,
    add_spend,
)


def cmd_route(args):
    """Route a single task."""
    task_type = TaskType(args.task_type) if args.task_type else TaskType.DESIGN
    estimated_tokens = args.estimated_tokens or 5000
    is_ambiguous = args.ambiguous

    decision = route(task_type, estimated_tokens, is_ambiguous=is_ambiguous)

    output = {
        "ai": decision.ai.value,
        "use_thinking": decision.use_thinking,
        "thinking_budget": decision.thinking_budget,
        "use_caching": decision.use_caching,
        "worker_count": decision.worker_count,
        "estimated_cost_usd": decision.estimated_cost_usd,
        "reason": decision.reason,
        "fallback_chain": [ai.value for ai in decision.fallback_chain],
    }

    print(json.dumps(output, indent=2))


def cmd_status(args):
    """Print system status."""
    check_daily_rollover()

    breaker = is_breaker_tripped()
    metrics = get_metrics_summary(hours=24)

    print("=== Orchestration Router Status ===\n")

    # Budget status
    from state_db import get_db
    with get_db() as conn:
        budget_row = conn.execute(
            "SELECT today_spent_usd, daily_limit_usd FROM budget WHERE id=1"
        ).fetchone()
        today_spent = budget_row[0] if budget_row else 0.0
        daily_limit = budget_row[1] if budget_row else None

    if daily_limit:
        pct = (today_spent / daily_limit * 100) if daily_limit > 0 else 0
        limit_str = f"{daily_limit:.2f}"
        status_str = "TRIPPED" if breaker else "OK"
        print(f"Budget: ${today_spent:.2f} / ${limit_str} ({pct:.1f}%) - {status_str}")
    else:
        print(f"Budget: ${today_spent:.2f} / unlimited (no limit set)")

    print()

    # Quota status
    print("Quota Status:")
    for ai_name in [
        "claude-fable-5",
        "claude-opus-4-8",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "codex",
        "gemini",
        "grok",       # Perplexity Computer 패턴 — lightweight/speed-sensitive
        "gpt-5.2",    # Perplexity Computer 패턴 — long-context recall (2M+)
    ]:
        status = "EXCEEDED" if is_quota_exceeded(ai_name) else "OK"
        print(f"  {ai_name:<20} {status}")

    print()

    # Metrics
    if metrics:
        print("Metrics (24h):")
        for ai, stats in metrics.items():
            success_rate = stats["success_rate"] * 100
            cost = stats["total_cost_usd"]
            print(
                f"  {ai:<20} "
                f"{stats['count']} calls, "
                f"{success_rate:.0f}% success, "
                f"${cost:.2f} cost"
            )
    else:
        print("Metrics: No data")


def cmd_set_daily_limit(args):
    """Set daily budget limit."""
    limit_usd = float(args.set_daily_limit)
    from state_db import get_db
    with get_db() as conn:
        conn.execute(
            "UPDATE budget SET daily_limit_usd = ? WHERE id = 1",
            (limit_usd,)
        )
        conn.commit()
    print(f"Daily limit set to ${limit_usd:.2f}")


def cmd_clear_quota(args):
    """Clear quota exceeded for an AI."""
    ai_type = args.clear_quota
    clear_quota(ai_type)
    print(f"Quota cleared for {ai_type}")


def cmd_trip_breaker(args):
    """Manually trip budget breaker."""
    trip_breaker("Manual: CLI trip")
    print("Budget breaker TRIPPED")


def cmd_reset_breaker(args):
    """Reset budget breaker."""
    reset_breaker()
    print("Budget breaker RESET")


def cmd_metrics(args):
    """Print detailed metrics."""
    hours = args.hours or 24
    metrics = get_metrics_summary(hours=hours)

    print(f"=== Metrics (last {hours}h) ===\n")
    if metrics:
        for ai, stats in metrics.items():
            print(f"AI: {ai}")
            print(f"  Calls: {stats['count']}")
            print(f"  Success rate: {stats['success_rate']*100:.1f}%")
            print(f"  Input tokens: {stats['tokens_in']:,}")
            print(f"  Output tokens: {stats['tokens_out']:,}")
            print(f"  Total cost: ${stats['total_cost_usd']:.4f}")
            print(f"  Avg latency: {stats['avg_latency_ms']:.0f}ms")
            print(f"  Cache hits: {stats['cache_hits']}")
            print()
    else:
        print("No metrics recorded")


def cmd_check(args):
    """Check if an AI can be used (quota + budget + fable-5 20% gate).

    Exits 0 if OK, 1 if any gate fails. Prints flags on stdout.
    """
    ai = args.check
    from state_db import get_db

    # SUSPEND mode 이력:
    #   2026-06-12 US export-control 로 Fable 5 / Mythos 5 suspend
    #   2026-07-01 Anthropic 이 restored (api-release 공식 statement)
    # 재-suspend 필요 시 아래 set 에 모델 ID 추가
    SUSPEND_MODELS = set()

    quota_ok = 0 if is_quota_exceeded(ai) else 1
    budget_ok = 1
    fable_ok = 0 if ai in SUSPEND_MODELS else 1
    fable_spent = 0.0
    fable_cap = None

    with get_db() as conn:
        row = conn.execute(
            "SELECT breaker_tripped, today_spent_usd, daily_limit_usd "
            "FROM budget WHERE id=1"
        ).fetchone()
        if row:
            breaker = row[0] or 0
            today_spent = row[1] or 0.0
            daily_limit = row[2]
            if breaker:
                budget_ok = 0
            if daily_limit and today_spent >= daily_limit:
                budget_ok = 0

            if ai == "claude-fable-5" and daily_limit:
                try:
                    fable_spent = conn.execute(
                        "SELECT COALESCE(SUM(total_cost_usd),0) FROM metrics "
                        "WHERE ai=? AND ts > datetime('now','-24 hours')",
                        (ai,),
                    ).fetchone()[0] or 0.0
                except Exception:
                    fable_spent = 0.0
                fable_cap = daily_limit * 0.20
                # SUSPEND 모드면 fable_ok 가 이미 0 -> 추가 게이트 영향 X
                if ai not in SUSPEND_MODELS and fable_spent >= fable_cap:
                    fable_ok = 0

    if ai in SUSPEND_MODELS:
        print(
            f"quota_ok={quota_ok} budget_ok={budget_ok} fable_ok=0 "
            f"SUSPEND=US-export-control-2026-06-12 "
            f"fallback=claude-opus-4-8"
        )
        ok = 0
    elif ai == "claude-fable-5" and fable_cap is not None:
        print(
            f"quota_ok={quota_ok} budget_ok={budget_ok} fable_ok={fable_ok} "
            f"fable_spent=${fable_spent:.2f} fable_cap=${fable_cap:.2f}"
        )
        ok = quota_ok and budget_ok and fable_ok
    else:
        print(f"quota_ok={quota_ok} budget_ok={budget_ok}")
        ok = quota_ok and budget_ok

    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Route tasks and manage budget/quota"
    )

    # Route command
    parser.add_argument(
        "--task-type",
        choices=["design", "implement", "verify", "document", "refactor", "simple"],
        help="Task classification",
    )
    parser.add_argument(
        "--estimated-tokens", type=int, help="Estimated input tokens"
    )
    parser.add_argument(
        "--ambiguous", action="store_true", help="Task is ambiguous"
    )

    # Status command
    parser.add_argument("--status", action="store_true", help="Print system status")

    # Budget/quota commands
    parser.add_argument(
        "--set-daily-limit", help="Set daily budget limit (USD)"
    )
    parser.add_argument("--clear-quota", help="Clear quota for AI type")
    parser.add_argument("--trip-breaker", action="store_true", help="Trip budget breaker")
    parser.add_argument(
        "--reset-breaker", action="store_true", help="Reset budget breaker"
    )

    # Metrics
    parser.add_argument("--metrics", action="store_true", help="Print detailed metrics")
    parser.add_argument("--hours", type=int, help="Hours to include in metrics")

    # Check (quota + budget + fable-5 20% gate)
    parser.add_argument(
        "--check",
        help="Check if AI can be used (e.g. --check claude-fable-5). "
             "Exits 0 if OK, 1 if any gate fails.",
    )

    args = parser.parse_args()

    # Initialize DB schema
    init_schema()

    # Route routing decision (default)
    if args.task_type or args.estimated_tokens or args.ambiguous:
        cmd_route(args)
    elif args.status:
        cmd_status(args)
    elif args.set_daily_limit:
        cmd_set_daily_limit(args)
    elif args.clear_quota:
        cmd_clear_quota(args)
    elif args.trip_breaker:
        cmd_trip_breaker(args)
    elif args.reset_breaker:
        cmd_reset_breaker(args)
    elif args.metrics:
        cmd_metrics(args)
    elif args.check:
        cmd_check(args)
    else:
        # Default: show status
        cmd_status(args)


if __name__ == "__main__":
    main()
