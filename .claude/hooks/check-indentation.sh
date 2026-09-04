#!/usr/bin/env bash
# PostToolUse hook — indentation rule 강제
# md/json/yaml/yml/sh/py 편집 후 탭/스페이스 혼용 검출 -> systemMessage
# 차단 안 함 (informational)
set +e

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
fi

[ -f "$FILE_PATH" ] || exit 0

# 검사 대상 확장자
case "$FILE_PATH" in
  *.md|*.json|*.yaml|*.yml|*.sh) ;;
  *) exit 0 ;;
esac

# 탭과 leading-space 혼용 검출
TAB_LINES=$(grep -cP '^\t' "$FILE_PATH" 2>/dev/null || echo 0)
SP_LINES=$(grep -cP '^  +' "$FILE_PATH" 2>/dev/null || echo 0)

# 둘 다 1+ = 혼용
if [ "$TAB_LINES" -ge 1 ] && [ "$SP_LINES" -ge 1 ]; then
  BASE="$(basename "$FILE_PATH")"
  cat <<EOF
{"systemMessage": "[indent-check] $BASE — 탭 ${TAB_LINES}줄 + 스페이스 ${SP_LINES}줄 혼용 (indentation rule 위반). \`sed -i 's/\\\\t/  /g'\` 권장."}
EOF
fi
exit 0
