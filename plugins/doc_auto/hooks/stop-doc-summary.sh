#!/usr/bin/env bash
# doc_auto Stop Hook — 세션 종료 시 doc 변경 통합 보고서
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/doc-auto.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

STATE_DIR="${PROJECT_ROOT}/.claude/state"
[ -d "$STATE_DIR" ] || exit 0

# 이번 세션의 doc-auto-*.md 모으기
DATE=$(date +%F)
SUMMARY="${STATE_DIR}/session-summary-${DATE}.md"

DOC_FILES=$(find "$STATE_DIR" -name 'doc-auto-*.md' -mtime -1 2>/dev/null)
[ -z "$DOC_FILES" ] && exit 0

{
  echo "# Session Summary — $DATE"
  echo ""
  echo "## doc_auto Pending Updates"
  echo ""
  for f in $DOC_FILES; do
    echo "### $(basename "$f")"
    head -50 "$f"
    echo ""
    echo "---"
    echo ""
  done
} > "$SUMMARY"

echo "[$(date +%F_%T)] summary: $SUMMARY" >> "$LOG"

# 사용자에게는 알림 안 함 (Zero-touch). 로그만.
exit 0
