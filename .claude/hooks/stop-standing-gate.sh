#!/usr/bin/env bash
# Stop hook: ACTIVE Standing Requirements 중 verify FAIL → Stop 차단.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0
IN="$(cat 2>/dev/null || true)"
SR="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/standing-requirements.py"
# 같은 Stop 입력(stop_hook_active 등)을 두 검사에 모두 전달.
# R356 (11-23 실측 각 0.23초 · 순차 0.46초): 서로 독립이라 동시에 실행 → 응답 끝 대기 약 0.2초 단축 · 출력은 종전 순서(gate → lang-check)로
E1="$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/sg1.$$")"; E2="$(mktemp 2>/dev/null || echo "${TMPDIR:-/tmp}/sg2.$$")"
printf '%s' "$IN" | "$PY" -X utf8 "$SR" gate >"$E1.out" 2>"$E1" & P1=$!
# §81 STD-KOREAN-001 마지막 보고 한글 검사 (영어면 1회 차단 + .claude/logs/language-violations.log)
printf '%s' "$IN" | "$PY" -X utf8 "$SR" lang-check >"$E2.out" 2>"$E2" & P2=$!
RC=0
wait "$P1" || RC=$?
wait "$P2" || RC=2
cat "$E1.out" "$E2.out" 2>/dev/null || true
cat "$E1" "$E2" >&2 2>/dev/null || true
rm -f "$E1" "$E2" "$E1.out" "$E2.out" 2>/dev/null || true
# R253 남은 품질 3건(시작 속도·한국어·재부팅 재개) 자동 판정 — 뒤에서 실행 · Stop 을 막거나 늦추지 않음
# 결과: .claude/state/quality-self-check.json · .claude/logs/quality-self-check.log
# R356: transcript_path 한 칸을 읽으려고 python 을 한 번 더 띄우던 것(≈0.11초) → 셸 문자열 추출 (JSON 의 \\ 는 \ 로)
TP="$(printf '%s' "$IN" | grep -o '"transcript_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed -E 's/^.*:[[:space:]]*"(.*)"$/\1/; s/\\\\/\\/g' || true)"
if [ -n "$TP" ]; then
  nohup "$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/quality-self-check.py" --transcript "$TP" >/dev/null 2>&1 &
fi
exit $RC
