#!/usr/bin/env bash
# SessionStart hook — mHC 워커 활성 검증 (codex-auto · gemini-auto · haiku-auto)
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
mkdir -p "$LOG_DIR"

INACTIVE=""
for worker in codex-auto gemini-auto haiku-auto; do
  PID_FILE="$PROJECT_ROOT/.claude/state/${worker}.pid"
  if [ ! -f "$PID_FILE" ]; then
    INACTIVE="${INACTIVE}${worker} "
  fi
done

if [ -n "$INACTIVE" ]; then
  echo "[check-workers] ⚠ 비활성 워커: $INACTIVE" >> "$LOG_DIR/worker-health.log"
fi

exit 0
