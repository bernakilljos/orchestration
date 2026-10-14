#!/bin/bash
# session-start-git-fetch.sh — SessionStart 시 origin fetch + behind 알림
# 왜: 다른 세션 (claude.ai web·다른 터미널) 에서 push 하면 이 세션은 모름
#     → "왜 자꾸 새 커밋 나와" 문제 재발 방지
#
# 동작:
#   - origin fetch (수초 걸림 · 백그라운드)
#   - behind 있으면 systemMessage 로 알림 (크리티컬 아님 · log 만)
#   - force pull 안 함 (사용자 결정 존중)

[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG="$PROJECT_DIR/.claude/logs/session-git-fetch.log"
mkdir -p "$PROJECT_DIR/.claude/logs"

# 1h throttle (매 세션마다 fetch 는 과함)
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

# 백그라운드로 fetch (세션 시작 지연 X)
(
  git fetch origin 2>/dev/null
  BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  if [ "$BEHIND" -gt 0 ]; then
    echo "[$TS] behind=$BEHIND ahead=$AHEAD" >> "$LOG"
    # systemMessage 로 알림 (크리티컬 5 아님 · 정보성)
    echo ""
    echo "[GIT] origin/main 과 간극: behind=$BEHIND ahead=$AHEAD"
    echo "  → 다른 세션/기기에서 push 가능성. 'git pull origin main' 권장"
    git log --oneline HEAD..origin/main 2>/dev/null | head -5 | sed 's/^/  - /'
  fi
  echo "$NOW" > "$LAST_FETCH"
) &

exit 0
