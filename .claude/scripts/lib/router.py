#!/usr/bin/env python3
"""
router.py — 24/7 quota/budget-aware routing for Orchestration v1.

All tasks are routed before execution. Routes based on:
- Budget breaker state (daily spend limit)
- AI quota exceeded flags
- Task type and token estimate
- Retry count and prior AI choice

Returns RouteDecision with selected AI, thinking budget, caching flag, and fallback chain.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import sys
from pathlib import Path

# Add lib path
sys.path.insert(0, str(Path(__file__).parent))

from state_db import (
    is_breaker_tripped,
    is_quota_exceeded,
    get_metrics_summary,
    check_daily_rollover,
    add_spend,
)
from pricing import estimate_cost, PRICING


class TaskType(str, Enum):
    """Task classification."""
    DESIGN = "design"          # Architecture, design, decisions
    IMPLEMENT = "implement"    # Code implementation
    VERIFY = "verify"          # Validation, review, summary
    DOCUMENT = "document"      # Documentation, research
    REFACTOR = "refactor"      # Code refactoring
    SIMPLE = "simple"          # Template filling, minor edits


class AiChoice(str, Enum):
    """Available AI choices."""
    CLAUDE_OPUS_4_7 = "claude-opus-4-7"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"
    CODEX = "codex"
    GEMINI = "gemini"
    WAIT = "wait"               # Cannot start now
    BREAKER = "breaker"         # Budget exceeded


@dataclass
class RouteDecision:
    """Routing decision output."""
    ai: AiChoice
    use_thinking: bool = False
    thinking_budget: int = 0        # tokens; 0 = no thinking
    use_caching: bool = True        # prompt caching enabled
    worker_count: int = 1           # parallel workers (for codex)
    reason: str = ""                # decision rationale (logs)
    estimated_cost_usd: float = 0.0 # predicted cost
    wait_seconds: int = 0           # WAIT/BREAKER: delay before retry
    fallback_chain: List[AiChoice] = field(default_factory=list)


def route(
    task_type: TaskType,
    estimated_tokens: int,
    is_ambiguous: bool = False,
    retry_count: int = 0,
    prior_ai: Optional[AiChoice] = None,
) -> RouteDecision:
    """
    Route a task to the best available AI.

    Decision logic (in order):
    1. Check budget breaker — if tripped, return BREAKER
    2. Check daily rollover (UTC midnight)
    3. Build quota map (check each AI)
    4. Select preferred AI by task type:
       - DESIGN/REFACTOR/ambiguous -> Opus 4.7 + thinking
       - IMPLEMENT <200 tokens -> Sonnet 4.6
       - IMPLEMENT 200-800k -> Opus 4.7
       - IMPLEMENT >=800k -> Codex (parallel) or Gemini 1M
       - VERIFY -> Haiku 4.5 (default), Gemini if >500k
       - DOCUMENT -> Sonnet 4.6
       - SIMPLE -> Sonnet 4.6
       - retry_count >0 AND prior_ai=(Sonnet/Haiku) -> Opus 4.7
    5. Check preferred AI quota. If exceeded, use fallback_chain.
    6. If all exceeded -> WAIT with backoff
    7. Auto-enable thinking if DESIGN/REFACTOR or ambiguous or retry_count>0

    Args:
        task_type: Classification of task
        estimated_tokens: Estimated input tokens for task
        is_ambiguous: True if task description is unclear
        retry_count: Number of prior attempts
        prior_ai: Which AI was used last (if retry)

    Returns:
        RouteDecision with routing choice and metadata
    """
    check_daily_rollover()

    # Step 1: Check budget breaker
    if is_breaker_tripped():
        return RouteDecision(
            ai=AiChoice.BREAKER,
            reason="Budget breaker is tripped (daily limit exceeded)",
            wait_seconds=3600,
        )

    # Step 2: Build quota availability map
    quota_map = {
        AiChoice.CLAUDE_OPUS_4_7: not is_quota_exceeded("claude-opus-4-7"),
        AiChoice.CLAUDE_SONNET_4_6: not is_quota_exceeded("claude-sonnet-4-6"),
        AiChoice.CLAUDE_HAIKU_4_5: not is_quota_exceeded("claude-haiku-4-5"),
        AiChoice.CODEX: not is_quota_exceeded("codex"),
        AiChoice.GEMINI: not is_quota_exceeded("gemini"),
    }

    # Step 3: Select preferred AI by task type
    preferred_ai = None
    fallback_chain = []
    use_thinking = False
    thinking_budget = 0

    if task_type == TaskType.DESIGN or task_type == TaskType.REFACTOR or is_ambiguous:
        preferred_ai = AiChoice.CLAUDE_OPUS_4_7
        use_thinking = True
        thinking_budget = 8000
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    elif task_type == TaskType.IMPLEMENT:
        if estimated_tokens < 200:
            preferred_ai = AiChoice.CLAUDE_SONNET_4_6
            fallback_chain = [
                AiChoice.CLAUDE_HAIKU_4_5,
                AiChoice.CLAUDE_OPUS_4_7,
            ]
        elif estimated_tokens < 800_000:
            preferred_ai = AiChoice.CLAUDE_OPUS_4_7
            fallback_chain = [
                AiChoice.CODEX,
                AiChoice.GEMINI,
                AiChoice.CLAUDE_SONNET_4_6,
            ]
        else:
            # >=800k: prefer Codex or Gemini
            if quota_map[AiChoice.CODEX]:
                preferred_ai = AiChoice.CODEX
                fallback_chain = [
                    AiChoice.GEMINI,
                    AiChoice.CLAUDE_OPUS_4_7,
                ]
            else:
                preferred_ai = AiChoice.GEMINI
                fallback_chain = [
                    AiChoice.CODEX,
                    AiChoice.CLAUDE_OPUS_4_7,
                ]

    elif task_type == TaskType.VERIFY:
        if estimated_tokens < 500_000:
            preferred_ai = AiChoice.CLAUDE_HAIKU_4_5
            fallback_chain = [
                AiChoice.CLAUDE_SONNET_4_6,
                AiChoice.CLAUDE_OPUS_4_7,
            ]
        else:
            preferred_ai = AiChoice.GEMINI
            fallback_chain = [
                AiChoice.CLAUDE_OPUS_4_7,
                AiChoice.CLAUDE_HAIKU_4_5,
            ]

    elif task_type == TaskType.DOCUMENT:
        preferred_ai = AiChoice.CLAUDE_SONNET_4_6
        fallback_chain = [
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.CLAUDE_OPUS_4_7,
        ]

    elif task_type == TaskType.SIMPLE:
        preferred_ai = AiChoice.CLAUDE_SONNET_4_6
        fallback_chain = [
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.CLAUDE_OPUS_4_7,
        ]

    else:
        # Fallback for unknown type
        preferred_ai = AiChoice.CLAUDE_OPUS_4_7
        use_thinking = True
        thinking_budget = 8000
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    # Step 4: Handle retry logic
    if retry_count > 0 and prior_ai in (
        AiChoice.CLAUDE_SONNET_4_6,
        AiChoice.CLAUDE_HAIKU_4_5,
    ):
        # If smaller model failed, escalate to Opus
        preferred_ai = AiChoice.CLAUDE_OPUS_4_7
        use_thinking = True
        thinking_budget = 4000 if retry_count == 1 else 8000
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    # Step 5: Check preferred AI quota
    selected_ai = None
    if quota_map[preferred_ai]:
        selected_ai = preferred_ai
    else:
        # Walk fallback chain
        for ai in fallback_chain:
            if quota_map[ai]:
                selected_ai = ai
                break

    # Step 6: If all exceeded, return WAIT
    if not selected_ai:
        # Find AI with nearest recovery time
        quota_map_exceeded = {
            ai: is_quota_exceeded(ai.value) for ai in AiChoice
            if ai not in (AiChoice.WAIT, AiChoice.BREAKER)
        }
        wait_seconds = 600  # Default 10 min
        return RouteDecision(
            ai=AiChoice.WAIT,
            reason="All AI quotas exceeded",
            wait_seconds=wait_seconds,
        )

    # Step 7: Estimate cost
    estimated_cost = 0.0
    if selected_ai not in (AiChoice.WAIT, AiChoice.BREAKER):
        estimated_cost = estimate_cost(
            selected_ai.value,
            tokens_in=estimated_tokens,
            tokens_out=int(estimated_tokens * 0.5),  # Conservative estimate
        )

    reason = f"{task_type.value} -> {selected_ai.value}"
    if is_ambiguous:
        reason += " (ambiguous)"
    if use_thinking:
        reason += f" + thinking({thinking_budget})"

    return RouteDecision(
        ai=selected_ai,
        use_thinking=use_thinking,
        thinking_budget=thinking_budget,
        use_caching=True,
        worker_count=4 if selected_ai == AiChoice.CODEX else 1,
        reason=reason,
        estimated_cost_usd=estimated_cost,
        fallback_chain=fallback_chain,
    )


def register_outcome(
    decision: RouteDecision,
    tokens_in: int,
    tokens_out: int,
    success: bool,
    cost_usd: Optional[float] = None,
    cache_hit: bool = False,
    error_class: Optional[str] = None,
    task_id: Optional[str] = None,
) -> None:
    """
    Record task outcome to metrics and budget.

    Automatically:
    - Records metric row with tokens, cost, error_class
    - Updates today_spent_usd via add_spend()
    - Trips breaker if daily limit exceeded
    - Sets quota_exceeded if error_class in (quota, rate_limit)

    Args:
        decision: RouteDecision from route()
        tokens_in: Actual input tokens used
        tokens_out: Actual output tokens generated
        success: True if task completed successfully
        cost_usd: Actual cost (optional; will be calculated if omitted)
        cache_hit: True if prompt cache was hit
        error_class: 'quota' | 'rate_limit' | None
        task_id: Optional task identifier for tracking
    """
    from state_db import (
        record_metric,
        add_spend,
        is_breaker_tripped,
        trip_breaker,
        set_quota_exceeded,
    )
    import time

    # Calculate cost if not provided
    if cost_usd is None:
        cost_usd = estimate_cost(
            decision.ai.value,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

    # Record metric
    record_metric(
        ai=decision.ai.value,
        model_id=decision.ai.value,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        latency_ms=0,
        success=success,
        task_id=task_id,
        cache_hit=cache_hit,
        error_class=error_class,
    )

    # Update budget
    if success and cost_usd > 0:
        add_spend(cost_usd)

    # Handle quota errors
    if error_class in ("quota", "rate_limit"):
        # Expire in 2 hours
        expires_at = int(time.time()) + 7200
        set_quota_exceeded(
            decision.ai.value,
            expires_at=expires_at,
            error_msg=error_class,
        )


if __name__ == "__main__":
    # Test routing
    decision = route(TaskType.DESIGN, 5000)
    print(f"DESIGN (5k tokens): {decision.ai.value}")
    print(f"  Thinking: {decision.use_thinking}, budget={decision.thinking_budget}")
    print(f"  Cost: ${decision.estimated_cost_usd:.4f}")
    print(f"  Reason: {decision.reason}")
    print()

    decision = route(TaskType.IMPLEMENT, 100)
    print(f"IMPLEMENT (100 tokens): {decision.ai.value}")
    print(f"  Reason: {decision.reason}")
    print()

    decision = route(TaskType.VERIFY, 1_000_000)
    print(f"VERIFY (1M tokens): {decision.ai.value}")
    print(f"  Reason: {decision.reason}")
