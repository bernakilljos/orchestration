#!/bin/bash
# HOOK-06 — Notify: Slack/Teams webhook 알림
# 사용: hook-06-notify.sh good|warning|danger "메시지"
set -e

LEVEL="${1:-good}"
MESSAGE="${2:-Notification}"
PROJECT="${3:-$(pwd)}"

# Load config
if [ -f "$PROJECT/.claude/deploy-config.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT/.claude/deploy-config.env" 2>/dev/null || true
  set +a
fi

NOTIFY_TYPE="${NOTIFY_TYPE:-none}"

# 색상 매핑
COLOR="good"
case "$LEVEL" in
  warning) COLOR="warning" ;;
  danger)  COLOR="danger" ;;
  *)       COLOR="good" ;;
esac

# 멘션
MENTION="${NOTIFY_MENTION:-}"
[ -n "$MENTION" ] && [ "$LEVEL" = "danger" ] && MESSAGE="$MENTION $MESSAGE"

if ! command -v curl >/dev/null 2>&1; then
  echo "[NOTIFY-SKIP] curl 없음"
  exit 0
fi

# Slack
if [ "$NOTIFY_TYPE" = "slack" ] || [ "$NOTIFY_TYPE" = "both" ]; then
  if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    PAYLOAD=$(printf '{"attachments":[{"color":"%s","text":"%s"}]}' "$COLOR" "$MESSAGE")
    curl -s -X POST -H 'Content-type: application/json' -d "$PAYLOAD" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 \
      && echo "[NOTIFY] Slack sent ($LEVEL)" \
      || echo "[NOTIFY-FAIL] Slack 실패"
  fi
fi

# Teams
if [ "$NOTIFY_TYPE" = "teams" ] || [ "$NOTIFY_TYPE" = "both" ]; then
  if [ -n "${TEAMS_WEBHOOK_URL:-}" ]; then
    PAYLOAD=$(printf '{"text":"[%s] %s"}' "$LEVEL" "$MESSAGE")
    curl -s -X POST -H 'Content-type: application/json' -d "$PAYLOAD" "$TEAMS_WEBHOOK_URL" >/dev/null 2>&1 \
      && echo "[NOTIFY] Teams sent ($LEVEL)" \
      || echo "[NOTIFY-FAIL] Teams 실패"
  fi
fi

[ "$NOTIFY_TYPE" = "none" ] && echo "[NOTIFY-SKIP] NOTIFY_TYPE=none"

exit 0
