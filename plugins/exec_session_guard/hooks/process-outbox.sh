#!/bin/bash
# process-outbox.sh — SessionStart hook
#
# Stop/SessionEnd 의 outbox-write.sh 가 쌓아둔 메시지를 처리:
#   - notion-outbox/*.md → stdout 출력 → Claude 가 보고 다음 turn 에 Notion MCP push
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
#   - slack-outbox/*.json → stdout 출력 → Claude 가 Slack MCP push (또는 curl)
#
# Claude 에게 "큐에 N 개 메시지 있음. MCP 로 처리해줘" 라는 reminder 출력.

set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT" 2>/dev/null || exit 0

NOTION_DIR="$PROJECT/.claude/state/notion-outbox"
SLACK_DIR="$PROJECT/.claude/state/slack-outbox"

NOTION_COUNT=0
SLACK_COUNT=0

[ -d "$NOTION_DIR" ] && NOTION_COUNT=$(ls "$NOTION_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ -d "$SLACK_DIR" ]  && SLACK_COUNT=$(ls "$SLACK_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')

if [ "$NOTION_COUNT" = "0" ] && [ "$SLACK_COUNT" = "0" ]; then
  exit 0  # 조용히 통과
fi

cat <<EOF
[outbox] 처리 대기 메시지 발견
  Notion outbox: $NOTION_COUNT 건 (.claude/state/notion-outbox/)
  Slack outbox:  $SLACK_COUNT 건 (.claude/state/slack-outbox/)

다음 turn 에 권장 동작:
  1) notion-outbox 의 *.md → mcp__claude_ai_Notion__notion-create-pages 로 push 후 파일 삭제
  2) slack-outbox 의 *.json → mcp__claude_ai_Slack__slack_send_message 로 push 후 파일 삭제
  3) SLACK_WEBHOOK_URL 환경변수 설정되어 있으면 outbox-write 가 즉시 발송 (이미 처리됨)
EOF

exit 0
