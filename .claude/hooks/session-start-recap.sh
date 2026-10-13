#!/usr/bin/env bash
# session-start-recap.sh — SessionStart 시 지난 세션 요약 + 미완료 TaskList 자동 조회
# 2026-10-13 신설 · 목표 A · Agile iteration enhancement

set -o pipefail
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
DB="${PROJECT_DIR}/.claude/state/orca.db"
LOGS_DIR="${PROJECT_DIR}/.claude/logs"
STATE_DIR="${PROJECT_DIR}/.claude/state"

# mkdir -p
mkdir -p "$LOGS_DIR" "$STATE_DIR"

LOG_FILE="$LOGS_DIR/session-start-recap.log"

{
  echo "[$(date -Iseconds)] SessionStart recap starting..."

  # 1. 지난 세션 session_summary 조회 (최근 1건)
  if [ -f "$DB" ]; then
    LAST_SUMMARY=$(sqlite3 "$DB" 2>/dev/null <<EOF || echo ""
SELECT session_id, summary, key_decisions, turns
FROM session_summary
ORDER BY updated_at DESC
LIMIT 1;
EOF
)
    if [ -n "$LAST_SUMMARY" ]; then
      echo "[RECAP] Last session summary:"
      echo "$LAST_SUMMARY" | awk -F'|' '{
        print "  Session: " $1
        print "  Turns: " $4
        if ($2 != "") print "  Summary: " substr($2, 1, 200) "..."
        if ($3 != "") print "  Key decisions: " substr($3, 1, 200) "..."
      }'
    fi

    # 2. 미완료 Task 목록 (status != "done")
    PENDING_TASKS=$(sqlite3 "$DB" 2>/dev/null <<EOF || echo ""
SELECT COUNT(*) FROM tasks WHERE status NOT IN ('done', 'archived');
EOF
)
    if [ "$PENDING_TASKS" -gt 0 ]; then
      echo "[RECAP] Pending tasks: $PENDING_TASKS"
      sqlite3 "$DB" 2>/dev/null <<EOF || true
SELECT task_id, status, created_at
FROM tasks
WHERE status NOT IN ('done', 'archived')
ORDER BY created_at DESC
LIMIT 5;
EOF
    fi
  fi

  # 3. systemMessage 주입용 마크다운 생성
  RECAP_MD="${STATE_DIR}/session-recap-current.md"
  {
    echo "## Session Recap"
    echo ""
    echo "Last session:"
    if [ -n "$LAST_SUMMARY" ]; then
      echo "$LAST_SUMMARY" | awk -F'|' '{
        print "- Turns: " $4
        if ($2 != "") print "- Summary: " substr($2, 1, 300)
        if ($3 != "") print "- Key decisions: " substr($3, 1, 300)
      }'
    fi
    echo ""
    echo "Pending tasks: $PENDING_TASKS"
    if [ "$PENDING_TASKS" -gt 0 ]; then
      echo "(See task list in workflow)"
    fi
  } > "$RECAP_MD"

  echo "[$(date -Iseconds)] SessionStart recap complete. Output: $RECAP_MD"

} >> "$LOG_FILE" 2>&1

exit 0
