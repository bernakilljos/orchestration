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
# 빠른 경로 (1111 §78): 대상 이름이 입력에 전혀 없으면 jq·grep 프로세스를 띄우지 않고 끝 (판정 불변 · 상위집합 검사)
case "$INPUT" in
  *rules*|*CLAUDE.md*|*memory*) ;;
  *) exit 0 ;;
esac

if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi
[ -z "$FILE_PATH" ] && exit 0
FILE_PATH="${FILE_PATH//\\//}"   # Windows 역슬래시 경로도 같은 규칙으로 (종전엔 */.claude/rules/* 에 안 맞아 재색인 안 됨)
while [[ "$FILE_PATH" == *//* ]]; do FILE_PATH="${FILE_PATH//\/\//\/}"; done   # jq 없을 때 JSON 의 \\ 가 // 로 남음

# 인덱싱 대상 파일만 트리거
case "$FILE_PATH" in
  */.claude/rules/*.md|*CLAUDE.md|*/memory/*.md)
    ;;
  *)
    exit 0
    ;;
esac

# 백그라운드 rebuild
PY=$(cat "${PROJECT_ROOT}/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n') || PY=python
"${PY:-python}" "${PROJECT_ROOT}/.claude/scripts/lookup-rule.py" --rebuild >> "${PROJECT_ROOT}/.claude/logs/lookup-index.log" 2>&1 &
exit 0
