#!/usr/bin/env bash
# session-stop-snapshot.sh — Stop 시 이번 세션 commit·결정·파일변경 자동 캡처
# 2026-10-13 신설 · 목표 A · Agile iteration enhancement

set -o pipefail
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="${PROJECT_DIR}/.claude/state"
LOGS_DIR="${PROJECT_DIR}/.claude/logs"
DB="${PROJECT_DIR}/.claude/state/orca.db"

mkdir -p "$STATE_DIR" "$LOGS_DIR"

LOG_FILE="$LOGS_DIR/session-stop-snapshot.log"
SNAPSHOT_FILE="${STATE_DIR}/session-snapshot-$(date +%Y%m%d-%H%M%S).md"

{
  echo "[$(date -Iseconds)] SessionStop snapshot starting..."

  {
    echo "# Session Stop Snapshot"
    echo ""
    echo "**Date**: $(date -Iseconds)"
    echo ""
    echo "## Git Changes"
    cd "$PROJECT_DIR" || exit 1
    if git rev-parse --git-dir >/dev/null 2>&1; then
      echo "\`\`\`"
      git diff --stat 2>/dev/null || echo "(no changes)"
      echo "\`\`\`"
      echo ""
      echo "### Recent Commits"
      echo "\`\`\`"
      git log --oneline -5 2>/dev/null || echo "(no commits)"
      echo "\`\`\`"
    fi

    echo ""
    echo "## Files Modified This Session"
    # .claude/state/session-files.log 에 기록되어 있다면 조회
    if [ -f "${STATE_DIR}/session-files.log" ]; then
      echo "\`\`\`"
      tail -20 "${STATE_DIR}/session-files.log" 2>/dev/null | awk -F'|' '{print $2, "(" $1 ")"}'
      echo "\`\`\`"
    fi

    echo ""
    echo "## Decisions Logged"
    if [ -f "$DB" ]; then
      sqlite3 "$DB" 2>/dev/null <<EOF || echo "(none)"
SELECT ts, decision_type, summary
FROM decisions
WHERE ts > datetime('now', '-1 hour')
ORDER BY ts DESC
LIMIT 10;
EOF
    fi

    echo ""
    echo "## Tasks Status"
    if [ -f "$DB" ]; then
      sqlite3 "$DB" 2>/dev/null <<EOF || echo "(no tasks)"
SELECT status, COUNT(*) FROM tasks GROUP BY status;
EOF
    fi

  } > "$SNAPSHOT_FILE"

  echo "[$(date -Iseconds)] Snapshot saved: $SNAPSHOT_FILE"

} >> "$LOG_FILE" 2>&1

exit 0
