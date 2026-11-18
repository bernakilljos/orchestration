#!/usr/bin/env bash
# Stop hook: ACTIVE Standing Requirements 중 verify FAIL → Stop 차단.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0
IN="$(cat 2>/dev/null || true)"
RC=0
# 같은 Stop 입력(stop_hook_active 등)을 두 검사에 모두 전달 · set -e 로 첫 검사 실패 시 끊기지 않게 || 로 받음
printf '%s' "$IN" | "$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/standing-requirements.py" gate || RC=$?
# §81 STD-KOREAN-001 마지막 보고 한글 검사 (영어면 1회 차단 + .claude/logs/language-violations.log)
printf '%s' "$IN" | "$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/standing-requirements.py" lang-check || RC=2
# R253 남은 품질 3건(시작 속도·한국어·재부팅 재개) 자동 판정 — 뒤에서 실행 · Stop 을 막거나 늦추지 않음
# 결과: .claude/state/quality-self-check.json · .claude/logs/quality-self-check.log
TP="$(printf '%s' "$IN" | "$PY" -c "import json,sys
try: print(json.load(sys.stdin).get('transcript_path',''))
except Exception: print('')" 2>/dev/null || true)"
if [ -n "$TP" ]; then
  nohup "$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/quality-self-check.py" --transcript "$TP" >/dev/null 2>&1 &
fi
exit $RC
