#!/usr/bin/env bash
# approval-gate-detect.sh — PreToolUse Bash matcher
# 위험 명령 감지 → approval-gate.py request 등록 (CLAUDE.md § 7-23)
#
# 5 위험 카테고리: data_loss / security / cost / system / irreversible
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/approval-gate.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# stdin
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# command 추출
if command -v jq >/dev/null 2>&1; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  CMD=$(echo "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

[ -z "$CMD" ] && exit 0

GATE="${PROJECT_ROOT}/.claude/scripts/approval-gate.py"
[ -f "$GATE" ] || exit 0

# detect — JSON 출력 또는 빈 출력
DETECT_JSON=$(python "$GATE" detect "$CMD" 2>>"$LOG" || echo "")

# JSON 비어있거나 null 이면 통과
if [ -z "$DETECT_JSON" ] || [ "$DETECT_JSON" = "null" ] || [ "$DETECT_JSON" = "{}" ]; then
  exit 0
fi

# category / description 추출
if command -v jq >/dev/null 2>&1; then
  CATEGORY=$(echo "$DETECT_JSON" | jq -r '.category // empty' 2>/dev/null)
  DESC=$(echo "$DETECT_JSON" | jq -r '.description // empty' 2>/dev/null)
else
  CATEGORY=$(echo "$DETECT_JSON" | grep -oE '"category"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  DESC=$(echo "$DETECT_JSON" | grep -oE '"description"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

[ -z "$CATEGORY" ] && exit 0

# task_id 생성 (cmd sha 앞 12자)
TASK_ID="appr-$(echo -n "$CMD$(date +%s)" | sha256sum 2>/dev/null | cut -c1-12)"
[ -z "$TASK_ID" ] || [ "$TASK_ID" = "appr-" ] && TASK_ID="appr-$(date +%s)"

# request 등록 (4 인자: task_id, command, category, detail)
python "$GATE" request "$TASK_ID" "$CMD" "$CATEGORY" "$DESC" >>"$LOG" 2>&1 || true

echo "[$(date +%F_%T)] BLOCK: $CATEGORY | task_id=$TASK_ID | cmd=$CMD" >> "$LOG"

cat >&2 <<EOF
{
  "decision": "block",
  "reason": "🚨 위험 명령 감지 ($CATEGORY): $DESC. /approve $TASK_ID 또는 /reject $TASK_ID [reason]",
  "systemMessage": "HITL Approval Gate — task_id=$TASK_ID | category=$CATEGORY | /approve <id> 로 승인 후 진행"
}
EOF
exit 2
