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


def usage_from_transcript(path: str):
    """서브에이전트 대화 기록(jsonl)의 assistant 메시지 usage 합 — (입력, 출력, 캐시 읽기, 캐시 쓰기, 모델) · 못 읽으면 None.
    R375 사용자 지시 4 (2026-11-27): SubagentStop 은 사용량을 주지 않아 서브에이전트 631건이 전부 토큰 0(UNKNOWN) 이었다 →
    공식 훅 입력 agent_transcript_path 의 기록에서 실측. 같은 메시지 id 가 여러 줄(스트리밍)로 나오면 마지막 값 1번만 센다."""
    import json
    seen = {}
    model = ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    o = json.loads(ln)
                except ValueError:
                    continue
                msg = o.get("message") if isinstance(o, dict) else None
                if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                    continue
                seen[msg.get("id") or o.get("uuid") or len(seen)] = msg["usage"]
                model = msg.get("model") or model
    except OSError:
        return None
    if not seen:
        return None
    g = lambda k: sum(int((u or {}).get(k) or 0) for u in seen.values())
    return (g("input_tokens"), g("output_tokens"), g("cache_read_input_tokens"), g("cache_creation_input_tokens"), model)


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
    usage_known: bool = True,
    cost_known: bool = True,
) -> float | None:
    """
    Record API call to metrics table and update budget.

    usage_known=False: 토큰·비용을 호출자가 모른다 (예: SubagentStop hook 은 사용량을 받지 못함).
      → cost_usd = NULL (UNKNOWN) 로 저장 · 0 토큰으로 비용을 추정하지 않음 · budget 에 더하지 않음.
      2026-11-02 실측: hook 이 tokens 0 을 넘겨 estimate_cost 가 $0.0 을 만들어 "측정된 0" 으로 보였다.

    Returns: cost_usd of this call (None = UNKNOWN)
    """
    check_daily_rollover()

    if usage_known and not cost_known:
        # 토큰은 실측 · 비용은 모름(구독 요금제는 청구액 아님) → 비용 NULL · 추정 X · budget 반영 X (차단기 오작동 방지)
        record_metric(ai=ai, model_id=model, tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=None,
                      latency_ms=latency_ms, success=success, task_id=task_id, cache_hit=bool(cache_hit_tokens > 0),
                      error_class=error_class if error_class and error_class != "none" else None)
        return None

    if not usage_known:
        record_metric(ai=ai, model_id=model, tokens_in=0, tokens_out=0, cost_usd=None,
                      latency_ms=latency_ms, success=success, task_id=task_id, cache_hit=False,
                      error_class=error_class if error_class and error_class != "none" else None)
        return None

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
    ap.add_argument("--tokens-in", type=int, default=0)
    ap.add_argument("--tokens-out", type=int, default=0)
    ap.add_argument("--usage-unknown", action="store_true",
                    help="토큰·비용 미측정 — cost NULL(UNKNOWN) 저장 · 추정 X · budget 반영 X")
    ap.add_argument("--latency-ms", type=int, required=True)
    ap.add_argument("--success", type=int, required=True, help="1 or 0")
    ap.add_argument("--task-id", default=None)
    ap.add_argument("--cache-hit-tokens", type=int, default=0)
    ap.add_argument("--cache-write-tokens", type=int, default=0)
    ap.add_argument("--error-class", default=None)
    ap.add_argument("--retry", type=int, default=0)
    ap.add_argument("--cost-usd", type=float, default=None)
    ap.add_argument("--usage-from-transcript", default=None,
                    help="서브에이전트 대화 기록 경로 — 토큰 실측 (못 읽으면 --usage-unknown 과 같음) · 비용은 UNKNOWN")

    args = ap.parse_args()
    cost_known = True
    if args.usage_from_transcript:
        u = usage_from_transcript(args.usage_from_transcript)
        if u:
            args.tokens_in = u[0] + u[2] + u[3]          # 입력 = 새 입력 + 캐시 읽기 + 캐시 쓰기 (모델이 실제로 읽은 양)
            args.tokens_out = u[1]
            args.cache_hit_tokens, args.cache_write_tokens = u[2], u[3]
            args.usage_unknown = False
            cost_known = False
        else:
            args.usage_unknown = True

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
        usage_known=not args.usage_unknown,
        cost_known=cost_known,
    )
    cost_txt = "UNKNOWN" if cost is None else f"${cost:.6f}"
    print(f"Recorded: {args.ai}/{args.model} in={args.tokens_in} out={args.tokens_out} cost={cost_txt}")


if __name__ == "__main__":
    main()
