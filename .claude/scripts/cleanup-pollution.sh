#!/usr/bin/env bash
# 오염 파일 자동 정리 — Windows redirect 잔재 + nested 폴더 + 3일+ 임시
# 호출: SessionStart hook 또는 cron 또는 수동
# 로그: .claude/logs/cleanup-pollution.log
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
LOG="$LOG_DIR/cleanup-pollution.log"
mkdir -p "$LOG_DIR"

NOW="$(date '+%Y-%m-%d %H:%M:%S')"
REMOVED=0

log() {
  echo "[$NOW] $1" >> "$LOG"
  REMOVED=$((REMOVED + 1))
}

# 1. nul/NUL 파일 (Windows `2>nul` 잔재) — 즉시 삭제
for f in "$PROJECT_ROOT/nul" "$PROJECT_ROOT/NUL"; do
  if [ -f "$f" ]; then
    rm -f "$f" && log "nul redirect: $f"
  fi
done
# 하위 디렉토리도 (maxdepth 4)
find "$PROJECT_ROOT" -maxdepth 4 -type f \( -name "nul" -o -name "NUL" \) 2>/dev/null | while read -r f; do
  rm -f "$f" && log "nul redirect: $f"
done

# 2. nested .claude/.claude/ (PROJECT_ROOT 계산 버그 잔재) — 즉시
if [ -d "$PROJECT_ROOT/.claude/.claude" ]; then
  rm -rf "$PROJECT_ROOT/.claude/.claude" && log "nested .claude/.claude/"
fi

# 3. 3일+ 임시 파일 (*.bak / *.orig / *.tmp / *.swp / *~)
DAYS=3
find "$PROJECT_ROOT" -maxdepth 5 -type f \
  \( -name "*.bak" -o -name "*.orig" -o -name "*.tmp" -o -name "*.swp" -o -name "*~" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -mtime +$DAYS 2>/dev/null | while read -r f; do
  rm -f "$f" && log "3일+ 임시: $f"
done

# 4. docs/screens/_*.log 3일+ (작업 완료 후 잔재)
find "$PROJECT_ROOT/docs/screens" -maxdepth 1 -type f -name "_*.log" -mtime +$DAYS 2>/dev/null | while read -r f; do
  rm -f "$f" && log "screens log 3일+: $f"
done

# 5. .claude/logs/*.log 14일+ (장기 보존)
find "$PROJECT_ROOT/.claude/logs" -maxdepth 2 -type f -name "*.log" -mtime +14 2>/dev/null | while read -r f; do
  rm -f "$f" && log "logs 14일+: $f"
done

# 6. .claude/tasks/done/ 30일+ 완료 task
find "$PROJECT_ROOT/.claude/tasks/done" -maxdepth 2 -type f -mtime +30 2>/dev/null | while read -r f; do
  rm -f "$f" && log "done task 30일+: $f"
done

# 7. claude tool result 임시파일 (사용자 cache 안) 7일+
TOOL_RESULTS="$HOME/.claude/projects/C--pjt-orchestration-v1/tool-results"
if [ -d "$TOOL_RESULTS" ]; then
  find "$TOOL_RESULTS" -maxdepth 2 -type f -mtime +7 2>/dev/null | while read -r f; do
    rm -f "$f"
  done
fi

# 8. 빈 디렉토리 정리 (carve-out: docs/screens, plugins, .claude 보존)
# 임시 폴더만 (.claude/tasks/*/temp/ 등)
find "$PROJECT_ROOT/.claude/tasks" -maxdepth 3 -type d -empty 2>/dev/null | while read -r d; do
  rmdir "$d" 2>/dev/null && log "empty task dir: $d"
done

# 결과
if [ $REMOVED -gt 0 ]; then
  echo "[cleanup-pollution] 정리: $REMOVED 항목 ($NOW)" >&2
fi
exit 0
