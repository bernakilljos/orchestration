#!/usr/bin/env bash
# pre-install-lock.sh — PreToolUse Bash hook
# 목적: install/sync-to-team/install-to 명령 감지 시 kit 편집 상태 검사
#       미완 상태 (uncommitted / edit-lock) 이면 block
# 근거: .claude/rules/install-order.md - feedback_install_order.md
set -e

INPUT="$(cat)"
if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)"
else
  CMD="$(echo "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/')"
fi

# install 트리거 패턴
TRIGGER='install\.bat|install_codex\.bat|install_gemini\.bat|sync-to-team\.sh|/install-to |install-to '
if ! echo "$CMD" | grep -qE "$TRIGGER"; then
  exit 0  # non-install -> pass
fi

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
BLOCK_REASON=""

# 1. kit-edit-lock 파일 존재?
LOCK_FILE="$PROJECT/.claude/state/kit-edit-lock"
if [ -f "$LOCK_FILE" ]; then
  BLOCK_REASON="kit-edit-lock 활성 ($(cat "$LOCK_FILE" 2>/dev/null | head -1))"
fi

# 2. git uncommitted 변경 있음?
if [ -z "$BLOCK_REASON" ] && command -v git >/dev/null 2>&1; then
  cd "$PROJECT" 2>/dev/null && {
    UNCOMMIT="$(git status --porcelain 2>/dev/null | wc -l | tr -d '[:space:]')"
    if [ "$UNCOMMIT" -gt 0 ] 2>/dev/null; then
      BLOCK_REASON="uncommitted 변경 $UNCOMMIT 건 (git status --porcelain)"
    fi
  }
fi

if [ -n "$BLOCK_REASON" ]; then
  cat <<EOF
{"decision":"block","reason":"[install-order 위반] kit 편집 미완 상태에서 install 시도.\n원인: $BLOCK_REASON\n\n순서 (rules/install-order.md):\n  1) kit 편집 완료\n  2) git commit\n  3) sync-plugins (필요 시)\n  4) install / sync-to-team\n  5) 검증\n\n해제: git commit 후 재시도 또는 rm .claude/state/kit-edit-lock"}
EOF
  exit 0
fi

exit 0
