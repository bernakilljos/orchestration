#!/bin/bash
# Hook: PreToolUse — Edit|Write 차단
# config.py, settings.json, main.py 등 핵심 파일 보호
# codex/gemini가 실수로 수정/삭제하는 것 방지

INPUT=$(cat)
TOOL=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | head -1 | cut -d'"' -f4)
FILE=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | head -1 | cut -d'"' -f4)

# 보호 대상 파일 패턴
PROTECTED_FILES=(
  "config.py"
  "settings.json"
  ".claude/settings.json"
  ".claude/settings.local.json"
  "main.py"
  ".env"
  ".env.local"
  "deploy-config.env"
)

if [ -z "$FILE" ]; then
  exit 0
fi

BASENAME=$(basename "$FILE")
RELPATH=$(echo "$FILE" | sed 's|\\|/|g')

for PATTERN in "${PROTECTED_FILES[@]}"; do
  if [[ "$BASENAME" == "$PATTERN" ]] || [[ "$RELPATH" == *"$PATTERN"* ]]; then
    echo "BLOCKED: $BASENAME is a protected file. Do not modify."
    exit 2
  fi
done

exit 0
