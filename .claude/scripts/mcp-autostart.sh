#!/usr/bin/env bash
# .claude/scripts/mcp-autostart.sh — Headroom proxy + claude-mem worker 자동 시작
# SessionStart hook 로 등록 (settings.json)
# 원칙: 이미 돌면 skip · 없으면 백그라운드 spawn · 실패 조용 (Zero-touch)

set -eu

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
mkdir -p "$LOG_DIR"

HEADROOM_PORT="${HEADROOM_PORT:-8787}"
CLAUDE_MEM_PORT="${CLAUDE_MEM_WORKER_PORT:-37777}"

# ── Headroom proxy 시작 ───────────────────────────────
if ! curl -sf "http://127.0.0.1:${HEADROOM_PORT}/health" > /dev/null 2>&1; then
  if command -v headroom > /dev/null 2>&1; then
    nohup headroom proxy > "$LOG_DIR/headroom-proxy.log" 2>&1 &
    disown 2>/dev/null || true
    echo "[mcp-autostart] Headroom proxy spawned (port $HEADROOM_PORT · log: $LOG_DIR/headroom-proxy.log)" >&2
  else
    echo "[mcp-autostart] Headroom CLI not found · skip (install: pip install \"headroom-ai[all]\")" >&2
  fi
else
  echo "[mcp-autostart] Headroom proxy already running (port $HEADROOM_PORT)" >&2
fi

# ── claude-mem worker 시작 ────────────────────────────
if ! curl -sf "http://127.0.0.1:${CLAUDE_MEM_PORT}/api/health" > /dev/null 2>&1; then
  if command -v npx > /dev/null 2>&1; then
    nohup npx -y claude-mem start > "$LOG_DIR/claude-mem-worker.log" 2>&1 &
    disown 2>/dev/null || true
    echo "[mcp-autostart] claude-mem worker spawned (port $CLAUDE_MEM_PORT · log: $LOG_DIR/claude-mem-worker.log)" >&2
  else
    echo "[mcp-autostart] npx not found · skip (install: Node.js required)" >&2
  fi
else
  echo "[mcp-autostart] claude-mem worker already running (port $CLAUDE_MEM_PORT)" >&2
fi

exit 0
