"""auto-explore-on-task 이식 — "전체"·"모든"·"전수조사" 감지 → Explore agent 추천 (2026-10-13 신설 hook).

원본 settings 줄: bash -c "python auto-explore-on-task.py --check '$(cat)'" 2>/dev/null || true
  · stdin JSON 원문(끝 개행 제거) 이 그대로 프롬프트로 들어갔다 → 같은 값(ctx.raw_stripped) 을 쓴다.
  · 원본은 프롬프트에 작은따옴표가 있으면 셸 따옴표가 깨지고, 내용이 셸 명령으로 해석될 수 있었다.
    in-process 로 옮기며 그 문제는 사라진다 (판정 규칙·문구·로그는 스크립트 것을 그대로 호출).
"""
from __future__ import annotations

from _common import load_script


def run(ctx):
    mod = load_script("auto-explore-on-task")
    if mod is None:
        return None
    prompt = ctx.raw_stripped
    if not prompt:
        return None
    if mod.detect_explore_trigger(prompt):
        mod.log(f"[TRIGGER] Explore agent recommended for: {prompt[:100]}...")
        return mod.generate_system_message_injection() + "\n"
    mod.log(f"[NO-TRIGGER] Explore not needed for: {prompt[:100]}...")
    return None
