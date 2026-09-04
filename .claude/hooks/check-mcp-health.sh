#!/usr/bin/env bash
# check-mcp-health.sh — SessionStart 시 MCP 서버 연결 상태 점검
# 실패한 MCP 자동 재등록 시도
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$PROJECT_DIR/.claude/logs/mcp-health.log"
mkdir -p "$PROJECT_DIR/.claude/logs" 2>/dev/null

TS="$(date '+%Y-%m-%d %H:%M:%S')"

# claude mcp list 실행 + 실패 서버 감지
MCP_OUTPUT=$(claude mcp list 2>&1 || echo "MCP_CHECK_FAILED")

if echo "$MCP_OUTPUT" | grep -q "MCP_CHECK_FAILED"; then
  echo "[$TS] MCP health check failed (claude mcp list error)" >> "$LOG"
  exit 0
fi

# Failed 서버 추출
FAILED=$(echo "$MCP_OUTPUT" | grep "Failed" | grep -oP '^\S+' || true)

if [ -z "$FAILED" ]; then
  echo "[$TS] All MCP servers healthy" >> "$LOG"
  exit 0
fi

echo "[$TS] Failed MCP servers detected:" >> "$LOG"
echo "$FAILED" >> "$LOG"

# 자동 재등록 시도 (알려진 서버만)
for server in $FAILED; do
  case "$server" in
    filesystem)
      claude mcp remove filesystem 2>/dev/null
      claude mcp add filesystem -- cmd /c npx -y @modelcontextprotocol/server-filesystem "%USERPROFILE%" "C:\\pjt" 2>/dev/null
      echo "  -> filesystem re-registered" >> "$LOG"
      ;;
    powerpoint)
      claude mcp remove powerpoint 2>/dev/null
      claude mcp add powerpoint -- cmd /c npx -y powerpoint-mcp-ultimate 2>/dev/null
      echo "  -> powerpoint re-registered" >> "$LOG"
      ;;
    dom-to-pptx)
      claude mcp remove dom-to-pptx 2>/dev/null
      claude mcp add dom-to-pptx -- cmd /c npx -y dom-to-pptx 2>/dev/null
      echo "  -> dom-to-pptx re-registered" >> "$LOG"
      ;;
    figma)
      claude mcp remove figma 2>/dev/null
      claude mcp add figma -- cmd /c npx -y claude-talk-to-figma-mcp 2>/dev/null
      echo "  -> figma re-registered" >> "$LOG"
      ;;
    *)
      echo "  -> $server: unknown, manual fix needed" >> "$LOG"
      ;;
  esac
done

# systemMessage 로 Claude 에게 알림
cat <<MSG

[WARN] [MCP Health] 실패 MCP 서버 감지 + 자동 재등록 시도:
$(echo "$FAILED" | sed 's/^/  - /')

로그: .claude/logs/mcp-health.log

MSG

exit 0
