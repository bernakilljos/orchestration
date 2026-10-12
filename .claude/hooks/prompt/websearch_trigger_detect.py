"""websearch-trigger-detect.sh 이식 — 최신 정보·가격·비교 등 트리거 어휘 감지 -> WebSearch 권장.

주의 (원본 동일): 프롬프트가 아니라 stdin JSON 원문 전체에서 매칭한다.
"""
from __future__ import annotations

from _common import search

TRIGGERS = "최신|신기능|신기술|changelog|릴리스|릴리즈|업데이트|얼마|응시료|가격|출시|발표|공개|요즘|트렌드|동향|화제|Opus 5|Sonnet 5|GPT-5|Gemini 3|Llama 4|Claude Code v2|어떤 게 좋|비교|vs|조사|찾아봐|알아봐|리서치|확인해봐|있나|존재|모르겠|궁금|뭐가 있|언제|어디|공식|문서|docs|레퍼런스|benchmark|점수|순위|리뷰|후기|평가"
MESSAGE = "[SIG] WebSearch 자동 발동 권장 - auto-websearch.md 룰 트리거 감지 (최신 정보-모델-가격-비교 등). WebSearch tool 로 확인 후 답변하세요. 출처 명시 필수."


def run(ctx):
    if not ctx.has_plugins():
        return None
    if search(TRIGGERS, ctx.raw_stripped):
        return MESSAGE
    return None
