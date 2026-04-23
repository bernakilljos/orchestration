---
description: "협업 MCP 설치 상태 확인 (Slack·Notion·Jira·Trello)"
allowed-tools: Bash(claude:*)
---

## Context
- 설치된 MCP 목록: !`claude mcp list 2>/dev/null || echo "(설치된 MCP 없음)"`
- 현재 환경: `node --version`, `npm --version`

## Your task

위 목록에서 협업 MCP 상태 확인:

```bash
claude mcp list 2>/dev/null | grep -E "slack|notion|jira|trello" || echo "협업 MCP 미설치"
```

**결과 해석**:

| 항목 | 설치됨 | 미설치 | 비고 |
|------|:-------:|:-------:|------|
| `slack` | ✓ | ✗ | @sigmacomputing/slack-mcp-server |
| `notion` | ✓ | ✗ | @notionhq/notion-mcp-server (공식) |
| `jira` | ✓ | ✗ | @rui.branco/jira-mcp (권장) |
| `trello` | ✓ | ✗ | trello-mcp (권장) |
| Gmail | ✓* | - | claude.ai 내장 (*자동) |
| Google Calendar | ✓* | - | claude.ai 내장 (*자동) |

**다음 단계**:
- 모두 ✓: 설치 완료. `/mcp_collab` 또는 각 도구 직접 사용 가능
- 하나 이상 ✗: `/mcp_collab-install` 실행하여 누락된 것 설치
