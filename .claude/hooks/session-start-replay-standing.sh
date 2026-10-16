#!/usr/bin/env bash
# SessionStart hook: Standing Requirements 자동 재주입.
# 근거: 2026-10-16 사용자 "저장 ≠ 재주입" · Persistent Requirement Contract.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0
"$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/standing-requirements.py" replay 2>/dev/null
exit 0
