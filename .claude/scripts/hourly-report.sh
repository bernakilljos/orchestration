#!/usr/bin/env bash
# hourly-report.sh — 1시간마다 진행상황 보고
# 출력: docs/hourly-reports/YYYY-MM-DD_HH00.md
# Trigger: Task Scheduler (Windows) 또는 cron

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

OUT_DIR="docs/hourly-reports"
mkdir -p "$OUT_DIR" 2>/dev/null
TS_FILE="$(date '+%Y-%m-%d_%H00')"
TS_HUMAN="$(date '+%Y-%m-%d %H:%M:%S')"
OUT="$OUT_DIR/${TS_FILE}.md"

{
  echo "# 1시간 보고 — $TS_HUMAN"
  echo
  echo "## 1) 워커 상태"
  echo
  echo "### heartbeat 파일"
  ls -la "$HOME/.claude/orca/workers/" 2>/dev/null | tail -n +2 | head -10 || echo "(없음)"
  echo
  echo "### 프로세스"
  tasklist 2>/dev/null | grep -iE "codex|gemini|claude\." | head -10 || echo "(없음)"
  echo
  echo "## 2) 전역 큐"
  echo
  echo "### 대기 task"
  ls "$HOME/.claude/orca/tasks/" 2>/dev/null | head -10 || echo "(없음)"
  echo
  echo "### 완료 task"
  ls "$HOME/.claude/orca/done/" 2>/dev/null | tail -10 || echo "(없음)"
  echo
  echo "## 3) git 진행 (최근 1h)"
  echo
  echo '```'
  git log --since='1 hour ago' --pretty=format:'%h %ad %s' --date=format:'%H:%M' 2>/dev/null | head -20 || echo "(없음)"
  echo
  echo '```'
  echo
  echo "## 4) 최근 변경 파일 (1h)"
  echo
  echo '```'
  find . -type f -mmin -60 \( -name "*.tsx" -o -name "*.py" -o -name "*.html" -o -name "*.md" -o -name "*.json" -o -name "*.sql" \) ! -path "./node_modules/*" ! -path "./.git/*" ! -path "./.claude/logs/*" ! -path "./.claude/state/*" 2>/dev/null | head -20 || echo "(없음)"
  echo '```'
  echo
  echo "## 5) Flask + 터널 상태"
  curl -sS -o /dev/null -w "Flask 5000: %{http_code}\n" --max-time 3 http://127.0.0.1:5000 2>&1 || echo "Flask: DOWN"
  if [ -f data/tunnel_url.txt ]; then
    URL=$(cat data/tunnel_url.txt 2>/dev/null | head -1)
    echo "Tunnel: $URL"
    curl -sS -o /dev/null -w "Tunnel: %{http_code}\n" --max-time 8 -L "$URL" 2>&1 || echo "Tunnel: DOWN"
  fi
  echo
  echo "## 6) 메모리-디스크"
  echo '```'
  ps -W 2>/dev/null | awk 'NR>1{ram+=$5}END{printf "Total RAM: %.1f MB\n", ram/1024}' 2>/dev/null || true
  df -h /c 2>/dev/null | tail -1 || true
  echo '```'
} > "$OUT" 2>&1

echo "[hourly-report] $OUT"
exit 0
