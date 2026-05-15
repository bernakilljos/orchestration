#!/usr/bin/env bash
# FileChanged hook — plugins/ 변경 시 sync-drift 실시간 점검
# 우리 check-sync-drift.sh 는 SessionStart 만 → 실시간 보강
set +e

INPUT="$(cat)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_FILE="$PROJECT_ROOT/.claude/logs/file-changed.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.file_path // .path // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+' | head -1 | sed 's/.*"\([^"]*\)$/\1/')"
fi

[ -z "$FILE_PATH" ] && exit 0

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "[$TS] changed: $FILE_PATH" >> "$LOG_FILE"

# plugins/ 안 변경만 drift 점검 (다른 변경은 noise)
case "$FILE_PATH" in
  */plugins/*|plugins/*)
    SYNC_SCRIPT="$PROJECT_ROOT/.claude/scripts/sync-plugins.sh"
    [ -f "$SYNC_SCRIPT" ] || exit 0
    RESULT="$(bash "$SYNC_SCRIPT" --check 2>&1 | tail -5)"
    if echo "$RESULT" | grep -qE "drift.*[1-9]|orphan.*[1-9]"; then
      cat <<EOF
{"systemMessage": "[file-changed] plugins/ 변경 → drift/orphan 감지:\n$RESULT\nbash .claude/scripts/sync-plugins.sh 권장"}
EOF
      echo "[$TS] DRIFT detected after $FILE_PATH" >> "$LOG_FILE"
    fi
    ;;
esac
exit 0
