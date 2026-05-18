#!/usr/bin/env bash
# auto-compact-check.sh — LV12 토큰 절약 자동 트리거
# 트리거: Stop hook (매 턴 종료마다)
# 동작: 턴 카운트 증가 → 임계치 도달 시 /compact 권장 메시지 + 마커 파일 생성
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
#
# 임계치 (env 로 override 가능):
#   COMPACT_TURN_THRESHOLD     기본 25 (턴 수)
#   COMPACT_GUARD_LINES        기본 600 (guard.log 라인 수 — 컨텍스트 무거워짐 신호)
#   COMPACT_COOLDOWN_TURNS     기본 10 (압축 권장 후 N턴 동안 재알림 차단)
#
# 마커 파일: .claude/context-cache/auto-compact-recommended
#   - 한 줄 메타: turns=N reason=... ts=...
#   - SessionStart 또는 Resume 시 사용자에게 표시 가능

set -uo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../../.." && pwd)}"
STATE_DIR="$PROJECT_ROOT/.claude/state"
CACHE_DIR="$PROJECT_ROOT/.claude/context-cache"
TURN_FILE="$STATE_DIR/session-turns"
COOLDOWN_FILE="$STATE_DIR/auto-compact-cooldown"
MARKER="$CACHE_DIR/auto-compact-recommended"
GUARD_LOG="$CACHE_DIR/guard.log"

THRESHOLD_TURNS="${COMPACT_TURN_THRESHOLD:-25}"
THRESHOLD_LINES="${COMPACT_GUARD_LINES:-600}"
COOLDOWN="${COMPACT_COOLDOWN_TURNS:-10}"

mkdir -p "$STATE_DIR" "$CACHE_DIR" 2>/dev/null || exit 0

# 1. 턴 카운터 증가
TURNS=$(cat "$TURN_FILE" 2>/dev/null || echo "0")
TURNS=$((TURNS + 1))
echo "$TURNS" > "$TURN_FILE"

# 2. cooldown 체크 (마지막 권장 후 N턴 이내면 skip)
COOL_AT=$(cat "$COOLDOWN_FILE" 2>/dev/null || echo "0")
if [ "${COOL_AT:-0}" -gt 0 ] && [ "$TURNS" -lt "$((COOL_AT + COOLDOWN))" ]; then
  exit 0
fi

# 3. guard.log 라인 수 (컨텍스트 무거움 신호)
LINES=0
if [ -f "$GUARD_LOG" ]; then
  LINES=$(wc -l < "$GUARD_LOG" 2>/dev/null | tr -d ' ' || echo "0")
fi

# 4. 임계치 판정
TRIGGER=""
if [ "$TURNS" -ge "$THRESHOLD_TURNS" ]; then
  TRIGGER="turns=$TURNS≥$THRESHOLD_TURNS"
fi
if [ "${LINES:-0}" -ge "$THRESHOLD_LINES" ]; then
  TRIGGER="${TRIGGER:+$TRIGGER, }guard_lines=$LINES≥$THRESHOLD_LINES"
fi

if [ -z "$TRIGGER" ]; then
  exit 0
fi

# 5. 마커 + cooldown 기록
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "turns=$TURNS guard_lines=$LINES reason=$TRIGGER ts=$TS" > "$MARKER"
echo "$TURNS" > "$COOLDOWN_FILE"

# 6. stdout — Claude 강제 의무 메시지 (다음 turn 첫 동작으로 /compact 자동 실행)
cat <<EOF
[auto-compact ENFORCED — 컨텍스트 임계치 도달]
트리거: $TRIGGER

★ Claude 의무 (NEXT TURN 첫 동작):
  1) 사용자 다음 prompt 받자마자 **가장 먼저 /compact 자체 실행**
     (도구 호출·답변 전, 모든 작업의 0순위)
  2) compact 완료 후 사용자 원래 요청 처리
  3) 한국어 한 줄 통지: "[auto-compact] 컨텍스트 압축 완료 — 다음 작업 진행"

★ 토큰 절감(LV12): /compact 시 다음 턴부터 90% 가벼워짐
★ 마커: .claude/context-cache/auto-compact-recommended
★ Cooldown: 다음 알림은 $COOLDOWN 턴 후
EOF

exit 0
