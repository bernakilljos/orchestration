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
    """Available AI choices.

    P0b H4 (2026-10-29) · 호환 어댑터 패턴:
      - 기존 enum 멤버는 유지 (하위 호환 · 외부 호출자 깨짐 방지)
      - 신규 모델은 ai-registry.yaml 등록 후 _registry_resolve() 로 접근
      - Router 선택 로직은 ai_registry.preferred_for() 참조 (아래 route())
    """
    CLAUDE_OPUS_4_7 = "claude-opus-4-7"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_HAIKU_4_5 = "claude-haiku-4-5"
    CODEX = "codex"
    GEMINI = "gemini"
    WAIT = "wait"               # Cannot start now
    BREAKER = "breaker"         # Budget exceeded


def _registry_resolve(name: str) -> Optional[AiChoice]:
    """ai-registry 모델명 → AiChoice (호환 어댑터).

    registry 에만 있고 enum 미등록이면 가장 가까운 tier 로 fallback 매핑.
    """
    # 직접 매치
    for choice in AiChoice:
        if choice.value == name:
            return choice
    # tier 기반 fallback
    try:
        from ai_registry import get_model
        m = get_model(name) or {}
        tier = m.get("tier", "")
        if tier in ("default", "fallback", "cost_fallback", "legacy", "mythos_class", "access_gated"):
            return AiChoice.CLAUDE_OPUS_4_7
        if tier == "balanced":
            return AiChoice.CLAUDE_SONNET_4_6
        if tier == "fast_verify":
            return AiChoice.CLAUDE_HAIKU_4_5
        if tier == "long_context":
            return AiChoice.GEMINI
        if tier == "external_coder":
            return AiChoice.CODEX
    except Exception:
        pass
    return None


def registry_preferred(task_type_str: str, tokens: int = 0) -> Optional[AiChoice]:
    """Registry 참조로 preferred AI 반환 (H4 중앙화 helper).

    모델 추가 시 ai-registry.yaml 만 수정하면 자동 반영.
    """
    try:
        from ai_registry import preferred_for, is_available
        name = preferred_for(task_type_str, tokens=tokens)
        if name and is_available(name):
            return _registry_resolve(name)
    except Exception:
        pass
    return None


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
    # P0b H4 (2026-10-29): Registry 우선 참조 (preferred_for) · 미매치 시 기존 로직
    preferred_ai = None
    fallback_chain = []
    use_thinking = False
    thinking_budget = 0

    # H4 중앙화: ai-registry 참조 (preferred + fallback_chain 모두 registry 기반)
    _registry_pref = registry_preferred(task_type.value, estimated_tokens)
    _registry_fb: List[AiChoice] = []
    if _registry_pref:
        try:
            from ai_registry import preferred_for, fallback_chain as _ai_fb
            primary_name = preferred_for(task_type.value, estimated_tokens)
            if primary_name:
                for fb_name in _ai_fb(primary_name, estimated_tokens):
                    resolved = _registry_resolve(fb_name)
                    if resolved and resolved not in _registry_fb and resolved != _registry_pref:
                        _registry_fb.append(resolved)
        except Exception:
            _registry_fb = []

    # P0b H1·H2 fix (2026-10-28): 하드코딩 임계값 (200·500k·800k) 제거
    # ai-registry.yaml routing_thresholds 참조 · 모델 추가 시 YAML 만 수정
    try:
        from ai_registry import get_routing_threshold as _grt, get_thinking_budget as _gtb
        _SMALL = _grt("small_task_tokens") or 2000
        _MEDIUM = _grt("medium_task_tokens") or 20000
        _LARGE = _grt("large_task_tokens") or 200000
        _RECALL = _grt("recall_task_tokens") or 800000
        _THINK_HIGH = _gtb("high") or 8000
        _THINK_MED = _gtb("medium") or 4000
    except Exception:
        # fail-closed to conservative defaults (ai-registry 로드 실패 시 작동 유지)
        _SMALL, _MEDIUM, _LARGE, _RECALL = 2000, 20000, 200000, 800000
        _THINK_HIGH, _THINK_MED = 8000, 4000

    if task_type == TaskType.DESIGN or task_type == TaskType.REFACTOR or is_ambiguous:
        preferred_ai = AiChoice.CLAUDE_OPUS_4_7
        use_thinking = True
        thinking_budget = _THINK_HIGH
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    elif task_type == TaskType.IMPLEMENT:
        if estimated_tokens < _SMALL:
            preferred_ai = AiChoice.CLAUDE_SONNET_4_6
            fallback_chain = [
                AiChoice.CLAUDE_HAIKU_4_5,
                AiChoice.CLAUDE_OPUS_4_7,
            ]
        elif estimated_tokens < _RECALL:
            preferred_ai = AiChoice.CLAUDE_OPUS_4_7
            fallback_chain = [
                AiChoice.CODEX,
                AiChoice.GEMINI,
                AiChoice.CLAUDE_SONNET_4_6,
            ]
        else:
            # >= recall: prefer Codex or Gemini (long context 처리)
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
        # VERIFY 는 Haiku 가 default · 큰 context (recall 이상) 는 Gemini
        if estimated_tokens < _RECALL:
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
        thinking_budget = _THINK_HIGH
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    # Step 4: Handle retry logic (P0b H2 fix · ai-registry thinking_budget 참조)
    if retry_count > 0 and prior_ai in (
        AiChoice.CLAUDE_SONNET_4_6,
        AiChoice.CLAUDE_HAIKU_4_5,
    ):
        # If smaller model failed, escalate to Opus
        preferred_ai = AiChoice.CLAUDE_OPUS_4_7
        use_thinking = True
        thinking_budget = _THINK_MED if retry_count == 1 else _THINK_HIGH
        fallback_chain = [
            AiChoice.CLAUDE_SONNET_4_6,
            AiChoice.CLAUDE_HAIKU_4_5,
            AiChoice.GEMINI,
        ]

    # Step 4.5: Claude 플랜 사용률 위임 (세션·주간 중 높은 쪽 >=90% codex · >=95% gemini 추가)
    #   정본: lib/usage_offload.py. 설계·애매한 작업은 Claude 유지.
    offload_note = ""
    if task_type != TaskType.DESIGN and not is_ambiguous:
        try:
            from usage_offload import offload_target, level_of, read_usage
            tgt = offload_target(task_type.value)
            if tgt:
                tgt_ai = AiChoice(tgt)
                if quota_map[tgt_ai]:
                    lvl, pct, _ = level_of(read_usage())
                    fallback_chain = [preferred_ai] + [a for a in fallback_chain if a not in (preferred_ai, tgt_ai)]
                    preferred_ai = tgt_ai
                    use_thinking, thinking_budget = False, 0
                    offload_note = f" [usage-offload L{lvl} {pct:.0f}%]"
        except Exception:
            pass  # noqa: BLE001 — 사용률 판정 실패 시 평소 라우팅

    # H4 중앙화 적용 (2026-10-29): Registry preferred 가 유효하고 quota OK 면 승격
    # 하드코딩 분기 결과보다 Registry 가 더 최신 (예: Opus 4.7 → Opus 5.5 자동 승격)
    _registry_decided = False
    if _registry_pref and _registry_pref != preferred_ai:
        if _registry_pref in quota_map and quota_map[_registry_pref]:
            # 기존 preferred 를 fallback 맨 앞에 보존
            prev = preferred_ai
            preferred_ai = _registry_pref
            # Registry fallback_chain 사용 · 기존 preferred 를 뒤에 보존
            new_fb = list(_registry_fb)
            if prev not in new_fb:
                new_fb.append(prev)
            fallback_chain = new_fb
            _registry_decided = True

    # Step 5: Check preferred AI quota
    selected_ai = None
    if quota_map.get(preferred_ai, False):
        selected_ai = preferred_ai
    else:
        # Walk fallback chain
        for ai in fallback_chain:
            if quota_map.get(ai, False):
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
    reason += offload_note

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
