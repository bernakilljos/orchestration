#!/usr/bin/env python3
"""
metrics-report.py — CLI tool to display metrics summary in table format.

Usage:
    python metrics-report.py [--hours 24] [--ai claude-opus]

Examples:
    python metrics-report.py                  # Last 24h all AI
    python metrics-report.py --hours 72       # Last 72h
    python metrics-report.py --ai claude-opus # Last 24h, Claude only
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "lib"))

from state_db import get_metrics_summary, get_db


def format_table(summary: dict, ai_filter: str = None):
    """Format metrics summary as ASCII table."""
    if ai_filter:
        summary = {k: v for k, v in summary.items() if k == ai_filter}

    if not summary:
        print("No metrics recorded.")
        return

    # Header
    print()
    print("─" * 100)
    print(f"{'AI':<20} {'Calls':<10} {'Success%':<12} {'Tokens (in/out)':<20} {'Cost':<12} {'Avg Latency':<12}")
    print("─" * 100)

    total_cost = 0.0
    total_calls = 0
    total_success = 0

    for ai in sorted(summary.keys()):
        m = summary[ai]
        success_pct = (m["success_rate"] * 100) if m["success_rate"] else 0
        tokens_in = m.get("tokens_in", 0)
        tokens_out = m.get("tokens_out", 0)
        cost = m.get("total_cost_usd", 0.0)
        latency = m.get("avg_latency_ms", 0)
        count = m.get("count", 0)

        # Format tokens with K/M suffix
        if tokens_in >= 1_000_000:
            tokens_in_str = f"{tokens_in/1_000_000:.1f}M"
        elif tokens_in >= 1_000:
            tokens_in_str = f"{tokens_in/1_000:.1f}K"
        else:
            tokens_in_str = str(tokens_in)

        if tokens_out >= 1_000_000:
            tokens_out_str = f"{tokens_out/1_000_000:.1f}M"
        elif tokens_out >= 1_000:
            tokens_out_str = f"{tokens_out/1_000:.1f}K"
        else:
            tokens_out_str = str(tokens_out)

        print(
            f"{ai:<20} {count:<10} {success_pct:<11.1f}% {tokens_in_str}/{tokens_out_str:<17} ${cost:<11.4f} {latency:.0f}ms"
        )

        total_cost += cost
        total_calls += count
        total_success += m.get("success_rate", 0) * count

    print("─" * 100)

    overall_success_pct = (total_success / total_calls * 100) if total_calls > 0 else 0
    print(f"{'TOTAL':<20} {total_calls:<10} {overall_success_pct:<11.1f}% {'':20} ${total_cost:<11.4f}")
    print()

    # Cache stats
    with get_db() as conn:
        since = int(__import__("time").time()) - (24 * 3600)
        row = conn.execute(
            "SELECT SUM(cache_hit) as cache_hits, COUNT(*) as total_calls FROM metrics WHERE recorded_at >= ?",
            (since,)
        ).fetchone()
        if row and row["total_calls"]:
            cache_hit_rate = (row["cache_hits"] / row["total_calls"] * 100) if row["total_calls"] > 0 else 0
            print(f"Cache hit rate (last 24h): {cache_hit_rate:.1f}% ({row['cache_hits']}/{row['total_calls']} calls)")

    # Error summary
    with get_db() as conn:
        since = int(__import__("time").time()) - (24 * 3600)
        rows = conn.execute(
            "SELECT error_class, COUNT(*) as count FROM metrics WHERE recorded_at >= ? AND success = 0 GROUP BY error_class ORDER BY count DESC",
            (since,)
        ).fetchall()
        if rows:
            print()
            print("Errors (last 24h):")
            for row in rows:
                error_class = row["error_class"] or "unknown"
                print(f"  {error_class:<20} {row['count']}")
    print()


def main():
    ap = argparse.ArgumentParser(description="Display metrics summary")
    ap.add_argument("--hours", type=int, default=24, help="Period in hours")
    ap.add_argument("--ai", default=None, help="Filter by AI type")
    args = ap.parse_args()

    summary = get_metrics_summary(hours=args.hours)

    # Header
    period = f"last {args.hours}h" if args.hours < 24 else f"last {args.hours // 24}d"
    print(f"\nMetrics summary ({period}):")

    format_table(summary, ai_filter=args.ai)


if __name__ == "__main__":
    main()
