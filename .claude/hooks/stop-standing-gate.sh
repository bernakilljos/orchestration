#!/usr/bin/env bash
# Stop hook: ACTIVE Standing Requirements 중 verify FAIL → Stop 차단.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0
"$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/standing-requirements.py" gate 2>/dev/null
exit $?
