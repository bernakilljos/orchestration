#!/usr/bin/env bash
# check-mcp-health.sh — MCP 서버 연결 상태 점검 (SessionStart 에서 호출 · 로그 + 상태줄 원천 갱신)
#
# 2026-10-16 수정 (실측 근거):
#   ① `claude mcp list` 는 모든 MCP 서버를 한 번씩 더 띄워 본다 — 한가할 때도 20.2초.
#      SessionStart 에서 바로 돌리면 Claude Code 가 같은 서버를 띄우는 순간 + SessionStart hook 28개와 겹쳐
#      서버 4개가 «30초 연결 시간 초과» 로 실패했다 (단독 기동은 2.5~4.4초). → 60초 뒤 백그라운드에서 점검.
#   ② 서버 이름 추출 정규식이 «playwright:» 처럼 콜론까지 잡아 어떤 복구 분기에도 안 맞았다 (로그 «playwright::»).
#   ③ 복구 분기는 지금 등록되지 않은 서버(filesystem·powerpoint 등)뿐이었고 "C:\pjt" 경로가 박혀 있었다(헌장 A1).
#      → 자동 재등록 삭제. 실패 서버는 로그 + 상태줄(MCP N on M off) 로만 알린다.
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
LOG="$PROJECT_DIR/.claude/logs/mcp-health.log"
mkdir -p "$PROJECT_DIR/.claude/logs" 2>/dev/null

if [ "${1:-}" != "--now" ]; then
  # 세션 시작 경합을 피해 분리 실행 (hook 은 즉시 끝난다)
  DELAY="${MCP_HEALTH_DELAY_SEC:-60}"
  nohup bash -c "sleep $DELAY; bash \"$0\" --now" >/dev/null 2>&1 &
  exit 0
fi

TS="$(date '+%Y-%m-%d %H:%M:%S')"
MCP_OUTPUT=$(claude mcp list 2>&1 || echo "MCP_CHECK_FAILED")

# statusline 의 "MCP N on M off" 원천 (.claude/state/mcp-status.json) 갱신 — 같은 출력 재사용
MCP_LIST_OUTPUT="$MCP_OUTPUT" bash "$PROJECT_DIR/.claude/scripts/refresh-mcp-status.sh" >/dev/null 2>&1 || true

if echo "$MCP_OUTPUT" | grep -q "MCP_CHECK_FAILED"; then
  echo "[$TS] MCP health check failed (claude mcp list error)" >> "$LOG"
  exit 0
fi

# Failed 서버 이름 — «이름: 명령 - ✗ Failed» 에서 첫 «: » 앞까지 (이름에 공백 있는 claude.ai 서버도 그대로)
FAILED=$(echo "$MCP_OUTPUT" | grep "Failed" | sed -E 's/: .*$//' || true)

if [ -z "$FAILED" ]; then
  echo "[$TS] All MCP servers healthy" >> "$LOG"
else
  {
    echo "[$TS] Failed MCP servers detected (60초 지연 점검 — 세션 시작 경합 아님):"
    echo "$FAILED" | sed 's/^/  - /'
  } >> "$LOG"
fi
exit 0
