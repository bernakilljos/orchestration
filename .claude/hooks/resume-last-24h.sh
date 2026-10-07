#!/usr/bin/env bash
# resume-last-24h.sh — SessionStart hook: 최근 24h 자동 복구
# Python 안에서 JSON 직접 반환 (bash pipe cp949 → surrogate 오염 회피)
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
python -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/resume-last-24h.py" --json 2>/dev/null
exit 0
