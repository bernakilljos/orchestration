#!/bin/bash
# user-prompt-git-fetch.sh — UserPromptSubmit 시 origin fetch (10분 throttle)
# 왜: 사용자가 다른 세션에서 push 하면 이 세션은 세션 중간엔 모름
#     session-start-git-fetch.sh 는 SessionStart 만 발동 → 보완
# 10분 throttle · 백그라운드 fetch · behind 있으면 systemMessage
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LAST="$PROJECT_DIR/.claude/state/last-git-fetch-prompt"
mkdir -p "$PROJECT_DIR/.claude/state"

NOW=$(date +%s)
if [ -f "$LAST" ]; then
  PREV=$(cat "$LAST" 2>/dev/null || echo 0)
  AGE=$((NOW - PREV))
  [ "$AGE" -lt 600 ] && exit 0  # 10분 throttle
fi

echo "$NOW" > "$LAST"

cd "$PROJECT_DIR" 2>/dev/null || exit 0

# 백그라운드 fetch (프롬프트 지연 X · 다음 턴에 반영)
(
  git fetch origin 2>/dev/null
  BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)
  if [ "$BEHIND" -gt 0 ]; then
    LOG="$PROJECT_DIR/.claude/logs/user-prompt-fetch.log"
    mkdir -p "$PROJECT_DIR/.claude/logs"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] behind=$BEHIND" >> "$LOG"
    # systemMessage (크리티컬 X · 정보성)
    echo ""
    echo "[GIT] 다른 세션 push 감지: behind=$BEHIND · 다음 turn 에 pull 권장"
    git log --oneline HEAD..origin/main 2>/dev/null | head -3 | sed 's/^/  - /'
  fi
) &

exit 0
