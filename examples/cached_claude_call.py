#!/usr/bin/env python3
"""
Example: Prompt caching을 활용한 Claude API 호출.

Anthropic SDK 사용 (없으면 pip install anthropic 안내).
이 예제는 .claude/scripts/lib/prompt_cache.py를 활용해
시스템 프롬프트와 CLAUDE.md, route_dispatch.md를 캐시합니다.

실행:
  python examples/cached_claude_call.py

(Python 3.8+)
"""

import json
import os
import sys
from pathlib import Path

# 부모 디렉토리 lib 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / ".claude" / "scripts" / "lib"))

from prompt_cache import (
    build_cached_system,
    estimate_cached_tokens,
    estimate_caching_savings,
)


def read_file(path: str) -> str:
    """파일 읽기 (에러 처리 포함)."""
    try:
        p = Path(path)
        if not p.is_absolute():
            p = project_root / p
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"[Error reading {path}: {e}]"


def main():
    """메인 예제."""
    print("=" * 70)
    print("Prompt Caching Example — Orchestration v1")
    print("=" * 70)

    # 1. 캐시할 파일들 로드
    print("\n[Step 1] Loading cacheable files...")

    system_prompt = "You are an expert code implementation worker in the Orchestration v1 kit."
    claude_md = read_file("CLAUDE.md")
    route_dispatch = read_file("plugins/exec_orch/skills/route_dispatch.md")

    print(f"  - System prompt: {len(system_prompt)} chars")
    print(f"  - CLAUDE.md: {len(claude_md)} chars")
    print(f"  - route_dispatch.md: {len(route_dispatch)} chars")

    # 2. 캐시 시스템 구성
    print("\n[Step 2] Building cached system...")

    system = build_cached_system([
        {"text": system_prompt, "cacheable": True},
        {"text": claude_md, "cacheable": True},
        {"text": route_dispatch, "cacheable": True},
        "Current session: example demo",  # dynamic (cache 안 됨)
    ])

    print(f"  System blocks: {len(system)}")
    for i, block in enumerate(system):
        if "cache_control" in block:
            chars = len(block.get("text", ""))
            print(f"    Block {i}: {chars} chars [CACHED]")
        else:
            chars = len(block.get("text", ""))
            print(f"    Block {i}: {chars} chars (dynamic)")

    # 3. 토큰 추정
    print("\n[Step 3] Estimating tokens...")

    stats = estimate_cached_tokens([claude_md, route_dispatch])
    print(f"  Total tokens: {stats['total']}")
    print(f"  Cacheable tokens: {stats['cacheable']}")
    print(f"  Cache ratio: {stats['cache_ratio']:.1%}")

    for warning in stats.get("warnings", []):
        print(f"  ⚠️  {warning}")

    # 4. 비용 절감 시뮬레이션
    print("\n[Step 4] Cost savings estimate (24h × 100 tasks)...")

    savings = estimate_caching_savings(
        total_calls=100,
        cacheable_tokens_per_call=stats["cacheable"],
        total_tokens_per_call=stats["total"],
        hours_window=24,
    )

    print(f"  Total calls: {savings['total_calls']}")
    print(f"  Cache write cost: {savings['cache_write_cost']:.2f} (per call)")
    print(f"  Cache hit cost: {savings['cache_hit_cost']:.2f} (per call)")
    print(f"  Average cost: {savings['average_cost_per_call']:.2f} (with caching)")
    print(f"  Savings ratio: {savings['savings_ratio']:.1%}")
    print(f"\n  📊 {savings['notes']}")

    # 5. Request body 덤프 (SDK 없을 때 직접 호출 가능)
    print("\n[Step 5] Request body structure...")

    request_body = {
        "model": "claude-opus-4-7",
        "max_tokens": 1024,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is the current task in .claude/tasks/?"}
                ],
            }
        ],
    }

    print("  Sample request body (system section only):")
    print(f"  {{\n    'model': '{request_body['model']}',")
    print(f"    'max_tokens': {request_body['max_tokens']},")
    print(f"    'system': [")
    for block in request_body["system"]:
        if "cache_control" in block:
            text_preview = block["text"][:50].replace("\n", "\\n")
            print(
                f"      {{'type': 'text', 'text': '{text_preview}...', "
                f"'cache_control': {block['cache_control']}}}"
            )
        else:
            text_preview = block["text"][:50].replace("\n", "\\n")
            print(f"      {{'type': 'text', 'text': '{text_preview}...'}}")
    print(f"    ],")
    print(f"    'messages': [...]\n  }}")

    # 6. Anthropic SDK로 실제 호출 (있으면)
    print("\n[Step 6] Attempting API call (requires anthropic SDK)...")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        print("  SDK found. Sending request...")

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=256,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": "Summarize the Orchestration v1 kit purpose in 2 sentences.",
                }
            ],
        )

        print("\n  ✅ Response received:")
        print(f"  {response.content[0].text[:200]}...")

        # Cache 통계 출력
        if hasattr(response, "usage"):
            usage = response.usage
            print(f"\n  Cache statistics:")
            print(f"    Input tokens: {usage.input_tokens}")
            print(f"    Cache creation tokens: {getattr(usage, 'cache_creation_input_tokens', 0)}")
            print(f"    Cache read tokens: {getattr(usage, 'cache_read_input_tokens', 0)}")
            print(f"    Output tokens: {usage.output_tokens}")

            if getattr(usage, "cache_creation_input_tokens", 0) > 0:
                print(f"\n  💾 First call: Cache created ({getattr(usage, 'cache_creation_input_tokens', 0)} tokens)")
                print(f"     Run the script again within 5 minutes to see cache hit!")

    except ImportError:
        print("  ❌ anthropic SDK not found.")
        print("     Install: pip install anthropic")
        print("     Set: export ANTHROPIC_API_KEY='sk-...'")
        print("\n  You can still use the request body above with requests or curl:")
        print("     curl -X POST https://api.anthropic.com/v1/messages \\")
        print("       -H 'x-api-key: $ANTHROPIC_API_KEY' \\")
        print("       -H 'content-type: application/json' \\")
        print("       -d @request.json")

    except anthropic.APIError as e:
        print(f"  ❌ API error: {e}")

    print("\n" + "=" * 70)
    print("Example complete. See docs/caching-strategy.md for details.")
    print("=" * 70)


if __name__ == "__main__":
    main()
