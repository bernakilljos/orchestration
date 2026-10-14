#!/usr/bin/env bash
# auto-compact-check.sh — LV12 토큰 절약 자동 트리거
# 트리거: Stop hook (매 턴 종료마다)
# 동작: 턴 카운트 증가 -> 임계치 도달 시 "작업 계속 · compact 를 사용자에게 미루지 않기" 안내 + 마커 파일 생성
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
# 세션별 턴 카운터 — 전역 파일은 세션이 바뀌어도 누적돼 새 세션이
# 이미 임계치 근처에서 시작했다 (2026-09-08: turns=31 로 4턴 뒤 강제압축 예약 상태였음)
# 세션 id 는 훅 stdin(JSON) 이 정본. 없으면 최신 transcript 파일명으로 대체.
PAYLOAD="$(cat 2>/dev/null || true)"
SID="$(printf '%s' "$PAYLOAD" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
if [ -z "${SID:-}" ]; then
  SID="$(ls -t "$HOME/.claude/projects/"*"$(basename "$PROJECT_ROOT")"*/*.jsonl 2>/dev/null | head -1 | xargs -r basename 2>/dev/null | sed 's/\.jsonl$//')"
fi
[ -n "${SID:-}" ] || SID="nosid-$PPID"
mkdir -p "$STATE_DIR/session-turns.d" 2>/dev/null
TURN_FILE="$STATE_DIR/session-turns.d/$SID.turns"
COOLDOWN_FILE="$STATE_DIR/session-turns.d/$SID.cooldown"
MARKER="$CACHE_DIR/auto-compact-recommended"
GUARD_LOG="$CACHE_DIR/guard.log"

THRESHOLD_TURNS="${COMPACT_TURN_THRESHOLD:-60}"
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

# 4. 임계치 판정 — 실제 컨텍스트 사용률이 정본.
#    2026-09-08: 턴 수만 보고 강제 압축하던 탓에 컨텍스트 29.5% 인데도 대화가
#    25턴마다 요약으로 뭉개졌다. 사용자 체감은 "또 처음부터 다시 시작".
#    턴 수-guard 라인은 컨텍스트 양과 무관하므로 단독 발동 금지.
PCT=0
if command -v python >/dev/null 2>&1; then PY=python
elif command -v python >/dev/null 2>&1; then PY=python
else PY=""; fi
if [ -n "$PY" ]; then
  PCT=$("$PY" -X utf8 "$PROJECT_ROOT/.claude/scripts/context-usage-pct.py" 2>/dev/null || echo 0)
fi
PCT=${PCT:-0}

TRIGGER=""
if [ "${PCT%.*}" -ge "${COMPACT_PCT_THRESHOLD:-85}" ]; then
  TRIGGER="context=${PCT}%≥${COMPACT_PCT_THRESHOLD:-85}%"
fi

if [ -z "$TRIGGER" ]; then
  exit 0
fi

# 보조 신호는 참고로만 덧붙인다 (단독 발동 X)
[ "$TURNS" -ge "$THRESHOLD_TURNS" ] && TRIGGER="$TRIGGER (turns=$TURNS)"
[ "${LINES:-0}" -ge "$THRESHOLD_LINES" ] && TRIGGER="$TRIGGER (guard_lines=$LINES)"

# 5. 마커 + cooldown 기록
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "turns=$TURNS guard_lines=$LINES reason=$TRIGGER ts=$TS" > "$MARKER"
echo "$TURNS" > "$COOLDOWN_FILE"

# 6. stdout — 2026-10-14: «다음 턴 첫 동작으로 /compact 자체 실행» 의무를 없앴다.
#    Claude 는 /compact 를 실행할 수 없다(사용자 명령) → 세션이 "compact 해 주세요" 로 사용자에게 미루고,
#    사용자가 직접 compact 하면 다음 메시지까지 작업이 멈췄다 (ICM 사례). 자동 compact(97%)는 작업을 이어 간다.
cat <<EOF
[컨텍스트 임계치 — $TRIGGER]
★ 남은 작업은 그대로 계속한다. 사용자에게 compact·/clear 를 요청하지 않는다
  (97% 자동 compact 는 작업을 이어 가고, 사용자가 직접 compact·clear 하면 다음 메시지까지 멈춘다).
★ 큰 파일 read·긴 출력은 자제한다. 작업이 다 끝났을 때만 "끝났으니 /clear 해도 됩니다" 한 줄.
EOF

exit 0
