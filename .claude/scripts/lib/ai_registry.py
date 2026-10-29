"""AI Registry helper (P0b H3+H4 · 2026-10-28).

중앙 모델 매트릭스 (ai-registry.yaml) 로드 helper. router.py / route.py / classify-task.py
가 참조. 모델 추가·삭제 시 YAML 만 수정 · 코드 수정 X.

제공:
- get_model(name) → dict 또는 None
- is_registered(name) → bool
- get_budget_cap_pct(name) → int or None (fable-5 등 특수 cap)
- get_context_window(name) → int or None
- get_pricing(name) → (input, output) or None
- list_models(availability='active') → list
- get_routing_threshold(key) → int or None
- get_classifier_threshold(key) → int or None
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]  # .claude/scripts/lib/x.py → project root
REGISTRY_PATH = ROOT / ".claude" / "config" / "ai-registry.yaml"

_CACHE: Optional[dict] = None


def _load() -> dict:
    """YAML 로드 · fail-soft (빈 dict · 호출자 fail-closed 처리)."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not REGISTRY_PATH.exists():
        _CACHE = {}
        return _CACHE
    try:
        import yaml  # type: ignore
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            _CACHE = yaml.safe_load(f) or {}
    except ImportError:
        # yaml 미설치 fallback — 간단 파서 (키-값만 지원 · 모델 리스트는 미지원)
        _CACHE = _simple_parse_fallback()
    except Exception:
        _CACHE = {}
    return _CACHE


def _simple_parse_fallback() -> dict:
    """yaml 미설치 시 scaffold fallback — 'is_registered' 만 작동 (model 이름 list)."""
    try:
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        models = {}
        current = None
        for line in text.splitlines():
            if line.startswith("  ") and ":" in line and not line.startswith("    "):
                name = line.strip().rstrip(":").strip()
                if name and not name.startswith("#"):
                    models[name] = {}
                    current = name
        return {"models": models}
    except Exception:
        return {}


def get_model(name: str) -> Optional[dict]:
    """모델 메타 반환 (None = 미등록)."""
    data = _load()
    return data.get("models", {}).get(name)


def is_registered(name: str) -> bool:
    return get_model(name) is not None


def get_budget_cap_pct(name: str) -> Optional[int]:
    """budget_cap_pct (fable-5 등 특수 cap). None = cap 없음."""
    m = get_model(name)
    if not m:
        return None
    v = m.get("budget_cap_pct")
    return int(v) if v is not None else None


def get_context_window(name: str) -> Optional[int]:
    m = get_model(name)
    if not m:
        return None
    v = m.get("context_window")
    return int(v) if v is not None else None


def get_pricing(name: str) -> Optional[tuple]:
    """(input, output) per MTok · None = 미등록."""
    m = get_model(name)
    if not m:
        return None
    i = m.get("pricing_input_per_mtok")
    o = m.get("pricing_output_per_mtok")
    if i is None or o is None:
        return None
    return (float(i), float(o))


def list_models(availability: str = "active") -> list:
    """활성 모델 리스트."""
    data = _load()
    models = data.get("models", {})
    if not availability:
        return list(models.keys())
    return [n for n, m in models.items() if m.get("availability", "active") == availability]


def get_routing_threshold(key: str) -> Optional[int]:
    data = _load()
    v = data.get("routing_thresholds", {}).get(key)
    return int(v) if v is not None else None


def get_classifier_threshold(key: str) -> Optional[int]:
    data = _load()
    v = data.get("classifier", {}).get(key)
    return int(v) if v is not None else None


def get_thinking_budget(level: str) -> Optional[int]:
    data = _load()
    v = data.get("thinking_budget", {}).get(level)
    return int(v) if v is not None else None


def select_by_tier(tier: str, availability: str = "active") -> list:
    """특정 tier 의 모델 리스트 반환 (H4 중앙화 helper)."""
    data = _load()
    out = []
    for name, m in data.get("models", {}).items():
        if m.get("tier") == tier and m.get("availability", "active") == availability:
            out.append(name)
    return out


def select_by_use_case(use_case: str, availability: str = "active") -> list:
    """use_cases 포함 모델 리스트."""
    data = _load()
    out = []
    for name, m in data.get("models", {}).items():
        if use_case in (m.get("use_cases") or []) and m.get("availability", "active") == availability:
            out.append(name)
    return out


def preferred_for(task_kind: str, tokens: int = 0) -> Optional[str]:
    """task kind (design/implement/verify/document/simple/refactor) → preferred model.

    ai-registry.yaml 안 tier/use_cases/context_window 를 참조해 동적 선택.
    모델 추가·삭제 시 YAML 만 수정 (코드 수정 X).

    kind → tier 매핑:
        design, refactor → default (Opus 5.5) → fallback (Opus 5) → cost_fallback (4.8)
        implement <small → balanced (Sonnet) → fast_verify (Haiku)
        implement >=recall → long_context (Gemini) → external_coder (Codex)
        verify <recall → fast_verify (Haiku 5.5·4.5) → balanced (Sonnet)
        verify >=recall → long_context (Gemini) → default (Opus)
        document, simple → balanced (Sonnet) → fast_verify (Haiku)
    """
    small = get_routing_threshold("small_task_tokens") or 2000
    recall = get_routing_threshold("recall_task_tokens") or 800000

    def _first(*tiers: str) -> Optional[str]:
        for t in tiers:
            lst = select_by_tier(t)
            if lst:
                return lst[0]
        return None

    kind = (task_kind or "").lower()
    if kind in ("design", "refactor"):
        return _first("default", "fallback", "cost_fallback")
    if kind == "implement":
        if tokens >= recall:
            return _first("long_context", "external_coder", "default")
        if tokens < small:
            return _first("balanced", "fast_verify")
        return _first("default", "fallback")
    if kind == "verify":
        if tokens >= recall:
            return _first("long_context", "default")
        return _first("fast_verify", "balanced")
    if kind in ("document", "simple"):
        return _first("balanced", "fast_verify")
    # unknown → default
    return _first("default", "fallback")


def is_available(name: str) -> bool:
    """모델이 active 인지 (provisional/unavailable 는 False)."""
    m = get_model(name)
    if not m:
        return False
    return m.get("availability", "active") == "active"


def fallback_chain(primary: str, tokens: int = 0) -> list:
    """primary 외 fallback 리스트 (tier 기반 · 중복 제거)."""
    primary_m = get_model(primary) or {}
    primary_tier = primary_m.get("tier")
    chain = []

    # 같은 tier 다른 모델 (예: default 안 opus-5-5 → opus-5)
    for name in select_by_tier(primary_tier or ""):
        if name != primary and name not in chain:
            chain.append(name)

    # 인접 tier
    tier_order = ["default", "fallback", "cost_fallback", "balanced", "fast_verify", "long_context", "external_coder"]
    try:
        idx = tier_order.index(primary_tier) if primary_tier in tier_order else 0
        for t in tier_order[idx + 1:]:
            for name in select_by_tier(t):
                if name not in chain and name != primary:
                    chain.append(name)
    except (ValueError, IndexError):
        pass

    return chain[:5]  # 최대 5개


# CLI test
if __name__ == "__main__":
    import sys, json
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        print(json.dumps(list_models(), ensure_ascii=False, indent=2))
    elif cmd == "get" and len(sys.argv) > 2:
        print(json.dumps(get_model(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "budget" and len(sys.argv) > 2:
        print(get_budget_cap_pct(sys.argv[2]))
