#!/usr/bin/env bash
# auto-save-next-actions.sh — Stop/SessionEnd hook: assistant 마지막 응답의
# "## Next Actions" / "## 다음 세션" / "## Phase N" 섹션을 .claude/state/next-actions.md 로 자동 저장.
#
# /clear·compact 후 resume-last-24h.py 가 그 파일을 systemMessage 로 주입 → 사용자 첫 메시지가 뭐든 바로 이어감.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0

"$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/auto-save-next-actions.py" 2>/dev/null || true
exit 0
