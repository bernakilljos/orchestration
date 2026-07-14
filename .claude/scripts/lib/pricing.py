#!/usr/bin/env python3
"""
Model pricing per 1M tokens (2026-07 basis, USD).
Source: https://docs.anthropic.com/en/docs/about-claude/models

tokenizer_factor:
    같은 텍스트가 각 모델의 tokenizer 로 얼마나 많은 토큰을 생성하는지 배수.
    기준 = Opus 4.7 tokenizer (=1.0). Opus 4.7 계열 (Fable 5, Sonnet 5, Mythos 5) 는
    이전 세대 대비 텍스트당 ~30% 더 많은 토큰 → factor=1.3 (2026-07-02 api-release 공지).
    estimate_cost 는 이 factor 를 적용해 실제 청구 토큰을 재산정.
"""

PRICING = {
    # === Opus 4.7 계열 tokenizer (factor 1.0 기준) ===
    "claude-opus-4-7": {
        "input": 15.0,
        "output": 75.0,
        "cache_write": 18.75,
        "cache_read": 1.5,
        "tokenizer_factor": 1.0,
    },
    # === Opus 4.8 (2026-05-28 default, 4.7 대비 저렴) ===
    "claude-opus-4-8": {
        "input": 5.0,
        "output": 25.0,
        "cache_write": 6.25,
        "cache_read": 0.5,
        "tokenizer_factor": 1.0,  # 이전 tokenizer 사용
    },
    # === Fable 5 / Mythos 5 (2026-07-01 RESTORED, Opus 4.7 tokenizer) ===
    "claude-fable-5": {
        "input": 10.0,
        "output": 50.0,
        "cache_write": 12.5,
        "cache_read": 1.0,
        "tokenizer_factor": 1.3,  # 30% 더 많은 토큰
    },
    "claude-mythos-5": {
        "input": 10.0,
        "output": 50.0,
        "cache_write": 12.5,
        "cache_read": 1.0,
        "tokenizer_factor": 1.3,
    },
    # === Sonnet ===
    "claude-sonnet-4-6": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.3,
        "tokenizer_factor": 1.0,
    },
    # === Sonnet 5 (2026-07-02 신규, Opus 4.7 tokenizer → 실효 비용 ~30% ↑) ===
    "claude-sonnet-5": {
        "input": 3.0,
        "output": 15.0,
        "cache_write": 3.75,
        "cache_read": 0.3,
        "tokenizer_factor": 1.3,
    },
    # === Haiku ===
    "claude-haiku-4-5": {
        "input": 0.8,
        "output": 4.0,
        "cache_write": 1.0,
        "cache_read": 0.08,
        "tokenizer_factor": 1.0,
    },
    # === Non-Anthropic ===
    "codex": {
        "input": 2.5,
        "output": 10.0,
        "cache_write": None,
        "cache_read": None,
        "tokenizer_factor": 1.0,
    },
    "gemini": {
        "input": 0.075,
        "output": 0.3,
        "cache_write": None,
        "cache_read": None,
        "tokenizer_factor": 1.0,
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

    # tokenizer_factor 로 실제 청구 토큰 재산정 (Opus 4.7 계열은 텍스트당 ~30% 더 많음)
    factor = p.get("tokenizer_factor", 1.0)
    tokens_in = int(tokens_in * factor)
    tokens_out = int(tokens_out * factor)
    cache_hit_tokens = int(cache_hit_tokens * factor)
    cache_write_tokens = int(cache_write_tokens * factor)

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
    # Smoke test: 1000 in / 500 out per model
    tests = [
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-fable-5",
        "claude-mythos-5",
        "claude-sonnet-5",
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "codex",
        "gemini",
    ]
    print(f"{'model':<22} {'cost (1k in / 500 out)':<26} {'tokenizer_factor'}")
    for m in tests:
        cost = estimate_cost(m, 1000, 500)
        factor = PRICING[m].get("tokenizer_factor", 1.0)
        print(f"{m:<22} ${cost:.6f}                  {factor}")
