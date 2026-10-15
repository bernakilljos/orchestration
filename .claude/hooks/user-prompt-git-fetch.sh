#!/bin/bash
# user-prompt-git-fetch.sh — UserPromptSubmit 시 origin fetch + 자동 pull
# 왜: 세션 중간에 다른 세션/기기 push 가 쌓이면 사용자가 매번 "pull 받아봐" 재지시.
#     2026-10-15 자동 pull 승격 (B안) — history.md 자동 conflict 해결 포함.
# 10분 throttle · 백그라운드 · push 는 안 함.

[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LAST="$PROJECT_DIR/.claude/state/last-git-fetch-prompt"
LOG="$PROJECT_DIR/.claude/logs/user-prompt-fetch.log"
mkdir -p "$PROJECT_DIR/.claude/state" "$PROJECT_DIR/.claude/logs"

NOW=$(date +%s)
if [ -f "$LAST" ]; then
  PREV=$(cat "$LAST" 2>/dev/null || echo 0)
  AGE=$((NOW - PREV))
  [ "$AGE" -lt 600 ] && exit 0  # 10분 throttle
fi
echo "$NOW" > "$LAST"

cd "$PROJECT_DIR" 2>/dev/null || exit 0

(
  git fetch origin 2>/dev/null
  BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  [ "$BEHIND" -eq 0 ] && exit 0

  TS=$(date '+%Y-%m-%d %H:%M:%S')
  STASH_MSG="auto-pull-prompt-$NOW"
  STASHED=0
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    git stash push -u -m "$STASH_MSG" >/dev/null 2>&1 && STASHED=1
  fi

  PULL_RC=1
  if git pull --rebase origin main >/dev/null 2>&1; then
    PULL_RC=0
  else
    CONFLICTS=$(git diff --name-only --diff-filter=U 2>/dev/null)
    if [ "$CONFLICTS" = "docs/deploy-history/history.md" ]; then
      git checkout --theirs docs/deploy-history/history.md 2>/dev/null
      git add docs/deploy-history/history.md 2>/dev/null
      if git rebase --continue >/dev/null 2>&1; then
        PULL_RC=0
      else
        git rebase --abort 2>/dev/null
      fi
    else
      git rebase --abort 2>/dev/null
    fi
  fi

  if [ "$STASHED" -eq 1 ]; then
    git stash pop >/dev/null 2>&1 || {
      CONFLICTS2=$(git diff --name-only --diff-filter=U 2>/dev/null)
      if [ "$CONFLICTS2" = "docs/deploy-history/history.md" ]; then
        git checkout --theirs docs/deploy-history/history.md 2>/dev/null
        git add docs/deploy-history/history.md 2>/dev/null
        git stash drop >/dev/null 2>&1
      fi
    }
  fi

  if [ "$PULL_RC" -eq 0 ]; then
    echo "[$TS] auto-pulled behind=$BEHIND" >> "$LOG"
    echo ""
    echo "[GIT] 다른 세션 push $BEHIND건 자동 pull 완료 (prompt hook)"
  else
    echo "[$TS] auto-pull FAILED behind=$BEHIND" >> "$LOG"
    echo ""
    echo "[GIT] 자동 pull 실패 (history.md 외 conflict) · behind=$BEHIND"
  fi
) &

exit 0
