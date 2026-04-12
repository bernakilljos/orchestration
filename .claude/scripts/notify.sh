#!/bin/bash
# =====================================================
# notify.sh — Slack/Teams notification
# Usage: bash .claude/scripts/notify.sh [color] [message]
# color: good(green) | warning(yellow) | danger(red)
# Example: bash .claude/scripts/notify.sh "good" "Deploy success"
# =====================================================
source .claude/deploy-config.env 2>/dev/null || true

COLOR="${1:-good}"
MESSAGE="${2:-Notification}"
TITLE="${3:-AI Orchestration}"

# Notification disabled
if [ -z "$NOTIFY_TYPE" ] || [ "$NOTIFY_TYPE" = "none" ]; then
  echo "[SKIP] Notification disabled (NOTIFY_TYPE=none)"
  exit 0
fi

# Mention handling
if [ -n "$NOTIFY_MENTION" ]; then
  MESSAGE="${MESSAGE}
${NOTIFY_MENTION}"
fi

# -------------------------------------------------------
# Slack send
# -------------------------------------------------------
send_slack() {
  if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "[SKIP] Slack webhook not configured"
    return 0
  fi

  PAYLOAD=$(cat <<EOF
{
  "attachments": [
    {
      "color": "${COLOR}",
      "title": "${TITLE}",
      "text": "${MESSAGE}",
      "footer": "AI Orchestration Kit",
      "ts": $(date +%s)
    }
  ]
}
EOF
)

  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    -d "$PAYLOAD")

  [ "$HTTP_STATUS" = "200" ] \
    && echo "[OK] Slack notification sent ($COLOR)" \
    || echo "[FAIL] Slack notification failed [$HTTP_STATUS]"
}

# -------------------------------------------------------
# Teams send
# -------------------------------------------------------
send_teams() {
  if [ -z "$TEAMS_WEBHOOK_URL" ]; then
    echo "[SKIP] Teams webhook not configured"
    return 0
  fi

  case "$COLOR" in
    good)    THEME_COLOR="00AA00" ;;
    warning) THEME_COLOR="FFA500" ;;
    danger)  THEME_COLOR="FF0000" ;;
    *)       THEME_COLOR="0078D7" ;;
  esac

  PAYLOAD=$(cat <<EOF
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "summary": "${TITLE}",
  "themeColor": "${THEME_COLOR}",
  "title": "${TITLE}",
  "text": "${MESSAGE}"
}
EOF
)

  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$TEAMS_WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    -d "$PAYLOAD")

  [ "$HTTP_STATUS" = "200" ] \
    && echo "[OK] Teams notification sent ($COLOR)" \
    || echo "[FAIL] Teams notification failed [$HTTP_STATUS]"
}

# -------------------------------------------------------
# Execute
# -------------------------------------------------------
case "$NOTIFY_TYPE" in
  slack) send_slack ;;
  teams) send_teams ;;
  both)  send_slack; send_teams ;;
  *)     echo "[SKIP] NOTIFY_TYPE=$NOTIFY_TYPE" ;;
esac
