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
EXPLORE_TRIGGERS = [
    r'\b전체\b',
    r'\b모든\b',
    r'\b전수조사\b',
    r'\ball\s+(files|plugins|hooks)',
    r'\b전부\b',
    r'\b다\b.*\b확인',
    r'\bscan\s+everything\b',
    r'\b100%\s+(read|survey)',
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
## ⚡ Explore Agent Recommendation

Your prompt includes full-survey keywords ("전체", "모든", "전수조사"). Consider delegating to **Explore agent** for:
- Parallel file reading (5+ files)
- Breadth-first pattern discovery
- Quick indexing before deep analysis

**Usage**: Prefix your detailed request with `Agent(Explore, "...")`

This keeps main context clean and speeds up analysis 3-5x.
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
