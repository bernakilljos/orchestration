#!/usr/bin/env bash
# PreToolUse hook — claude-md-design rule 강제
# CLAUDE.md / AGENTS.md 편집 시 500줄+ 이면 systemMessage 알림
# 차단 안 함 (informational + 권장)
set +e

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')"
  CONTENT="$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
  CONTENT=""
fi

# CLAUDE.md / AGENTS.md / GEMINI.md 만 검사
BASE="$(basename "$FILE_PATH" 2>/dev/null)"
case "$BASE" in
  CLAUDE.md|AGENTS.md|GEMINI.md) ;;
  *) exit 0 ;;
esac

# content 가 비어있으면 file 자체 줄수 (Edit 의 경우)
if [ -n "$CONTENT" ] && [ "$CONTENT" != "null" ]; then
  LINES=$(echo "$CONTENT" | wc -l)
else
  [ -f "$FILE_PATH" ] || exit 0
  LINES=$(wc -l < "$FILE_PATH")
fi

# 500줄+ 이면 warn (CLAUDE.md design rule §5-2 "500줄 이하 유지")
if [ "$LINES" -ge 500 ]; then
  cat <<EOF
{"systemMessage": "[claude-md-size] $BASE 가 ${LINES}줄 — design rule §5-2 (500줄 이하) 권장 초과. 참조 파일로 분리 권장."}
EOF
fi
exit 0
