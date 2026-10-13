#!/bin/bash
# track-agent-dispatch.sh — Agent tool 호출 감지 & 진행률 기록
# 발동: PreToolUse Agent (start) / PostToolUse Agent (end)
# 입력: stdin JSON { tool_name, tool_input: { subagent_type, description } }
# 저장: .claude/state/active-agents.json
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_DIR/.claude/state"
LOG_DIR="$PROJECT_DIR/.claude/logs"
mkdir -p "$STATE_DIR" "$LOG_DIR"

ACTIVE_AGENTS_FILE="$STATE_DIR/active-agents.json"
AGENT_MODEL_MAP="$STATE_DIR/agent-model-map.json"

if [ ! -f "$AGENT_MODEL_MAP" ]; then
  cat > "$AGENT_MODEL_MAP" <<'EOF'
{
  "explore": "inherit",
  "plan": "inherit",
  "judge": "claude-haiku-4-5",
  "general-purpose": "inherit",
  "code-reviewer": "inherit",
  "test-runner": "inherit",
  "brainstorming-partner": "inherit",
  "claude": "inherit"
}
EOF
fi

[ ! -f "$ACTIVE_AGENTS_FILE" ] && echo "[]" > "$ACTIVE_AGENTS_FILE"

ACTION="${1:-start}"
export HOOK_STDIN="$(cat 2>/dev/null || echo '{}')"
export HOOK_ACTION="$ACTION"
export HOOK_STATE_FILE="$ACTIVE_AGENTS_FILE"

# Windows Store 스텁 회피
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[ -f "$HERE/find-python.sh" ] && . "$HERE/find-python.sh"
PY="${PYTHON:-python}"

"$PY" - <<'PYEOF' 2>>"$LOG_DIR/track-agent-dispatch.err" || true
import json, os, sys
from datetime import datetime

action = os.environ.get("HOOK_ACTION", "start")
state_file = os.environ["HOOK_STATE_FILE"]
raw = os.environ.get("HOOK_STDIN", "{}")

try:
    hook = json.loads(raw) if raw.strip() else {}
except Exception as e:
    sys.stderr.write(f"[track] json parse: {e}\n")
    sys.exit(0)

tool_name = hook.get("tool_name") or hook.get("toolName") or ""
if tool_name != "Agent":
    sys.exit(0)

tool_input = hook.get("tool_input") or hook.get("toolInput") or {}
agent_id = tool_input.get("subagent_type") or tool_input.get("agent_type") or "unknown"
desc = (tool_input.get("description") or agent_id)[:80]
ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

try:
    with open(state_file, "r", encoding="utf-8") as f:
        agents = json.load(f)
    if not isinstance(agents, list):
        agents = []
except Exception:
    agents = []

if action == "start":
    agents = [a for a in agents if not (a.get("id") == agent_id and not a.get("end_ts"))]
    agents.append({
        "id": agent_id,
        "description": desc,
        "start_ts": ts,
        "end_ts": None,
        "duration_s": 0,
    })
elif action == "end":
    for a in agents:
        if a.get("id") == agent_id and not a.get("end_ts"):
            try:
                start = datetime.strptime(a["start_ts"], "%Y-%m-%dT%H:%M:%SZ")
                end = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                a["duration_s"] = max(0, int((end - start).total_seconds()))
            except Exception:
                a["duration_s"] = 0
            a["end_ts"] = ts
            break
    now = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    kept = []
    for a in agents:
        if a.get("end_ts"):
            try:
                e = datetime.strptime(a["end_ts"], "%Y-%m-%dT%H:%M:%SZ")
                if (now - e).total_seconds() <= 30:
                    kept.append(a)
            except Exception:
                kept.append(a)
        else:
            kept.append(a)
    agents = kept

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(agents, f, indent=2, ensure_ascii=False)
PYEOF

exit 0
