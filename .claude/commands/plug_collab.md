---
description: "협업/자동화 MCP 설치 — Slack·Notion·Jira·Trello·Gmail·Google Calendar"
allowed-tools: Bash(claude:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task

Gmail·Google Calendar는 **claude.ai 내장 MCP**. 나머지 미설치된 것만 설치.

```
# Slack
claude mcp add slack -s user -- npx -y @modelcontextprotocol/server-slack

# Notion
claude mcp add notion -s user -- npx -y @modelcontextprotocol/server-notion

# Jira (Atlassian)
claude mcp add jira -s user -- npx -y @atlassian/mcp-atlassian

# Trello
claude mcp add trello -s user -- npx -y trello-mcp-server
```

내장 확인:
- Gmail → `mcp__claude_ai_Gmail__` 툴 존재 여부
- Google Calendar → `mcp__claude_ai_Google_Calendar__` 툴 존재 여부

결과 보고:

| MCP | 상태 | 역할 |
|-----|------|------|
| Slack | 설치됨/실패 | 알림·트리거 |
| Notion | 설치됨/실패 | 문서·작업 |
| Jira | 설치됨/실패 | 이슈 트래킹 |
| Trello | 설치됨/실패 | 보드 관리 |
| Gmail | 내장 | 이메일 자동화 |
| Google Calendar | 내장 | 일정 기반 실행 |
