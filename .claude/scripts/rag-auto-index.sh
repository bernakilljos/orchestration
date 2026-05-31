#!/usr/bin/env bash
# rag-auto-index.sh — 매일 1회 RAG 인덱스 자동 재빌드
# Trigger: Task Scheduler 또는 SessionStart hook (idempotent)
# 마지막 빌드 후 24h 이상 경과 시만 재빌드 (cost 절약)

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

STAMP=".claude/state/chromadb/.last-build"
mkdir -p "$(dirname "$STAMP")"
LOG=".claude/logs/rag-auto-index.log"
mkdir -p "$(dirname "$LOG")"

NOW=$(date +%s)
LAST=0
[ -f "$STAMP" ] && LAST=$(cat "$STAMP" 2>/dev/null || echo 0)

# 24h = 86400s
DIFF=$((NOW - LAST))
if [ "$DIFF" -lt 86400 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] skip — last build $(( DIFF / 3600 ))h ago" >> "$LOG"
  exit 0
fi

# 동시 실행 방지
LOCK=".claude/state/chromadb/.build.lock"
if [ -f "$LOCK" ]; then
  PID=$(cat "$LOCK" 2>/dev/null || echo "")
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] skip — already building (pid $PID)" >> "$LOG"
    exit 0
  fi
fi
echo $$ > "$LOCK"
trap "rm -f $LOCK" EXIT

echo "[$(date '+%Y-%m-%d %H:%M:%S')] starting index build" >> "$LOG"
PYTHONIOENCODING=utf-8 python .claude/scripts/rag-recall.py --build >> "$LOG" 2>&1
RC=$?

if [ "$RC" -eq 0 ]; then
  echo "$NOW" > "$STAMP"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] build OK" >> "$LOG"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] build FAILED (rc=$RC)" >> "$LOG"
fi
exit 0
