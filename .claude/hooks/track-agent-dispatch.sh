#!/bin/bash
# track-agent-dispatch.sh — Agent tool 호출 감지 & 진행률 기록
# 발동: PreToolUse (Agent tool 시작) / PostToolUse (완료)
# 저장: .claude/state/active-agents.json

set -euo pipefail

# 프로젝트 디렉토리 확인
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
[ -d "$PROJECT_DIR" ] || exit 0

STATE_DIR="$PROJECT_DIR/.claude/state"
mkdir -p "$STATE_DIR"

ACTIVE_AGENTS_FILE="$STATE_DIR/active-agents.json"
AGENT_MODEL_MAP="$STATE_DIR/agent-model-map.json"

# 신규 agent-model-map.json 초기화 (없으면)
if [ ! -f "$AGENT_MODEL_MAP" ]; then
  cat > "$AGENT_MODEL_MAP" <<'EOF'
{
  "explore": "inherit",
  "plan": "inherit",
  "judge": "claude-haiku-4-5",
  "general-purpose": "inherit",
  "code-reviewer": "inherit",
  "test-runner": "inherit"
}
EOF
fi

# 신규 active-agents.json 초기화 (없으면)
if [ ! -f "$ACTIVE_AGENTS_FILE" ]; then
  echo "[]" > "$ACTIVE_AGENTS_FILE"
fi

# 입력 JSON에서 tool 정보 파싱
# TOOL_NAME, TOOL_TYPE, AGENT_ID, AGENT_DESC 환경변수 기대
if [ -z "${TOOL_NAME:-}" ] || [ "$TOOL_TYPE" != "agent" ]; then
  exit 0
fi

AGENT_ID="${AGENT_ID:-unknown}"
AGENT_DESC="${AGENT_DESC:-$AGENT_ID}"
ACTION="${1:-start}"  # start 또는 end
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")

# active-agents.json 임시 파일로 업데이트
TEMP_FILE="$ACTIVE_AGENTS_FILE.tmp.$$"
trap "rm -f '$TEMP_FILE'" EXIT

if [ "$ACTION" = "start" ]; then
  # Agent 시작: 배열에 항목 추가
  python3 <<PYTHON 2>/dev/null || true
import json
import sys

try:
    with open("$ACTIVE_AGENTS_FILE", "r") as f:
        agents = json.load(f)
except:
    agents = []

# 중복 제거 (같은 agent_id)
agents = [a for a in agents if a.get("id") != "$AGENT_ID"]

# 신규 항목 추가
agents.append({
    "id": "$AGENT_ID",
    "description": "$AGENT_DESC",
    "start_ts": "$TS",
    "end_ts": None,
    "duration_s": None
})

with open("$TEMP_FILE", "w") as f:
    json.dump(agents, f, indent=2, ensure_ascii=False)
PYTHON
  mv "$TEMP_FILE" "$ACTIVE_AGENTS_FILE" 2>/dev/null || true

elif [ "$ACTION" = "end" ]; then
  # Agent 완료: 항목 업데이트
  python3 <<PYTHON 2>/dev/null || true
import json
from datetime import datetime

try:
    with open("$ACTIVE_AGENTS_FILE", "r") as f:
        agents = json.load(f)
except:
    agents = []

# 해당 agent 찾아서 end_ts 설정
for agent in agents:
    if agent.get("id") == "$AGENT_ID":
        if agent.get("start_ts"):
            try:
                start = datetime.fromisoformat(agent["start_ts"].replace("Z", "+00:00"))
                end = datetime.fromisoformat("$TS".replace("Z", "+00:00"))
                duration = (end - start).total_seconds()
                agent["end_ts"] = "$TS"
                agent["duration_s"] = max(0, int(duration))
            except:
                pass
        break

# 오래된 항목 정리 (30초 이상 지난 완료 항목)
now = datetime.fromisoformat("$TS".replace("Z", "+00:00"))
cleaned = []
for agent in agents:
    if agent.get("end_ts"):
        try:
            end = datetime.fromisoformat(agent["end_ts"].replace("Z", "+00:00"))
            if (now - end).total_seconds() <= 30:
                cleaned.append(agent)
        except:
            cleaned.append(agent)
    else:
        cleaned.append(agent)
agents = cleaned

with open("$TEMP_FILE", "w") as f:
    json.dump(agents, f, indent=2, ensure_ascii=False)
PYTHON
  mv "$TEMP_FILE" "$ACTIVE_AGENTS_FILE" 2>/dev/null || true
fi

exit 0
