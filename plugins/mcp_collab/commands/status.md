---
description: "협업 MCP 설치 상태 확인 (Slack·Notion·Jira·Trello·Telegram)"
allowed-tools: Bash(claude:*)
---

## Context
- 설치된 MCP 목록: !`claude mcp list 2>/dev/null || echo "(설치된 MCP 없음)"`
- 현재 환경: `node --version`, `npm --version`

## Your task

위 목록에서 협업 MCP 상태 확인:

```bash
claude mcp list 2>/dev/null | grep -E "slack|notion|jira|trello|telegram" || echo "협업 MCP 미설치"
```

**결과 해석**:

| 항목 | 설치됨 | 미설치 | 비고 |
|------|:-------:|:-------:|------|
| `slack` | ✓ | ✗ | @sigmacomputing/slack-mcp-server |
| `notion` | ✓ | ✗ | @notionhq/notion-mcp-server (공식) |
| `jira` | ✓ | ✗ | @rui.branco/jira-mcp (권장) |
| `trello` | ✓ | ✗ | trello-mcp (권장) |
| `telegram` | ✓ | ✗ | telegram-bot-mcp-server (Bot API) |
| Gmail | ✓* | - | claude.ai 내장 (*자동) |
| Google Calendar | ✓* | - | claude.ai 내장 (*자동) |

**환경변수 점검**:
```bash
echo "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:+set}"
echo "NOTION_API_KEY=${NOTION_API_KEY:+set}"
echo "JIRA_API_TOKEN=${JIRA_API_TOKEN:+set}"
echo "TRELLO_API_TOKEN=${TRELLO_API_TOKEN:+set}"
echo "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:+set}"
echo "TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:+set}"
```

**다음 단계**:
- 모두 ✓: 설치 완료. `/mcp_collab` 또는 각 도구 직접 사용 가능
- 하나 이상 ✗: `/mcp_collab-install` 실행하여 누락된 것 설치
- Telegram 알림 hook 까지 원하면: `.claude/hooks/SessionEnd.sh` 에 `notify-telegram.sh` 호출 추가
