"""MoE 자동 입력 분류기 — 사용자 메시지 -> 최적 AI 자동 결정.

규칙 기반 (LLM 호출 X) — 빠르고 결정론적.
출력: {"ai": "claude|codex|gemini|haiku", "reason": "...", "task_type": "..."}
"""
import sys
import re
import json
from typing import Optional


# 분류 규칙 (정규식 + 우선순위)
# 2026-10-16 외부 감사 결함 #3 수정 — Codex 트리거 확장 (명시/3+파일/300줄+/반복/코드 리뷰)
RULES = [
    # 사용자 Codex 명시 (최우선) · 한글 조사 대응 (2026-10-16 R13 결함 수정)
    {
        "task_type": "codex_explicit",
        "ai": "codex",
        "patterns": [
            r"[Cc]odex(?:로|으로|에게|한테|시켜|써|로서|보고)",
            r"(?:로|으로|시켜|써)\s*[Cc]odex",
            r"[Cc]odex\s+(?:실행|호출|구현|검증|리뷰|review|verify|dispatch)",
        ],
        "reason": "사용자가 Codex 명시 -> 즉시 Codex 위임 (orchestrator 자동 dispatch)",
    },
    # 코드 대량 구현 -> Codex (확장: 3+파일/300줄+/반복)
    {
        "task_type": "code_implementation",
        "ai": "codex",
        "patterns": [
            r"(\d{3,}|300\+|500\+|대량|batch)\s*(줄|line|file|파일)",
            r"(refactor|리팩토링|마이그레이션|migration)",
            r"(전체|모든|all)\s*(파일|file|폴더|directory).*(?:수정|편집|edit|update)",
            r"(3|4|5|여러|multiple)\s*(개|\+)?\s*(파일|file|페이지|page).*(?:구현|수정|작성|만들|생성)",
            r"(반복|repeat|동일한?)\s*(패턴|pattern|구현|작성|설정).*(?:×|x|여러)",
            r"(독립.*(?:리뷰|검증)|code\s*review|코드\s*리뷰)",
            r"(공통화|중앙화|dedupe|통합|리팩터).*(?:필요|해줘|작업|진행)",
        ],
        "reason": "3+파일/300줄+/반복패턴/공통화 -> Codex 자동 dispatch (orchestrator 호출)",
    },
    # 장문/멀티모달 -> Gemini Flash
    {
        "task_type": "long_context_or_multimodal",
        "ai": "gemini",
        "patterns": [
            r"(>?500k|장문|long\s*context|전체\s*책|whole\s*book)",
            r"(이미지|image|pdf|docx)\s*(\d+\s*장|분석|analyze)",
            r"(영상|video|youtube)\s*(분석|요약)",
        ],
        "reason": "장문 (>500k 토큰) 또는 멀티모달 (이미지-PDF) -> Gemini Flash",
    },
    # 빠른 검증-점수-요약 -> Haiku
    {
        "task_type": "fast_verify_or_score",
        "ai": "haiku",
        "patterns": [
            r"(검증|verify|점수|score|판정|judge)\s*\d+\s*(건|개|item)",
            r"(빠른|fast|quick)\s*(요약|summarize)",
            r"(분류|classify|매칭|match|필터|filter)",
        ],
        "reason": "빠른 검증-점수-요약-분류 -> Haiku 4.5 + prompt cache 90%↓",
    },
    # 설계-복잡 추론-결정 -> Claude (default fallback)
]

DEFAULT = {
    "ai": "claude",
    "task_type": "design_or_complex_reasoning",
    "reason": "기본 — 설계-복잡 추론-결정-도구 호출은 Claude (Extended Thinking 1M ctx)",
}


def classify(message: str) -> dict:
    """사용자 메시지 -> AI 자동 분류."""
    for rule in RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, message, re.IGNORECASE):
                return {
                    "ai": rule["ai"],
                    "task_type": rule["task_type"],
                    "reason": rule["reason"],
                    "matched_pattern": pattern,
                }
    return {**DEFAULT, "matched_pattern": None}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # stdin 또는 example
        if not sys.stdin.isatty():
            msg = sys.stdin.read().strip()
        else:
            print("usage: classify-task.py '<사용자 메시지>'")
            print("       또는 echo '메시지' | classify-task.py")
            sys.exit(2)
    else:
        msg = " ".join(sys.argv[1:])

    result = classify(msg)
    print(json.dumps(result, ensure_ascii=False, indent=2))
