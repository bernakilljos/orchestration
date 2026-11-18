#!/usr/bin/env bash
# auto-save-next-actions.sh — Stop/SessionEnd hook: assistant 마지막 응답의
# "## Next Actions" / "## 다음 세션" / "## Phase N" 섹션을 .claude/state/next-actions.md 로 자동 저장.
#
# /clear·compact 후 resume-last-24h.py 가 그 파일을 systemMessage 로 주입 → 사용자 첫 메시지가 뭐든 바로 이어감.
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0

INPUT="$(cat 2>/dev/null || true)"
"$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/auto-save-next-actions.py" </dev/null 2>/dev/null || true

# R258: 작업 종료(Stop · 비동기 등록)마다 자기 산출물 정리 + 불필요한 자기 승인 요청 취소 + 남은 승인 요청 기록.
#   SessionEnd 는 같은 훅이 동기로 등록돼 있어 실행하지 않는다 (종료를 기다리게 하지 않음 · 다음 Stop 이 처리).
case "$INPUT" in
  *'"hook_event_name"'*'"Stop"'*|*'"hook_event_name":"Stop"'*)
    printf '%s' "$INPUT" | "$PY" -X utf8 "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/own-cleanup.py" run >/dev/null 2>&1 || true ;;
esac
exit 0
