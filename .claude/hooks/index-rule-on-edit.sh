#!/usr/bin/env bash
# index-rule-on-edit.sh — PostToolUse Edit/Write hook
# .claude/rules/, memory/, CLAUDE.md 변경 시 lookup-rule.py 인덱스 자동 rebuild
set -uo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
[ -d "${PROJECT_ROOT}/.claude" ] || exit 0

# 재귀 가드
[ -n "${RULE_INDEX_ACTIVE:-}" ] && exit 0
export RULE_INDEX_ACTIVE=1

# stdin -> file_path
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi
[ -z "$FILE_PATH" ] && exit 0

# 인덱싱 대상 파일만 트리거
case "$FILE_PATH" in
  */.claude/rules/*.md|*CLAUDE.md|*/memory/*.md)
    ;;
  *)
    exit 0
    ;;
esac

# 백그라운드 rebuild
python "${PROJECT_ROOT}/.claude/scripts/lookup-rule.py" --rebuild >> "${PROJECT_ROOT}/.claude/logs/lookup-index.log" 2>&1 &
exit 0
