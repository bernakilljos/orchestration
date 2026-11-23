#!/usr/bin/env bash
# MCP 상태 카운트 -> .claude/state/mcp-status.json 갱신
# 사용: SessionStart hook - 사용자 수동 - 주기적 (예: 5분마다)
# R355 (2026-11-23): 실패가 보이면 15초 뒤 1번 재확인 (세션 시작 경합 등 일시 연결 시간 초과가 실패로 굳던 것)
#   · 시작·결과를 .claude/logs/mcp-health.log 에 남김 (백그라운드 재측정이 조용히 사라져도 보이게)
#   · 결과 파일은 임시 파일에 쓰고 옮김 (중간 상태가 읽히지 않게)
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/.claude/state/mcp-status.json"
LOG="$ROOT/.claude/logs/mcp-health.log"
mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] refresh-mcp-status: $*" >> "$LOG" 2>/dev/null || true; }

count() {
  ok=$(printf '%s' "$1" | grep -c "Connected" || true)
  fail=$(printf '%s' "$1" | grep -c "Failed to connect" || true)
  ok=${ok:-0}
  fail=${fail:-0}
}

# check-mcp-health.sh 가 이미 돌린 결과를 넘기면 재사용 (claude mcp list 2회 방지)
if [ -n "${MCP_LIST_OUTPUT:-}" ]; then
  raw="$MCP_LIST_OUTPUT"
else
  log "start"
  raw="$(claude mcp list 2>&1 || true)"
fi
count "$raw"
if [ "$fail" -gt 0 ] && [ -z "${MCP_REFRESH_NO_RETRY:-}" ]; then
  log "실패 ${fail}건 — ${MCP_REFRESH_RETRY_SEC:-15}초 뒤 재확인"
  sleep "${MCP_REFRESH_RETRY_SEC:-15}"
  raw="$(claude mcp list 2>&1 || true)"
  count "$raw"
fi
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
tmp="$OUT.tmp.$$"
cat > "$tmp" <<EOF
{
  "connected": $ok,
  "failed": $fail,
  "timestamp": "$ts"
}
EOF
mv -f "$tmp" "$OUT"
log "connected=$ok failed=$fail"
echo "[mcp-status] connected=$ok failed=$fail"
