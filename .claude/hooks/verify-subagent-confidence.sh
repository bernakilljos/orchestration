#!/usr/bin/env bash
# verify-subagent-confidence.sh — SubagentStop
# Subagent 결과에서 confidence ≤ 4 인데 PASS 찍힌 케이스 감지 (failure-mode.md § Failure mode)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/subagent-confidence.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# subagent output (final response 또는 last_message) 추출
if command -v jq >/dev/null 2>&1; then
  OUTPUT=$(echo "$INPUT" | jq -r '.result // .output // .response // empty' 2>/dev/null)
  AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // .id // "unknown"' 2>/dev/null)
else
  OUTPUT=$(echo "$INPUT" | grep -oE '"(result|output|response)"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  AGENT_ID="unknown"
fi

[ -z "$OUTPUT" ] && exit 0

# confidence 추출 (다양한 패턴)
CONFIDENCE=$(echo "$OUTPUT" | grep -oiE 'confidence[^0-9]{0,5}([0-9]+)' | head -1 | grep -oE '[0-9]+' | head -1)
[ -z "$CONFIDENCE" ] && CONFIDENCE=$(echo "$OUTPUT" | grep -oiE '신뢰도[^0-9]{0,5}([0-9]+)' | head -1 | grep -oE '[0-9]+' | head -1)
[ -z "$CONFIDENCE" ] && exit 0

# PASS 라벨 감지
PASS_SIGN=0
echo "$OUTPUT" | grep -qiE '\bPASS\b|통과|[OK]' && PASS_SIGN=1

# Safety 점수 추출 (있으면)
SAFETY=$(echo "$OUTPUT" | grep -oiE 'safety[^0-9]{0,5}([0-9]+)' | head -1 | grep -oE '[0-9]+' | head -1)

echo "[$(date +%F_%T)] agent=$AGENT_ID confidence=$CONFIDENCE pass=$PASS_SIGN safety=${SAFETY:-na}" >> "$LOG"

# 위반: confidence ≤ 4 AND PASS = 허위 PASS
if [ "$CONFIDENCE" -le 4 ] && [ "$PASS_SIGN" = "1" ]; then
  echo "[VIOLATION] confidence=$CONFIDENCE 인데 PASS 찍음 (agent=$AGENT_ID)" >> "$LOG"
  cat <<EOF
{
  "systemMessage": "[WARN] Subagent confidence=$CONFIDENCE 인데 PASS 라벨. failure-mode.md § Failure mode 위반 가능. 재검토 필요."
}
EOF
fi

# Safety ≤ 7 이면 FAIL 강제 (failure-mode.md § PASS/FAIL 룰)
if [ -n "$SAFETY" ] && [ "$SAFETY" -le 7 ] && [ "$PASS_SIGN" = "1" ]; then
  echo "[VIOLATION] safety=$SAFETY 인데 PASS (agent=$AGENT_ID)" >> "$LOG"
  cat <<EOF
{
  "systemMessage": "[WARN] Subagent safety=$SAFETY (≤7) 인데 PASS. failure-mode.md § PASS 자격 미달."
}
EOF
fi

exit 0
