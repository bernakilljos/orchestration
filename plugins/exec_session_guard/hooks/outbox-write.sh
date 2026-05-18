#!/bin/bash
# outbox-write.sh — Stop/SessionEnd hook
#
# 세션 종료 시 요약을 outbox 큐에 저장. 두 가지 채널:
#   .claude/state/notion-outbox/  → 다음 세션에 Notion MCP 로 push
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
#   .claude/state/slack-outbox/   → SLACK_WEBHOOK_URL 있으면 즉시 curl, 없으면 큐
#
# 5핵심 #4 Memory 의 장기 기억 + #5 Observability 의 외부 알림 보완.
# zero-touch — webhook 없으면 큐만 쌓고 다음 세션의 process-outbox 가 처리.

set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT" 2>/dev/null || exit 0

EVENT="${1:-Stop}"
NOTION_DIR="$PROJECT/.claude/state/notion-outbox"
SLACK_DIR="$PROJECT/.claude/state/slack-outbox"
mkdir -p "$NOTION_DIR" "$SLACK_DIR"

NOW=$(date '+%Y-%m-%dT%H:%M:%S')
TS=$(date '+%Y%m%d-%H%M%S')

# .env 로드 (선택 — SLACK_WEBHOOK_URL 있으면 즉시 발송)
[ -f "$PROJECT/.env" ] && set -a && . "$PROJECT/.env" 2>/dev/null && set +a

# --- 1. 세션 요약 수집 ---
LAST_COMMITS=$(git -C "$PROJECT" log --oneline -5 2>/dev/null | head -5)
GIT_STATUS_COUNT=$(git -C "$PROJECT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
SESSION_TURNS=0
if [ -d "$PROJECT/.claude/state/session-turns" ]; then
  SESSION_TURNS=$(ls "$PROJECT/.claude/state/session-turns" 2>/dev/null | wc -l | tr -d ' ')
fi

# --- 2. Notion outbox (장기 기억) — 매 세션 무조건 기록 ---
NOTION_FILE="$NOTION_DIR/$TS.md"
cat > "$NOTION_FILE" <<EOF
# 세션 종료 요약 ($EVENT)

- 시각: $NOW
- 프로젝트: $(basename "$PROJECT")
- 이벤트: $EVENT
- 미커밋 변경 파일: $GIT_STATUS_COUNT 개
- 세션 turn 수: $SESSION_TURNS

## 최근 commit (5건)
\`\`\`
$LAST_COMMITS
\`\`\`

## 다음 세션 처리 방법
이 파일은 SessionStart 시 process-outbox.sh 가 감지.
Claude 가 자동으로 Notion MCP (notion-create-pages) 로 push 후 이 파일 삭제.
EOF

# --- 3. Slack outbox (크리티컬만) ---
# 크리티컬 조건: 미커밋 파일 0 (clean stop) 이 아니거나 PostToolUseFailure
SLACK_NEEDED=0
SLACK_LEVEL="good"
SLACK_TITLE=""

if [ "$EVENT" = "PostToolUseFailure" ]; then
  SLACK_NEEDED=1
  SLACK_LEVEL="danger"
  SLACK_TITLE="작업 실패 — $(basename "$PROJECT")"
fi

# (필요 시 추가 조건: 비용 임계·시크릿 노출 등 — orca.db 에서 조회)

if [ "$SLACK_NEEDED" = "1" ]; then
  SLACK_FILE="$SLACK_DIR/$TS.json"
  cat > "$SLACK_FILE" <<EOF
{
  "ts": "$NOW",
  "level": "$SLACK_LEVEL",
  "title": "$SLACK_TITLE",
  "project": "$(basename "$PROJECT")",
  "event": "$EVENT"
}
EOF

  # webhook URL 있으면 즉시 발송 (curl), 없으면 큐로 남김
  if [ -n "${SLACK_WEBHOOK_URL:-}" ] && command -v curl >/dev/null 2>&1; then
    PAYLOAD=$(printf '{"attachments":[{"color":"%s","title":"%s","text":"event=%s project=%s ts=%s"}]}' \
              "$SLACK_LEVEL" "$SLACK_TITLE" "$EVENT" "$(basename "$PROJECT")" "$NOW")
    curl -s -X POST -H 'Content-type: application/json' \
         -d "$PAYLOAD" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 \
      && rm -f "$SLACK_FILE"  # 발송 성공 시 큐에서 제거
  fi
fi

exit 0
