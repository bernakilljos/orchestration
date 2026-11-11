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
exit $RC
