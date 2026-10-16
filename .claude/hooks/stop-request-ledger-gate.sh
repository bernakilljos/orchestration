#!/usr/bin/env bash
# stop-request-ledger-gate.sh — Stop hook: Request Ledger n/n 완료 전 종료 차단.
#
# 근거: 외부 감사 2026-10-16 · execution-contract.md § 2 "n/n 완료 전 보고 금지"
#
# 동작:
# - .claude/state/request-ledger.json 안 request 전부 complete 상태 → exit 0 (허용)
# - 미완료 있음 → exit 2 (Claude 가 계속 작업하도록 유도)
# - ledger 없음 → exit 0 (무조건 통과)
#
# 사용자 "다 해줘" 유형 지시가 매번 "일부만 하고 보고" 로 떨어지는 결함 차단.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0

"$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/request-ledger.py" gate 2>/dev/null
exit $?
