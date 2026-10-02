#!/usr/bin/env bash
# aggregate-rule-adherence.sh — PostToolUse / UserPromptSubmit 자동 집계 트리거
# TTL 10분 (aggregate-rule-adherence.py 안 체크) · 매 턴 10ms 안쪽
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
# stdin 소비 (hook 규약)
cat >/dev/null 2>&1 || true
python -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/aggregate-rule-adherence.py" >/dev/null 2>&1 &
exit 0
