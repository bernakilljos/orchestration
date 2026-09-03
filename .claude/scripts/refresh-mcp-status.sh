#!/usr/bin/env bash
# MCP 상태 카운트 -> .claude/state/mcp-status.json 갱신
# 사용: SessionStart hook - 사용자 수동 - 주기적 (예: 5분마다)
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/.claude/state/mcp-status.json"
mkdir -p "$(dirname "$OUT")"
raw="$(claude mcp list 2>&1 || true)"
ok=$(printf '%s' "$raw" | grep -c "Connected$" || true)
fail=$(printf '%s' "$raw" | grep -c "Failed to connect$" || true)
ok=${ok:-0}
fail=${fail:-0}
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$OUT" <<EOF
{
  "connected": $ok,
  "failed": $fail,
  "timestamp": "$ts"
}
EOF
echo "[mcp-status] connected=$ok failed=$fail"
