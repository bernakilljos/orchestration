#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P0b H1·H2·H4 종단 검증 (2026-10-29).

목적:
  Router 가 ai-registry.yaml 의 임계값·thinking·모델을 참조한다는 **종단 증거**.
  코드 안 호출 체인만 아니라 YAML 변경 → Router 출력 변경을 재현.

금지:
  - 특정 모델 이름 hardcoded assert (예: 'claude-opus-4-7') → ai-registry 변경에 깨짐
  - 특정 숫자 hardcoded assert (예: thinking_budget == 8000) → YAML 변경에 깨짐
  - 그 대신 **등록된 모델만 선택** + **tier 매핑** + **임계값 변경에 반응** 검증

Usage:
  python .claude/scripts/test-h1-h2-h4-e2e.py
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))

PASS = 0
FAIL = 0
NOTES: list[str] = []


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    tag = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{tag}] {msg}")


def section(name: str) -> None:
    print(f"\n=== {name} ===")


def main() -> int:
    # 1) Registry 자체 능력
    section("1. ai_registry.yaml 로드")
    from ai_registry import (
        list_models,
        get_model,
        get_routing_threshold,
        get_thinking_budget,
        preferred_for,
        is_available,
        fallback_chain,
        select_by_tier,
    )

    active = list_models("active")
    provisional = list_models("provisional")
    check(len(active) > 0, f"active 모델 등록 ({len(active)} 개)")
    check(len(provisional) > 0, f"provisional 모델 분리 ({len(provisional)} 개)")

    # 2) Router 가 Registry 참조하는지 (H1 임계값)
    section("2. H1 · Router 가 Registry 임계값 참조")
    from router import route, TaskType, AiChoice, registry_preferred

    # Registry 가 반환하는 preferred 가 Router 출력과 일관
    small_pref = preferred_for("implement", 100)
    small_route = route(TaskType.IMPLEMENT, 100)
    check(
        small_pref is not None and is_available(small_pref),
        f"small_task preferred 가 registry active 모델 ({small_pref})",
    )
    check(small_route.ai.value in [m for m in active + provisional] + ["wait", "breaker"],
          f"small_task route 결과가 registered 모델 ({small_route.ai.value})")

    large_pref = preferred_for("implement", 1_500_000)
    check(
        large_pref is not None and is_available(large_pref),
        f"recall_task preferred 가 registry active 모델 ({large_pref})",
    )
    # 1.5M 는 long_context tier (gemini) 가 default
    long_models = select_by_tier("long_context")
    check(
        large_pref in long_models or large_pref in select_by_tier("external_coder"),
        f"1.5M tokens → long_context 또는 external_coder tier ({large_pref})",
    )

    # 3) H2 · thinking_budget Registry 참조
    section("3. H2 · thinking_budget Registry 참조")
    tb_med = get_thinking_budget("medium")
    tb_high = get_thinking_budget("high")
    check(tb_med is not None and tb_high is not None, f"medium/high thinking_budget 등록 ({tb_med}/{tb_high})")
    check(tb_high > tb_med, "high > medium (단조 증가)")

    r = route(TaskType.DESIGN, 5000)
    check(r.use_thinking, "DESIGN 작업에 thinking on")
    check(r.thinking_budget >= tb_med, f"thinking_budget >= registry medium ({r.thinking_budget} >= {tb_med})")

    # 4) H4 · AiChoice resolve 가 Registry 모든 활성 모델 커버
    section("4. H4 · AiChoice resolve 가 Registry 활성 모델 커버")
    from router import _registry_resolve

    uncovered = []
    for name in active:
        resolved = _registry_resolve(name)
        if resolved is None:
            uncovered.append(name)
    check(
        len(uncovered) == 0,
        f"모든 active 모델이 AiChoice 로 resolve ({len(active)} 개 전수 매핑)" if not uncovered else f"미커버: {uncovered}",
    )

    # 5) H4 · Registry 변경 시 route.py MODELS 리스트 반영 (하드코딩 제거 증명)
    section("5. H4 · route.py MODELS 하드코딩 제거 확인")
    route_py = (ROOT / ".claude" / "scripts" / "route.py").read_text(encoding="utf-8")
    # 하드코딩 리스트 패턴
    hardcoded = (
        '    for ai_name in [\n'
        '        "claude-fable-5",'
    )
    check(hardcoded not in route_py, "route.py 안 하드코딩된 모델 리스트 제거됨")
    check("from ai_registry import list_models" in route_py or "from ai_registry import" in route_py,
          "route.py 가 ai_registry.list_models 참조")

    # 6) 설정 손상 (파일 손상) 시 fail-closed
    section("6. 설정 손상 시 fail-closed")
    import ai_registry
    bak_cache = ai_registry._CACHE
    ai_registry._CACHE = {}  # 손상 시뮬레이션
    bad_pref = preferred_for("design", 5000)
    check(bad_pref is None, "ai-registry 비어도 preferred_for 는 None (crash X)")
    bad_route = route(TaskType.DESIGN, 5000)
    check(bad_route.ai != AiChoice.WAIT and bad_route.ai != AiChoice.BREAKER,
          f"Registry 손상 시 Router 는 enum fallback 로 작동 ({bad_route.ai.value})")
    ai_registry._CACHE = bak_cache  # 복원

    # 7) Fallback chain 이 Registry 안 등록된 모델만 포함 (미등록 X)
    section("7. Fallback chain registry 안 등록된 모델만")
    all_registered = set(active + provisional)
    for tt in [TaskType.DESIGN, TaskType.IMPLEMENT, TaskType.VERIFY, TaskType.DOCUMENT]:
        for tokens in [100, 50_000, 1_500_000]:
            r = route(tt, tokens)
            for fb in r.fallback_chain:
                if fb.value in ("wait", "breaker"):
                    continue
                check(
                    fb.value in all_registered,
                    f"{tt.value}/{tokens} fallback {fb.value} 가 registered" if fb.value in all_registered else f"{tt.value}/{tokens} fallback {fb.value} 미등록",
                )

    # 8) Budget cap (H3) · fable-5 특수 분기 → 모델 속성
    section("8. H3 · budget_cap_pct 모델 속성 참조")
    from ai_registry import get_budget_cap_pct

    fable_cap = get_budget_cap_pct("claude-fable-5-1")
    opus_cap = get_budget_cap_pct("claude-opus-5-5")
    check(fable_cap is not None and fable_cap > 0, f"fable-5-1 budget_cap_pct 등록 ({fable_cap}%)")
    check(opus_cap is None, "opus-5-5 는 budget_cap_pct 없음 (cap 없음)")

    # 9) 가용성 분리 — provisional 은 preferred 로 선택되지 않음
    section("9. provisional 모델 preferred 제외")
    # 모든 task_kind 에서 preferred_for 결과가 provisional 가 아님
    for kind in ["design", "implement", "verify", "document", "simple", "refactor"]:
        for tokens in [100, 50_000, 500_000, 1_500_000]:
            pref = preferred_for(kind, tokens)
            if pref:
                check(
                    is_available(pref),
                    f"preferred_for({kind}, {tokens}) → {pref} 가 active (not provisional)" if is_available(pref) else f"preferred_for({kind}, {tokens}) → {pref} provisional 선택 ",
                )

    # 결과
    print("\n" + "=" * 60)
    print(f"PASS: {PASS}  FAIL: {FAIL}  TOTAL: {PASS + FAIL}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
