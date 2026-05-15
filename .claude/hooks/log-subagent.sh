#!/usr/bin/env bash
# SubagentStart/Stop hook — 워커 spawn/finish 자동 메트릭
# record_call.py 와 정합 (route_dispatch.md §5)
set +e

INPUT="$(cat)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_FILE="$PROJECT_ROOT/.claude/logs/subagent.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null

# event 종류 (SubagentStart / SubagentStop)
if command -v jq >/dev/null 2>&1; then
  EVENT="$(echo "$INPUT" | jq -r '.hook_event_name // .event // "unknown"')"
  SUBAGENT_ID="$(echo "$INPUT" | jq -r '.subagent_id // .agent_id // "?"')"
  SUBAGENT_TYPE="$(echo "$INPUT" | jq -r '.subagent_type // .agent_type // .tool_name // "?"')"
  DURATION_MS="$(echo "$INPUT" | jq -r '.duration_ms // .elapsed_ms // 0')"
  TOKENS_IN="$(echo "$INPUT" | jq -r '.tokens_in // .input_tokens // 0')"
  TOKENS_OUT="$(echo "$INPUT" | jq -r '.tokens_out // .output_tokens // 0')"
  SUCCESS="$(echo "$INPUT" | jq -r '.success // .ok // "1"')"
else
  EVENT="?"
  SUBAGENT_ID="?"
  SUBAGENT_TYPE="?"
  DURATION_MS=0
  TOKENS_IN=0
  TOKENS_OUT=0
  SUCCESS=1
fi

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "[$TS] $EVENT | id=$SUBAGENT_ID type=$SUBAGENT_TYPE duration=${DURATION_MS}ms tokens_in=$TOKENS_IN tokens_out=$TOKENS_OUT success=$SUCCESS" >> "$LOG_FILE"

# SubagentStop 이면 metrics DB 에 기록
if [ "$EVENT" = "SubagentStop" ]; then
  RECORD_PY="$PROJECT_ROOT/.claude/scripts/lib/record_call.py"
  if [ -f "$RECORD_PY" ]; then
    python "$RECORD_PY" \
      --ai claude --model "subagent-$SUBAGENT_TYPE" \
      --tokens-in "$TOKENS_IN" --tokens-out "$TOKENS_OUT" \
      --latency-ms "$DURATION_MS" --success "$SUCCESS" \
      --task-id "subagent-$SUBAGENT_ID" 2>/dev/null
  fi
fi
exit 0
