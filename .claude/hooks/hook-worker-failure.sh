#!/bin/bash
# hook-worker-failure.sh — 워커 실패 시 자동으로 exec_learning JSON에 패턴 기록
#
# 트리거: PostToolUseFailure (Bash), SessionEnd
# 입력: stdin JSON (tool_name, tool_input, tool_response)
# 출력: {"continue": true} + .claude/learning/failure-patterns.json 업데이트

set -euo pipefail

# Windows Store python.exe 스텁 회피
SCRIPT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
source "$SCRIPT_DIR/.claude/hooks/find-python.sh" 2>/dev/null || PYTHON=""

REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LEARNING_DIR="$REPO_ROOT/.claude/learning"
PATTERNS_FILE="$LEARNING_DIR/failure-patterns.json"

mkdir -p "$LEARNING_DIR"

# 입력 파싱
INPUT=$(cat)

# 워커 실패 인지 여부 판단: Bash 도구이고 명령이 codex-auto/gemini-auto/claude-auto 포함
cmd=$(echo "$INPUT" | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    cmd = data.get('tool_input', {}).get('command', '')
    print(cmd)
except Exception:
    pass
" 2>/dev/null || true)

is_worker=false
for keyword in "codex-auto" "gemini-auto" "claude-auto" "orca-dispatch"; do
  if echo "$cmd" | grep -q "$keyword"; then
    is_worker=true
    break
  fi
done

if [ "$is_worker" != "true" ]; then
  # 워커 관련 아님 — 통과
  echo '{"continue": true}'
  exit 0
fi

# 실패 정보 추출
fail_data=$(echo "$INPUT" | python -c "
import json, sys, datetime
try:
    data = json.load(sys.stdin)
    cmd = data.get('tool_input', {}).get('command', '')[:500]
    resp = data.get('tool_response', {})
    stderr = resp.get('stderr', '')[:1000] if isinstance(resp, dict) else ''
    exit_code = resp.get('exit_code', 0) if isinstance(resp, dict) else 0

    entry = {
        'ts': datetime.datetime.utcnow().isoformat() + 'Z',
        'command': cmd,
        'exit_code': exit_code,
        'stderr_snippet': stderr,
        'session': data.get('session_id', 'unknown'),
    }
    print(json.dumps(entry, ensure_ascii=False))
except Exception as e:
    pass
" 2>/dev/null || echo "")

if [ -z "$fail_data" ]; then
  echo '{"continue": true}'
  exit 0
fi

# failure-patterns.json 에 append (JSON lines 형식 추가로 유지)
{
  if [ ! -f "$PATTERNS_FILE" ]; then
    echo '{"failures": []}' > "$PATTERNS_FILE"
  fi

  ${PYTHON:-python} - "$PATTERNS_FILE" "$fail_data" <<'PYEOF'
import json, sys
path = sys.argv[1]
entry = json.loads(sys.argv[2])
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = {"failures": []}
if "failures" not in data:
    data["failures"] = []
data["failures"].append(entry)
# 최근 100개만 유지
data["failures"] = data["failures"][-100:]
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
PYEOF
} 2>/dev/null || true

echo '{"continue": true, "systemMessage": "[learning] 워커 실패 패턴 기록됨"}'
