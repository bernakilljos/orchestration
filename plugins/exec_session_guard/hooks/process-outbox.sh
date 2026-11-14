#!/bin/bash
# process-outbox.sh — SessionStart hook
#
# Stop/SessionEnd 의 outbox-write.sh 가 쌓아둔 메시지를 처리:
#   - notion-outbox/*.md -> stdout 출력 -> Claude 가 보고 다음 turn 에 Notion MCP push
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
#   - slack-outbox/*.json -> stdout 출력 -> Claude 가 Slack MCP push (또는 curl)
#
# Claude 에게 "큐에 N 개 메시지 있음. MCP 로 처리해줘" 라는 reminder 출력.

set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT" 2>/dev/null || exit 0

NOTION_DIR="$PROJECT/.claude/state/notion-outbox"
SLACK_DIR="$PROJECT/.claude/state/slack-outbox"

# R253 재측정: 소비자가 없어 2026-05 부터 1,892개가 쌓였고 (Notion 1579 · Slack 313) 디스크 캐시가
#   식은 첫 실행이 27.6초 → 시간 제한 10초에 끊겨(hook_cancelled) 한 번도 끝나지 못했다.
#   3일 넘은 대기 파일은 (하루 ~50개 · 소비자 없음 · 같은 요약은 orca.db 에도 저장) archive/ 로 옮겨(삭제 X · 되돌릴 수 있음) 폴더를 작게 유지하고,
#   겹쳐 실행되지 않게 잠그고, 끝날 때마다 한 줄 기록해 비동기 실행의 정상 종료를 확인할 수 있게 한다.
LOG="$PROJECT/.claude/logs/process-outbox.log"
LOCK="$PROJECT/.claude/state/process-outbox.lock"
mkdir -p "$(dirname "$LOG")" 2>/dev/null
T0=$(date +%s%N 2>/dev/null || echo 0)
if ! mkdir "$LOCK" 2>/dev/null; then
  # 10분 넘은 잠금은 끊긴 실행의 잔여로 보고 회수
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +10 2>/dev/null)" ]; then
    rmdir "$LOCK" 2>/dev/null; mkdir "$LOCK" 2>/dev/null || exit 0
  else
    echo "$(date '+%F %T') skip 이미 실행 중" >> "$LOG"; exit 0
  fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

ARCHIVED=0
for d in "$NOTION_DIR" "$SLACK_DIR"; do
  [ -d "$d" ] || continue
  mkdir -p "$d/archive" 2>/dev/null
  n=$(find "$d" -maxdepth 1 -type f \( -name '*.md' -o -name '*.json' \) -mtime +3 -print -exec mv -n {} "$d/archive/" \; 2>/dev/null | wc -l | tr -d ' ')
  ARCHIVED=$((ARCHIVED + ${n:-0}))
done

NOTION_COUNT=0
SLACK_COUNT=0
[ -d "$NOTION_DIR" ] && NOTION_COUNT=$(find "$NOTION_DIR" -maxdepth 1 -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
[ -d "$SLACK_DIR" ]  && SLACK_COUNT=$(find "$SLACK_DIR" -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l | tr -d ' ')
T1=$(date +%s%N 2>/dev/null || echo 0)
echo "$(date '+%F %T') done notion=$NOTION_COUNT slack=$SLACK_COUNT archived=$ARCHIVED ms=$(( (T1 - T0) / 1000000 ))" >> "$LOG"

if [ "$NOTION_COUNT" = "0" ] && [ "$SLACK_COUNT" = "0" ]; then
  exit 0  # 조용히 통과
fi

cat <<EOF
[outbox] 처리 대기 메시지 발견
  Notion outbox: $NOTION_COUNT 건 (.claude/state/notion-outbox/)
  Slack outbox:  $SLACK_COUNT 건 (.claude/state/slack-outbox/)

다음 turn 에 권장 동작:
  1) notion-outbox 의 *.md -> mcp__claude_ai_Notion__notion-create-pages 로 push 후 파일 삭제
  2) slack-outbox 의 *.json -> mcp__claude_ai_Slack__slack_send_message 로 push 후 파일 삭제
  3) SLACK_WEBHOOK_URL 환경변수 설정되어 있으면 outbox-write 가 즉시 발송 (이미 처리됨)
EOF

exit 0
