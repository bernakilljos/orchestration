#!/bin/bash
# Wrapper - calls block-korean-removal.py
# stdin (hook JSON) is forwarded to python script
PY=$(cat "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n') || PY=python
exec "${PY:-python}" "$(dirname "$0")/block-korean-removal.py"
