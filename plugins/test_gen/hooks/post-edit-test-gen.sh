#!/usr/bin/env bash
# test_gen Hook — PostToolUse Edit/Write
# AI-Native 파이프라인 1단계
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/test-gen.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# stdin 에서 hook input (JSON) 읽기
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# file_path 추출 (jq 우선, fallback grep)
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

[ -z "$FILE_PATH" ] && exit 0

# 확장자 필터 (코드 파일만)
case "$FILE_PATH" in
  *.py|*.js|*.ts|*.tsx|*.jsx|*.go|*.rs)
    ;;
  *)
    exit 0
    ;;
esac

# 테스트 파일 자체는 skip
case "$FILE_PATH" in
  */tests/*|*/__tests__/*|*test_*.py|*.test.*|*.spec.*)
    exit 0
    ;;
esac

echo "[$(date +%F_%T)] trigger: $FILE_PATH" >> "$LOG"

# Chain script 호출 (test_gen → sec_scan → doc_auto)
CHAIN="${PROJECT_ROOT}/.claude/scripts/ai-native-chain.sh"
if [ -x "$CHAIN" ]; then
  "$CHAIN" test_gen "$FILE_PATH" >> "$LOG" 2>&1 &
fi

exit 0
