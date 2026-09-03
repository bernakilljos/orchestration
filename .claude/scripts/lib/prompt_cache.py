"""
prompt_cache.py — Anthropic prompt caching helper.
시스템 프롬프트-CLAUDE.md-라우팅 룰 같은 반복 컨텍스트를 5분 TTL ephemeral 캐시로 표시.

사용 방식:
  1. build_cached_system() — system 배열 생성 (마지막 블록에 cache_control 추가)
  2. build_cached_messages() — messages 배열에 캐시 분리
  3. estimate_cached_tokens() — 캐시 가능 토큰 추정
  4. cache_control_block() — 단일 블록에 cache_control 붙임
"""

import re
from typing import Literal, Optional


def cache_control_block(text: str, ttl: Literal["5m", "1h"] = "5m") -> dict:
    """
    단일 text 블록에 cache_control 붙여서 반환.

    Args:
        text: 캐시할 텍스트
        ttl: "5m" (ephemeral, 5분) 또는 "1h" (ephemeral, 1시간)

    Returns:
        {"type": "text", "text": "...", "cache_control": {"type": "ephemeral" [, "ttl": "1h"]}}
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("text cannot be empty")

    block = {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"},
    }
    if ttl == "1h":
        block["cache_control"]["ttl"] = "1h"
    return block


def estimate_cached_tokens(blocks: list[str]) -> dict:
    """
    블록별 토큰 추정 (char / 4 근사치).
    Anthropic 캐시 최소 요건: 1024 토큰 이상.

    Args:
        blocks: 텍스트 블록 리스트

    Returns:
        {"total": int, "cacheable": int, "cache_ratio": float, "warnings": [str]}
    """
    total_chars = sum(len(b) if isinstance(b, str) else len(b.get("text", "")) for b in blocks)
    total_tokens = max(1, total_chars // 4)
    cacheable_tokens = total_tokens
    warnings = []

    if cacheable_tokens < 1024:
        warnings.append(
            f"Warning: cacheable tokens ({cacheable_tokens}) < 1024 minimum. "
            "Cache will not be created. Consider combining blocks."
        )

    cache_ratio = (cacheable_tokens / total_tokens) if total_tokens > 0 else 0.0

    return {
        "total": total_tokens,
        "cacheable": cacheable_tokens,
        "cache_ratio": round(cache_ratio, 3),
        "warnings": warnings,
    }


def _is_dynamic(block) -> bool:
    """블록이 dynamic인지 판단 (캐시 제외 대상)."""
    if isinstance(block, dict):
        return block.get("cacheable", False) is False
    # 문자열은 기본 dynamic (안전하게 가정)
    return True


def build_cached_system(blocks: list) -> list[dict]:
    """
    system 배열 생성. 문자열은 자동 text block화.

    마지막 static/cacheable 블록까지를 하나의 cacheable 섹션으로,
    나머지 dynamic 블록들은 뒤에 붙임.

    각 블록은:
      - str: dynamic으로 간주 (안전)
      - dict: {"text": "...", "cacheable": True/False}

    Args:
        blocks: str 또는 dict 블록 리스트

    Returns:
        system 배열 (text block + cache_control)

    Example:
        system = build_cached_system([
            {"text": "You are a code implementation worker.", "cacheable": True},
            read_file("CLAUDE.md"),  # str -> dynamic
            {"text": read_file("route_dispatch.md"), "cacheable": True},
            f"Current task: {task_id}",  # dynamic
        ])
    """
    if not blocks:
        return []

    # 마지막 cacheable 블록 인덱스 찾기
    last_cacheable_idx = -1
    for i in range(len(blocks) - 1, -1, -1):
        block = blocks[i]
        if isinstance(block, dict):
            if block.get("cacheable", False) is not False:
                last_cacheable_idx = i
                break
        # str은 dynamic -> skip

    result = []
    cacheable_text = ""

    # cacheable 블록들 축적
    for i in range(last_cacheable_idx + 1):
        block = blocks[i]
        if isinstance(block, str):
            cacheable_text += block + "\n"
        elif isinstance(block, dict):
            text = block.get("text", "")
            if text:
                cacheable_text += text + "\n"

    # cacheable 섹션을 마지막에 cache_control과 함께 추가
    if cacheable_text.strip():
        result.append(cache_control_block(cacheable_text.rstrip("\n"), ttl="5m"))

    # dynamic 블록들 추가 (캐시 제외)
    for i in range(last_cacheable_idx + 1, len(blocks)):
        block = blocks[i]
        if isinstance(block, str):
            result.append({"type": "text", "text": block})
        elif isinstance(block, dict) and "text" in block:
            result.append({"type": "text", "text": block["text"]})

    return result


def build_cached_messages(
    user_content: str,
    cached_context: Optional[str] = None,
    ttl: Literal["5m", "1h"] = "5m",
) -> list[dict]:
    """
    messages 배열에서 user 메시지의 캐시 분리.

    cached_context는 "이전 대화 요약"이나 "레퍼런스 코드 덩어리" 같은
    static 블록으로, user_content 앞에 붙음.

    Args:
        user_content: 사용자 쿼리 (dynamic)
        cached_context: 선택사항 static 컨텍스트
        ttl: "5m" 또는 "1h"

    Returns:
        messages 배열 (cache_control 포함)
    """
    content_blocks = []

    if cached_context:
        content_blocks.append(cache_control_block(cached_context, ttl=ttl))

    # user_content는 캐시 제외 (dynamic)
    content_blocks.append({"type": "text", "text": user_content})

    return [{"role": "user", "content": content_blocks}]


def extract_cached_tokens_from_response(response_dict: dict) -> dict:
    """
    API 응답에서 캐시 통계 추출.

    Args:
        response_dict: API response (dict 형태)

    Returns:
        {"cache_creation_input_tokens": int, "cache_read_input_tokens": int}
    """
    usage = response_dict.get("usage", {})
    return {
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
    }


def estimate_caching_savings(
    total_calls: int,
    cacheable_tokens_per_call: int,
    total_tokens_per_call: int,
    hours_window: float = 24.0,
) -> dict:
    """
    N시간 동안의 caching 절감률 추정.

    Cache write: cacheable_tokens × 1.25
    Cache hit: cacheable_tokens × 0.1
    Cache miss (5분 후 재생성): cacheable_tokens × 1.25

    Args:
        total_calls: N시간 내 호출 횟수
        cacheable_tokens_per_call: 호출당 캐시 가능 토큰
        total_tokens_per_call: 호출당 전체 토큰
        hours_window: 시간 범위 (기본 24h)

    Returns:
        {
            "total_calls": int,
            "cacheable_tokens_per_call": int,
            "total_tokens_per_call": int,
            "cache_write_cost": float,  # (tokens × 1.25)
            "cache_hit_cost": float,  # (tokens × 0.1)
            "average_cost_per_call": float,
            "savings_ratio": float,
            "notes": str
        }
    """
    # 5분 TTL = 12회 / hour
    # 24시간 = 288회 가능 (5분마다 캐시 갱신 필요)

    cache_write_cost = cacheable_tokens_per_call * 1.25
    cache_hit_cost = cacheable_tokens_per_call * 0.1
    no_cache_cost = cacheable_tokens_per_call * 1.0

    # 초기 write + (N-1) hits 가정
    # 실제: write 후 4분 이내 hit, 5분 후 miss -> new write
    # 보수적으로: 1h당 2회 write (30분마다), 나머지 hit

    writes_per_hour = 2  # 30분마다 새로 write
    total_writes = writes_per_hour * hours_window
    total_hits = max(0, total_calls - total_writes)

    total_cost_with_cache = (total_writes * cache_write_cost) + (total_hits * cache_hit_cost)
    total_cost_without_cache = total_calls * no_cache_cost

    avg_cost_with_cache = total_cost_with_cache / total_calls if total_calls > 0 else 0
    avg_cost_without_cache = no_cache_cost

    savings_ratio = (
        (total_cost_without_cache - total_cost_with_cache) / total_cost_without_cache
        if total_cost_without_cache > 0
        else 0
    )

    return {
        "total_calls": total_calls,
        "cacheable_tokens_per_call": cacheable_tokens_per_call,
        "total_tokens_per_call": total_tokens_per_call,
        "cache_write_cost": round(cache_write_cost, 2),
        "cache_hit_cost": round(cache_hit_cost, 2),
        "total_cost_with_cache": round(total_cost_with_cache, 0),
        "total_cost_without_cache": round(total_cost_without_cache, 0),
        "average_cost_per_call": round(avg_cost_with_cache, 2),
        "savings_ratio": round(savings_ratio, 3),
        "notes": (
            f"Assumption: 2 cache writes/hour (30min TTL margin), rest cache hits. "
            f"With {total_calls} calls over {hours_window}h: "
            f"~{round(savings_ratio*100)}% cost reduction vs no caching."
        ),
    }


if __name__ == "__main__":
    # 간단 테스트
    claude_md = "# CLAUDE.md\n" + ("x" * 4000)
    route_dispatch = "# route_dispatch\n" + ("y" * 3000)

    system = build_cached_system([
        {"text": "You are a code worker.", "cacheable": True},
        {"text": claude_md, "cacheable": True},
        {"text": route_dispatch, "cacheable": True},
        "Current task: test",  # dynamic
    ])

    print("System blocks:", len(system))

    stats = estimate_cached_tokens([claude_md, route_dispatch])
    print("Token stats:", stats)

    savings = estimate_caching_savings(
        total_calls=100,
        cacheable_tokens_per_call=stats["cacheable"],
        total_tokens_per_call=stats["total"],
        hours_window=24,
    )
    print("Savings estimate:", savings)
