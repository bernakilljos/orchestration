#!/usr/bin/env bash
# 산출물 유통기한 자동 점검 - SessionStart hook.
#
# 룰: .claude/rules/artifact-freshness-check.md (SoT - 유통기한 매트릭스)
# 스크립트: .claude/scripts/artifact-freshness-report.py
#
# OVERDUE 있으면 systemMessage 로 첫 응답 전 사용자 알림.
# STALE 은 로그만 (침묵).
# FRESH 는 완전 침묵.

set -u

# PROJECT_ROOT = 이 스크립트 위치 .claude/hooks/ 의 상위 2단계
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

REPORT="$PROJECT_ROOT/.claude/scripts/artifact-freshness-report.py"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
LOG_FILE="$LOG_DIR/artifact-freshness.log"

mkdir -p "$LOG_DIR"

# R259: 월간 health-check 가 «30일 지나면 자동» 설계인데 부르는 곳이 없어 10/16 점수가 한 달 넘게 상태줄에 남았다.
#   monthly 는 스스로 30일 제한 (1.4초 실측) · 이 훅은 비동기 등록이라 시작을 기다리게 하지 않음.
PY_H="$(command -v python 2>/dev/null)"
[ -n "$PY_H" ] && [ -f "$PROJECT_ROOT/.claude/scripts/health-check.py" ] && \
  "$PY_H" -X utf8 "$PROJECT_ROOT/.claude/scripts/health-check.py" monthly >> "$LOG_DIR/health-check.log" 2>&1

# 1시간 throttle — SessionStart 폭주 방지
THROTTLE_FILE="$PROJECT_ROOT/.claude/state/artifact-freshness.last"
mkdir -p "$(dirname "$THROTTLE_FILE")"

if [ -f "$THROTTLE_FILE" ]; then
  LAST=$(cat "$THROTTLE_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  if [ $((NOW - LAST)) -lt 3600 ]; then
    exit 0
  fi
fi

date +%s > "$THROTTLE_FILE"

if [ ! -f "$REPORT" ]; then
  echo "[artifact-freshness] scan script 없음: $REPORT" >> "$LOG_FILE"
  exit 0
fi

# Python 동적 검색 (하드코딩 X)
PY_BIN="$(command -v python 2>/dev/null || command -v python 2>/dev/null || echo python)"

# 스캔 실행 - stdout=OVERDUE, stderr=STALE
OUTPUT="$("$PY_BIN" "$REPORT" 2>>"$LOG_FILE")"
RC=$?

if [ $RC -ne 0 ]; then
  echo "[$(date -Iseconds)] scan failed rc=$RC" >> "$LOG_FILE"
  exit 0
fi

echo "[$(date -Iseconds)] scan done" >> "$LOG_FILE"

if [ -n "$OUTPUT" ]; then
  # Claude Code hook JSON — systemMessage 로 첫 응답 전 노출
  # jq 있으면 안전하게, 없으면 최소 escape
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$OUTPUT" | jq -Rs '{systemMessage: .}'
  else
    ESC=$(printf '%s' "$OUTPUT" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "%s\\n", $0}')
    printf '{"systemMessage":"%s"}\n' "$ESC"
  fi
fi

exit 0
