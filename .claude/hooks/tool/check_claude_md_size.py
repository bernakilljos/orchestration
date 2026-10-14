"""check-claude-md-size.sh 이식 — CLAUDE.md/AGENTS.md/GEMINI.md 편집 시 500줄+ 경고 (비차단).

대상 파일명이 아니면 즉시 통과 (프로세스 0개). 대상이면 원본 스크립트에 위임 (드문 경로).
"""
from __future__ import annotations

from _common import Spawn, bash_basename, bash_cat, grep_key_value_a, has_jq

REL = ".claude/hooks/check-claude-md-size.sh"


def run(ctx):
    if has_jq():
        return Spawn(REL)
    fp = grep_key_value_a(bash_cat(ctx.raw), "file_path")
    if bash_basename(fp) in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        return Spawn(REL)
    return None
