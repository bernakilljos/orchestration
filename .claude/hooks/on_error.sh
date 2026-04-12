#!/usr/bin/env bash
# on_error.sh — 에러 발생시 로그 저장 + 알림
# Windows Git Bash 호환
# Usage: bash .claude/hooks/on_error.sh "에러 메시지" [소스파일]

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ERROR_MSG="${1:-Unknown error}"
SOURCE_FILE="${2:-unknown}"
ERROR_LOG_DIR="$PROJECT_DIR/.claude/logs/errors"
mkdir -p "$ERROR_LOG_DIR"

# 1. 에러 로그 파일 저장
ERROR_LOG="$ERROR_LOG_DIR/error_${TIMESTAMP}.log"
cat > "$ERROR_LOG" << HEREDOC
=== ERROR LOG ===
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Source: $SOURCE_FILE
Message: $ERROR_MSG
Working Dir: $(pwd)
Python: $(python --version 2>&1 || echo "N/A")
=================

--- System Info ---
OS: $(uname -s 2>/dev/null || echo "Windows")
User: $(whoami 2>/dev/null || echo "unknown")

--- Recent Bash Commands (last 5) ---
$(tail -5 "$PROJECT_DIR/.claude/logs/bash_commands.log" 2>/dev/null || echo "N/A")
HEREDOC

echo "[ERROR] 로그 저장: $ERROR_LOG"

# 2. 에러 요약을 통합 에러 히스토리에 추가
HISTORY="$ERROR_LOG_DIR/error_history.csv"
if [ ! -f "$HISTORY" ]; then
    echo "timestamp,source,message" > "$HISTORY"
fi
SAFE_MSG=$(echo "$ERROR_MSG" | tr ',' ';' | tr '\n' ' ' | head -c 200)
echo "${TIMESTAMP},${SOURCE_FILE},${SAFE_MSG}" >> "$HISTORY"

# 3. 에러 로그 정리 (100개 초과시 오래된 것 삭제)
ERROR_COUNT=$(ls -1 "$ERROR_LOG_DIR"/error_*.log 2>/dev/null | wc -l)
if [ "${ERROR_COUNT:-0}" -gt 100 ]; then
    ls -1t "$ERROR_LOG_DIR"/error_*.log | tail -n +101 | xargs rm -f
    echo "[INFO] 오래된 에러 로그 정리 (최근 100개 유지)"
fi

echo "[INFO] 에러 처리 완료"
