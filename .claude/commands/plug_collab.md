---
description: "협업 MCP 설치 — Slack·Notion·Jira·Trello·Gmail·Google Calendar (2026-04 검증)"
allowed-tools: Bash(claude:*), Bash(npm:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null | grep -E "slack|notion|jira|trello" || echo "(없음)"`

## Your task

협업 서비스 MCP를 설치합니다. 다음 서비스 중 미설치된 것만 설치:

### OAuth 필수 (인증 토큰 준비)

#### 1. Slack (DEPRECATED—대체 권장)
**경고**: `@modelcontextprotocol/server-slack` 는 공식 deprecated 상태 (2025).
대신 `@sigmacomputing/slack-mcp-server` 권장.

**설정**:
1. https://api.slack.com/apps → Create New App → "From scratch"
2. App name: Claude, Workspace 선택
3. OAuth & Permissions:
   - Scopes: `chat:write`, `channels:list`, `users:list`, `files:write`
   - Bot Token Signing Secret 발급
4. Bot token (`xoxb-...`) 복사

```bash
claude mcp add slack -s user \
  --env SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -- npx -y @sigmacomputing/slack-mcp-server
```

#### 2. Notion (Official)
**패키지**: `@notionhq/notion-mcp-server` v2.2.1 (공식)

**설정**:
1. https://www.notion.so/my-integrations → "Create new integration"
2. Name: Claude, 권한: Read content + Update content + Delete content
3. Internal integration token 복사

```bash
claude mcp add notion -s user \
  --env NOTION_API_KEY=$NOTION_API_KEY \
  -- npx -y @notionhq/notion-mcp-server
```

#### 3. Jira (여러 선택지)
**권장**: `@rui.branco/jira-mcp` v1.7.5 (최신, Claude 최적화)
또는: `jira-mcp` v1.0.1 (경량)

**설정**:
1. Atlassian Cloud: https://id.atlassian.com/manage/api-tokens → Create API token
2. 또는 On-premise: Jira admin → User Profile → API Token
3. 기본 인증: base64(email:token)

```bash
claude mcp add jira -s user \
  --env JIRA_HOST=https://your-domain.atlassian.net \
  --env JIRA_EMAIL=your-email@example.com \
  --env JIRA_API_TOKEN=$JIRA_API_TOKEN \
  -- npx -y @rui.branco/jira-mcp
```

#### 4. Trello (No Official)
**권장**: `trello-mcp` v1.0.3 (최신 종합)
또는: `trello-mcp-server` v0.0.4 (경량)

**설정**:
1. https://trello.com/app-key → API key 발급
2. "Token" 링크 → Generate token (만료 안 함 권장)

```bash
claude mcp add trello -s user \
  --env TRELLO_API_KEY=$TRELLO_API_KEY \
  --env TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -- npx -y trello-mcp
```

### Built-in (claude.ai—별도 설치 불필요)

| 서비스 | 상태 | 설명 |
|--------|------|------|
| **Gmail** | 내장 | claude.ai 에 기본 포함 (Google OAuth) |
| **Google Calendar** | 내장 | claude.ai 에 기본 포함 (Google OAuth) |

Google 서비스 이용 시 해당 계정 인증만 필요 (claude.ai 설정에서 권한 요청).

## 설치 결과 보고

설치 후 다음 명령으로 확인:

```bash
claude mcp list
```

기대 결과 (설치된 것만):
- `slack` — Slack 채널·메시지 관리
- `notion` — Notion DB·페이지 관리
- `jira` — Jira 이슈 관리
- `trello` — Trello 보드·카드 관리
- `Gmail` (내장) — 이메일 자동화
- `Google Calendar` (내장) — 일정 기반 실행

### 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| "package not found" | npm에 없는 패키지명 | 위 권장 패키지명 정확히 사용 |
| "OAuth invalid" | 토큰 만료/권한 부족 | 해당 서비스 개발자 콘솔 재확인 |
| "command failed" | Node 설치 안 됨 | `node --version` 확인, 14+ 필요 |
| Gmail/Calendar 안 보임 | 내장이지만 미활성 | https://claude.ai 로그인 → 설정 → 권한 활성화 |
