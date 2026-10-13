"""detect-repeat-request.sh 이식 — 최근 프롬프트와 키워드 3+ 겹치면 /explainlikeim5 자동 트리거.

상태: .claude/state/prompt-history (최근 10줄 · 300자/줄)
"""
from __future__ import annotations

import os
import re

from _common import append_text, bash_strip, head_bytes, is_loop_prompt, read_lines, write_text

MESSAGE = (
    "[중복 요청 감지 — 유사도 @SCORE@ 키워드 · 3회+ 반복]\n"
    "★ 자동 발동: /explainlikeim5 (5살 톤·일상 비유·짧게 재설명). 사용자가 못 알아들어서 반복 중 = 설명 방식 결함.\n"
    "\n"
    "★ 대응:\n"
    "  1) 지금까지 대응이 부족했는지 인정\n"
    "  2) /explainlikeim5 톤으로 재설명 (고급 용어 금지 · 비유 우선)\n"
    "  3) /loop 자동 발동 검토 (반복 작업 자동화)\n"
    "  4) 감지-강제 시스템 (hook-rule-memory) 이 놓친 부분 실측 후 등재\n"
    "  5) 매번 같은 지적 = 시스템 결함 신호 (사용자 인지 부하 X)\n"
    "\n"
    "관련 룰: .claude/rules/user-emotion.md (3회+ → explainlikeim5)\n"
    "         .claude/rules/consistency.md § 기준 일관성"
)

_KW = re.compile(r"[가-힣a-zA-Z][가-힣a-zA-Z0-9_-]+")


def _kw(t: str) -> set:
    return set(_KW.findall(t))


def run(ctx):
    prompt = bash_strip(head_bytes(ctx.prompt_jq(), 500))
    if not prompt:
        return None
    if is_loop_prompt(prompt):  # /loop·배경 알림은 반복 요청 오탐 방지
        return None

    hist = os.path.join(ctx.project_dir, ".claude", "state", "prompt-history")
    os.makedirs(os.path.dirname(hist), exist_ok=True)

    # 줄바꿈 -> 공백 · 연속 공백 1개 · 300자
    current = re.sub(" +", " ", prompt.replace("\n", " "))[:300]

    # 유사도 — 키워드 상위 10개 vs 최근 5줄 중 처음 3개+ 겹친 줄의 겹침 수
    score = 0
    if os.path.isfile(hist):
        cur = set(sorted(_kw(current))[:10])
        try:
            with open(hist, encoding="utf-8", errors="replace") as f:
                past = f.read().splitlines()[-5:]
        except Exception:
            past = []
        for ln in past:
            n = len(cur & _kw(ln))
            if n >= 3:
                score = n
                break

    # 히스토리 추가 · 최근 10줄만 유지
    append_text(hist, current + "\n")
    lines = read_lines(hist)
    if len(lines) > 10:
        write_text(hist, "\n".join(lines[-10:]) + "\n")

    if score >= 3:
        return MESSAGE.replace("@SCORE@", str(score))
    return None
