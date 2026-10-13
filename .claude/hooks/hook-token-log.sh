#!/bin/bash
# hook-token-log.sh — 세션 종료 시 토큰 사용 로그 append
#
# 트리거: SessionEnd 훅
# 입력: stdin JSON (session_id 포함)
# 출력: .claude/state/token-usage.jsonl append
#
# 주의: Claude Code 가 토큰 수치를 stdin 으로 제공하지 않으므로 이 훅은
#       **세션 단위 메타데이터** 만 기록. 실제 token 수치는 플랫폼별 수집 필요.
#       (Claude Code /cost 명령 결과 또는 SDK 사용 시 API 응답에서 추출)

set -uo pipefail

# Windows Store python.exe 스텁 회피
SCRIPT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
source "$SCRIPT_DIR/.claude/hooks/find-python.sh" 2>/dev/null || PYTHON=""

REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
STATE_DIR="$REPO_ROOT/.claude/state"
LOG="$STATE_DIR/token-usage.jsonl"

mkdir -p "$STATE_DIR"

# stdin 파싱 (없어도 OK)
INPUT=$(cat 2>/dev/null || echo '{}')

session_id=$(echo "$INPUT" | ${PYTHON:-python} -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', 'unknown'))
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")

ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# JSON Lines append
# 토큰 수치는 N/A (Claude Code 네이티브 export 없음)
${PYTHON:-python} -c "
import json
entry = {
    'ts': '$ts',
    'session': '$session_id',
    'event': 'session_end',
    'tokens': {
        'input': None,
        'output': None,
        'cache_read': None,
        'cache_write': None,
        'note': 'Claude Code does not export via hook; fill via /cost or SDK'
    },
    'est_cost_usd': None
}
print(json.dumps(entry, ensure_ascii=False))
" >> "$LOG" 2>/dev/null || true

echo '{"continue": true}'
