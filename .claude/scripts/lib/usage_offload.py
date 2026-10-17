#!/usr/bin/env python3
"""usage_offload.py — Claude 플랜 사용률(세션·주간)에 따라 일을 codex·gemini 로 넘기는 정본 1곳.

근거 2026-10-17 사용자 지시: «세션 90% 주간 90%면 codex도 시키고 95%이상이면 gemini도 시키자».

단계 (세션 five_hour · 주간 seven_day 중 **높은 쪽** 기준):
  level 0  (< CODEX_PCT)   평소대로
  level 1  (>= CODEX_PCT)  구현·리팩터·단순 작업 -> codex (Claude 는 설계·확인)
  level 2  (>= GEMINI_PCT) 위 + 검증·문서·대량 조사 -> gemini (Claude 는 최종 판단·커밋만)
  설계(design)·애매한 작업은 어느 단계든 Claude 에 남긴다 (D10 Gemini 자동 채택 금지와 정합).

입력: ~/.claude/state/rate-limits.json — statusline_context.py 가 stdin rate_limits 로 쓰는 캐시.
      resets_at 이 지난 키는 이미 풀린 값이라 버린다. 파일이 없으면 level 0 (미측정은 넘기지 않음).
임계: 환경변수 USAGE_OFFLOAD_CODEX_PCT / USAGE_OFFLOAD_GEMINI_PCT 로 조정 (기본 90 / 95).
"""
from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

CODEX_PCT = float(os.environ.get("USAGE_OFFLOAD_CODEX_PCT", "90"))    # BASIS: agreed(2026-10-17 사용자 지시)
GEMINI_PCT = float(os.environ.get("USAGE_OFFLOAD_GEMINI_PCT", "95"))  # BASIS: agreed(2026-10-17 사용자 지시)
RATE_CACHE = Path(os.path.expanduser("~")) / ".claude" / "state" / "rate-limits.json"

LABEL = {"five_hour": "세션", "seven_day": "주간"}

# level 별로 넘기는 작업 종류 -> 대상 AI
OFFLOAD = {
    1: {"implement": "codex", "refactor": "codex", "simple": "codex"},
    2: {"implement": "codex", "refactor": "codex", "simple": "codex",
        "verify": "gemini", "document": "gemini"},
}


def read_usage(path: Path = RATE_CACHE, now: float | None = None) -> dict:
    """{'five_hour': pct, 'seven_day': pct} — 없거나 리셋 지난 키는 빠진다."""
    now = time.time() if now is None else now
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for k, v in ((d or {}).get("rate_limits") or {}).items():
        if k not in LABEL or not isinstance(v, dict):
            continue
        pct = v.get("used_percentage")
        if not isinstance(pct, (int, float)):
            continue
        reset = v.get("resets_at")
        if isinstance(reset, (int, float)) and reset < now:
            continue  # 이미 리셋됨 — 옛 값으로 넘기지 않는다
        out[k] = float(pct)
    return out


def level_of(usage: dict) -> tuple[int, float, str]:
    """(level, 기준 %, 기준 키). 둘 중 높은 쪽."""
    if not usage:
        return 0, 0.0, ""
    key = max(usage, key=lambda k: usage[k])
    pct = usage[key]
    lvl = 2 if pct >= GEMINI_PCT else 1 if pct >= CODEX_PCT else 0
    return lvl, pct, key


def cli_available(ai: str) -> bool:
    return shutil.which(ai) is not None


def offload_target(task_type: str, usage: dict | None = None) -> str | None:
    """이 작업 종류를 넘길 AI ('codex'|'gemini') 또는 None (Claude 유지)."""
    lvl, _, _ = level_of(read_usage() if usage is None else usage)
    ai = OFFLOAD.get(lvl, {}).get(task_type)
    if ai and not cli_available(ai):
        return None
    return ai


def status(usage: dict | None = None) -> dict:
    usage = read_usage() if usage is None else usage
    lvl, pct, key = level_of(usage)
    return {
        "level": lvl,
        "pct": pct,
        "basis": LABEL.get(key, ""),
        "usage": {LABEL[k]: v for k, v in usage.items()},
        "thresholds": {"codex": CODEX_PCT, "gemini": GEMINI_PCT},
        "offload": OFFLOAD.get(lvl, {}),
        "cli": {"codex": cli_available("codex"), "gemini": cli_available("gemini")},
    }


def notice(usage: dict | None = None) -> str:
    """프롬프트 주입 문구 — level 0 이면 빈 문자열."""
    s = status(usage)
    if s["level"] == 0:
        return ""
    use = " · ".join(f"{k} {v:.0f}%" for k, v in s["usage"].items())
    miss = [a for a, ok in s["cli"].items() if not ok]
    tail = f" (CLI 없음: {', '.join(miss)} → 해당 작업은 Claude 유지)" if miss else ""
    if s["level"] == 1:
        body = (f"구현·리팩터·단순 반복은 codex 로 넘겨라 — task-instruction.md 작성 후 "
                f"`python .claude/scripts/auto-dispatch.py` (codex-rules.md). Claude 는 설계·검증·커밋만.")
    else:
        body = (f"구현·리팩터·단순 반복 → codex, 검증·문서·대량 조사 → gemini (task-instruction.md 필수). "
                f"Claude 는 최종 판단·커밋·사용자 답변만. Gemini 결과는 자동 채택 X (D10).")
    return (f"[사용량 위임 L{s['level']}] {use} ≥ {CODEX_PCT if s['level'] == 1 else GEMINI_PCT:.0f}% "
            f"({s['basis']} 기준) — {body}{tail}")


if __name__ == "__main__":
    print(json.dumps(status(), ensure_ascii=False, indent=2))
