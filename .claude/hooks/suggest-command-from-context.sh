#!/usr/bin/env bash
# suggest-command-from-context.sh — UserPromptSubmit hook
# 5중 자동 발동 (2중 패턴·3중 임계·4중 재사용·5중 외부신호)
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
cat >/dev/null 2>&1 || true
python -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/suggest-command-from-context.py" 2>/dev/null
exit 0
