#!/bin/bash
# session-start-git-fetch.sh — SessionStart 시 origin fetch + 자동 pull
# 왜: 다른 세션 (claude.ai web·다른 터미널·다른 기기) 에서 push 하면 이 세션은 모름.
#     "pull 받아봐" 재지시가 48h 안 5회+ 반복 → 자동 pull 로 승격 (2026-10-15).
# 동작:
#   - origin fetch (수초 · 백그라운드)
#   - behind > 0 → 자동 rebase pull (stash → rebase → pop)
#   - conflict 가 history.md 뿐이면 --theirs 로 자동 해결 (chore(auto) 자동 생성이라 손실 없음)
#   - 다른 파일 conflict 면 abort + 알림만 (사용자 결정)
# 안전장치: push 는 안 함. pull 만.

[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG="$PROJECT_DIR/.claude/logs/session-git-fetch.log"
mkdir -p "$PROJECT_DIR/.claude/logs"

# 1h throttle
LAST_FETCH="$PROJECT_DIR/.claude/state/last-git-fetch"
NOW=$(date +%s)
if [ -f "$LAST_FETCH" ]; then
  LAST=$(cat "$LAST_FETCH" 2>/dev/null || echo 0)
  AGE=$((NOW - LAST))
  if [ "$AGE" -lt 3600 ]; then
    exit 0
  fi
fi

cd "$PROJECT_DIR" 2>/dev/null || exit 0

# 백그라운드 (세션 시작 지연 X)
(
  git fetch origin 2>/dev/null
  BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  echo "$NOW" > "$LAST_FETCH"

  if [ "$BEHIND" -eq 0 ]; then
    exit 0
  fi

  # 자동 pull 시도 (B안 승격)
  STASH_MSG="auto-pull-$NOW"
  STASHED=0
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    git stash push -u -m "$STASH_MSG" >/dev/null 2>&1 && STASHED=1
  fi

  if git pull --rebase origin main >/dev/null 2>&1; then
    PULL_RC=0
  else
    # conflict 또는 rebase 실패
    PULL_RC=1
    # history.md 만 conflict 면 --theirs 로 자동 해결 (chore 자동 생성 손실 없음)
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
      # 다른 파일 conflict → abort + 알림만
      git rebase --abort 2>/dev/null
    fi
  fi

  # stash 복원
  if [ "$STASHED" -eq 1 ]; then
    git stash pop >/dev/null 2>&1 || {
      # pop 중 conflict → history.md 만이면 theirs
      CONFLICTS2=$(git diff --name-only --diff-filter=U 2>/dev/null)
      if [ "$CONFLICTS2" = "docs/deploy-history/history.md" ]; then
        git checkout --theirs docs/deploy-history/history.md 2>/dev/null
        git add docs/deploy-history/history.md 2>/dev/null
        git stash drop >/dev/null 2>&1
      fi
    }
  fi

  if [ "$PULL_RC" -eq 0 ]; then
    echo "[$TS] auto-pulled behind=$BEHIND ahead=$AHEAD" >> "$LOG"
    echo ""
    echo "[GIT] 다른 세션 push $BEHIND건 자동 pull 완료"
    git log --oneline -$BEHIND 2>/dev/null | sed 's/^/  - /'
  else
    echo "[$TS] auto-pull FAILED behind=$BEHIND (conflict beyond history.md)" >> "$LOG"
    echo ""
    echo "[GIT] 자동 pull 실패 (history.md 외 conflict) · behind=$BEHIND · 수동 pull 필요"
  fi
) &

exit 0
