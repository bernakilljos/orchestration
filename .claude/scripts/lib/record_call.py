#!/usr/bin/env python3
"""
record_call.py — Workers record API call metrics to SQLite.

CLI usage:
    python record_call.py --ai codex --model codex \\
        --tokens-in 1000 --tokens-out 500 \\
        --latency-ms 2500 --success 1 \\
        --task-id task-42 [--cache-hit 1] [--error-class none]

Python import usage:
    from record_call import record_api_call
    cost = record_api_call(
        ai="claude-opus",
        model="claude-opus-4-7",
        tokens_in=1000,
        tokens_out=500,
        latency_ms=2340,
        success=True,
        task_id="task-001"
    )
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from state_db import record_metric, add_spend, check_daily_rollover


def estimate_cost(model: str, tokens_in: int, tokens_out: int,
                  cache_hit_tokens: int = 0, cache_write_tokens: int = 0) -> float:
    """
    Estimate cost for API call. Fallback when pricing.py not available.
    Uses typical 3:1 output:input token cost ratio.
    """
    # Typical pricing ratios per 1M tokens
    pricing_map = {
        "claude-opus-4-7": (0.015, 0.075),        # $15/$75 per 1M
        "claude-haiku-4-5": (0.0008, 0.004),      # $0.80/$4 per 1M
        "codex": (0.0008, 0.0024),                # Placeholder
        "gemini-2-0-flash": (0.00008, 0.00032),   # Placeholder
    }

    in_price, out_price = pricing_map.get(model, (0.001, 0.003))

    # Cache tokens cost 10% of normal (Anthropic pricing)
    cache_cost = (cache_hit_tokens * in_price * 0.1 +
                  cache_write_tokens * in_price * 0.25)

    regular_cost = (tokens_in * in_price + tokens_out * out_price) / 1_000_000

    return regular_cost + cache_cost


def record_api_call(
    ai: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
    success: bool,
    task_id: str | None = None,
    cache_hit_tokens: int = 0,
    cache_write_tokens: int = 0,
    error_class: str | None = None,
    retry: int = 0,
    cost_usd: float | None = None,
) -> float:
    """
    Record API call to metrics table and update budget.

    Returns: cost_usd of this call
    """
    check_daily_rollover()

    # Estimate cost if not provided
    if cost_usd is None:
        cost_usd = estimate_cost(
            model, tokens_in, tokens_out,
            cache_hit_tokens, cache_write_tokens
        )

    # Record metric
    record_metric(
        ai=ai,
        model_id=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        success=success,
        task_id=task_id,
        cache_hit=bool(cache_hit_tokens > 0),
        error_class=error_class if error_class and error_class != "none" else None,
    )

    # Update budget
    today_spent = add_spend(cost_usd)

    # Auto-trip breaker if daily limit exceeded
    try:
        from state_db import get_db, trip_breaker
        with get_db() as conn:
            row = conn.execute(
                "SELECT daily_limit_usd FROM budget WHERE id=1"
            ).fetchone()
        if row and row[0] is not None and today_spent >= row[0]:
            trip_breaker(f"Daily limit ${row[0]:.2f} reached (spent ${today_spent:.2f})")
    except Exception:
        pass  # Budget check failed, but metric recorded

    return cost_usd


def main():
    ap = argparse.ArgumentParser(description="Record API call metrics")
    ap.add_argument("--ai", required=True, help="AI type (claude-opus, codex, gemini, etc)")
    ap.add_argument("--model", required=True, help="Model ID")
    ap.add_argument("--tokens-in", type=int, required=True)
    ap.add_argument("--tokens-out", type=int, required=True)
    ap.add_argument("--latency-ms", type=int, required=True)
    ap.add_argument("--success", type=int, required=True, help="1 or 0")
    ap.add_argument("--task-id", default=None)
    ap.add_argument("--cache-hit-tokens", type=int, default=0)
    ap.add_argument("--cache-write-tokens", type=int, default=0)
    ap.add_argument("--error-class", default=None)
    ap.add_argument("--retry", type=int, default=0)
    ap.add_argument("--cost-usd", type=float, default=None)

    args = ap.parse_args()

    cost = record_api_call(
        ai=args.ai,
        model=args.model,
        tokens_in=args.tokens_in,
        tokens_out=args.tokens_out,
        latency_ms=args.latency_ms,
        success=bool(args.success),
        task_id=args.task_id,
        cache_hit_tokens=args.cache_hit_tokens,
        cache_write_tokens=args.cache_write_tokens,
        error_class=args.error_class,
        retry=args.retry,
        cost_usd=args.cost_usd,
    )
    print(f"Recorded: {args.ai}/{args.model} in={args.tokens_in} out={args.tokens_out} cost=${cost:.6f}")


if __name__ == "__main__":
    main()
