#!/usr/bin/env bash
# resume-last-24h.sh — SessionStart hook: 최근 24h 작업 자동 복구
# 재부팅·메모리 종료 복구 (사용자 설명 요구 X)
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

OUT="$(python -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/resume-last-24h.py" 2>/dev/null)"
[ -z "$OUT" ] && exit 0

# JSON escape (newline → \n, " → \", backslash → \\)
ESC=$(printf '%s' "$OUT" | python -c "import sys,json; print(json.dumps(sys.stdin.read())[1:-1])")
cat <<EOF
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"$ESC"}}
EOF
exit 0
