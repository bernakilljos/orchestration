#!/usr/bin/env bash
# auto-smoke-test.sh — PostToolUse Edit/Write hook
# CLAUDE.md § 7-24: DB/API/UI 변경 시 자동 smoke test
# stdin: hook input JSON (tool_input.file_path)
set -uo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"

# Sub-project 가드
[ -d "${PROJECT_ROOT}/.claude" ] || exit 0

# 재귀 가드 (env var)
[ -n "${SMOKE_TEST_ACTIVE:-}" ] && exit 0
export SMOKE_TEST_ACTIVE=1

# stdin JSON 에서 file_path 추출
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0
# 빠른 경로 (1111 §78): 대상 확장자·이름이 입력에 전혀 없으면 jq·grep 없이 끝 (판정 불변 · 상위집합 검사)
case "$INPUT" in
  *.sql*|*ontroller*|*ervice*|*outer*|*.html*|*.jsx*|*.tsx*|*.vue*) ;;
  *) exit 0 ;;
esac

if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi
[ -z "$FILE_PATH" ] && exit 0
FILE_PATH="${FILE_PATH//\\//}"
while [[ "$FILE_PATH" == *//* ]]; do FILE_PATH="${FILE_PATH//\/\//\/}"; done

# 확장자 필터 — DB/API/UI 만
case "$FILE_PATH" in
  *.sql|*Controller.java|*Service.java|*controller*.py|*service*.py|*router*.py|*.html|*.jsx|*.tsx|*.vue)
    ;;
  *)
    exit 0  # smoke test 대상 아님
    ;;
esac

SCRIPT="${PROJECT_ROOT}/.claude/scripts/smoke-test-screen.sh"
[ -x "$SCRIPT" ] || exit 0

# 백그라운드 실행 (PostToolUse 차단 X)
bash "$SCRIPT" "$FILE_PATH" >> "${PROJECT_ROOT}/.claude/logs/smoke-test.log" 2>&1 &

exit 0
