#!/usr/bin/env bash
# test_gen Hook — PostToolUse Edit/Write
# AI-Native 파이프라인 1단계
set -e

# === KILL SWITCH (leak 방지) ===
PROJECT_ROOT_GUARD="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -f "${PROJECT_ROOT_GUARD}/.claude/state/ai-native-chain.disabled" ]; then
  exit 0
fi

# === RECURSION GUARD ===
# ai-native-chain.sh 가 set 한 env var 가 있으면 = 체인 내부 호출 → 즉시 종료
# (PostToolUse 가 chain 내부 file write 에 재귀하지 않도록)
if [ -n "${AI_NATIVE_CHAIN_ACTIVE:-}" ]; then
  exit 0
fi

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
