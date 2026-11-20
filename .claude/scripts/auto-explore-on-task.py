#!/usr/bin/env python3
# auto-explore-on-task.py — UserPromptSubmit 시 "전체"·"모든"·"전수조사" 키워드 감지 → Explore 추천
# 2026-10-13 신설 · 목표 C · Auto subagent delegation

import os
import sys
import re
from pathlib import Path

PROJECT_DIR = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
LOGS_DIR = Path(PROJECT_DIR) / '.claude/logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / 'auto-explore-on-task.log'

# 트리거 키워드 (전수조사 신호)
# R337 (2026-11-20): '전체'·'모든'·'전부'·'다…확인' 은 일반 지시문 대부분에 걸려 위임 권고가 과잉이었다 → 명시적 전수 읽기 표현만
EXPLORE_TRIGGERS = [
    r'전수\s*조사',
    r'all\s+(files|plugins|hooks)',
    r'scan\s+everything',
    r'100%\s+(read|survey)',
    r'모든\s*파일',
]

def log(msg: str):
    """로그 기록"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        from datetime import datetime
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def detect_explore_trigger(prompt: str) -> bool:
    """프롬프트에서 Explore 트리거 감지"""
    for pattern in EXPLORE_TRIGGERS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return True
    return False

def generate_system_message_injection() -> str:
    """
    systemMessage 로 주입할 추천 텍스트
    (Claude Code v2.1+ 는 systemMessage 수정 지원 · PostToolUse 로 inject)
    """
    return """
## 읽기 조사 위임 검토 (R337 · 자동 위임 아님)

전수 읽기 표현이 보입니다. 위임 여부는 `execution-contract.md § 7` 로 판단하세요:
- 대상 위치를 알거나 파일 수십 개 이하 → Grep·Read 직접이 보통 더 빠름
- 서로 독립인 여러 영역 · 결론만 필요 → Explore (가벼운 모델) · 적은 수부터
- 병렬로 돌려도 N 배 빨라진다고 가정하지 않음 (시작·통합·검증 시간 포함 · R333 실측: 읽기 조사 1건 280초)
"""

if __name__ == '__main__':
    # CLI: auto-explore-on-task.py --check "<prompt>"
    if len(sys.argv) < 2:
        log("[INFO] Usage: auto-explore-on-task.py --check '<prompt>'")
        sys.exit(0)

    if sys.argv[1] == '--check' and len(sys.argv) > 2:
        prompt = sys.argv[2]
        if detect_explore_trigger(prompt):
            log(f"[TRIGGER] Explore agent recommended for: {prompt[:100]}...")
            print(generate_system_message_injection())
        else:
            log(f"[NO-TRIGGER] Explore not needed for: {prompt[:100]}...")
