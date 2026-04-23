#!/usr/bin/env python3
"""
Model pricing per 1M tokens (2026-04 basis, USD).
Source: https://docs.anthropic.com/en/docs/about-claude/models
"""

PRICING = {
    "claude-opus-4-7": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.5,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.3,
    },
    "claude-haiku-4-5": {
        "input": 0.8,
        "output": 4.0,
        "cache_write": 1.0,
        "cache_read": 0.08,
    },
    "codex": {
        "input": 2.5,
        "output": 10.0,
        "cache_write": None,
        "cache_read": None,
    },
    "gemini": {
        "input": 0.075,
        "output": 0.3,
        "cache_write": None,
        "cache_read": None,
    },
}


def estimate_cost(
    model: str,
    tokens_in: int,
    tokens_out: int,
    cache_hit_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """
    Calculate USD cost for API call.

    Args:
        model: Model key from PRICING dict
        tokens_in: Input tokens (not counting cache)
        tokens_out: Output tokens
        cache_hit_tokens: Input tokens from cache hit (charged at reduced rate)
        cache_write_tokens: Input tokens added to cache (charged at write rate)

    Returns:
        float: Estimated cost in USD, rounded to 6 decimals
    """
    p = PRICING.get(model)
    if not p:
        return 0.0

    cost = 0.0

    # Regular input tokens (minus cache)
    regular_input = tokens_in - cache_hit_tokens - cache_write_tokens
    if regular_input > 0:
        cost += (regular_input / 1_000_000) * p["input"]

    # Output tokens
    cost += (tokens_out / 1_000_000) * p["output"]

    # Cache write tokens (higher rate)
    if cache_write_tokens > 0 and p["cache_write"]:
        cost += (cache_write_tokens / 1_000_000) * p["cache_write"]

    # Cache hit tokens (lower rate)
    if cache_hit_tokens > 0 and p["cache_read"]:
        cost += (cache_hit_tokens / 1_000_000) * p["cache_read"]

    return round(cost, 6)


if __name__ == "__main__":
    # Quick test
    cost = estimate_cost("claude-opus-4-7", 1000, 500)
    print(f"Opus: 1000 in, 500 out = ${cost:.6f}")

    cost = estimate_cost("claude-sonnet-4-6", 1000, 500)
    print(f"Sonnet: 1000 in, 500 out = ${cost:.6f}")

    cost = estimate_cost("claude-haiku-4-5", 1000, 500)
    print(f"Haiku: 1000 in, 500 out = ${cost:.6f}")
