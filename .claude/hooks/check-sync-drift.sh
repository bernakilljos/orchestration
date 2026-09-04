#!/usr/bin/env bash
# SessionStart hook — sync-workflow rule 강제 자동 점검
# plugins/ ↔ .claude/ drift / orphan 백그라운드 로그
# 실패해도 차단 안 함 (informational only)
set +e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
LOG_FILE="$LOG_DIR/sync-drift.log"
SYNC_SCRIPT="$PROJECT_ROOT/.claude/scripts/sync-plugins.sh"

[ -f "$SYNC_SCRIPT" ] || exit 0
mkdir -p "$LOG_DIR" 2>/dev/null

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
RESULT="$(bash "$SYNC_SCRIPT" --check 2>&1 | tail -10)"

# drift 또는 orphan 감지 시 systemMessage (informational)
if echo "$RESULT" | grep -qE "drift.*[1-9]|orphan.*[1-9]"; then
  cat <<EOF
{"systemMessage": "[sync-drift] plugins/ <-> .claude/ 드리프트-orphan 감지 — bash .claude/scripts/sync-plugins.sh 권장:\n$RESULT"}
EOF
  echo "[$TS] DRIFT|ORPHAN detected" >> "$LOG_FILE"
  echo "$RESULT" >> "$LOG_FILE"
else
  echo "[$TS] clean" >> "$LOG_FILE"
fi
exit 0
