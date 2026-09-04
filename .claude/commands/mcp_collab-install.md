---
description: "협업 MCP 설치 (Slack·Notion·Jira·Trello·Telegram + 내장 Gmail·Calendar) — 2026-05 npm 검증"
allowed-tools: Bash(claude:*), Bash(npm:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(미설치)"`
- Node.js 확인: !`node --version && npm --version`

## Your task

아래 5개 협업 MCP를 설치합니다. 각각 토큰 필요.

### 1. Slack — @sigmacomputing/slack-mcp-server (권장)

**왜 이것?**: 공식 `@modelcontextprotocol/server-slack` 는 deprecated (2025).

**준비**:
```bash
# 1. Slack API 콘솔 https://api.slack.com/apps
#    - Create New App → From scratch
#    - Name: Claude, Workspace 선택
# 2. OAuth & Permissions:
#    - Scopes 추가: chat:write, channels:list, users:list, files:write
#    - Install to Workspace (또는 reinstall)
# 3. Bot Token Signing Secret 복사 → SLACK_BOT_TOKEN 환경변수 설정
```

**설치**:
```bash
export SLACK_BOT_TOKEN="xoxb-..."  # 위에서 복사한 토큰
claude mcp add slack -s user \
  --env SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN \
  -- npx -y @sigmacomputing/slack-mcp-server
```

### 2. Notion — @notionhq/notion-mcp-server v2.2.1 (공식)

**준비**:
```bash
# 1. https://www.notion.so/my-integrations → Create new integration
# 2. Name: Claude
# 3. Capabilities: Read, Update, Delete
# 4. Internal Integration Token 복사 → NOTION_API_KEY 설정
```

**설치**:
```bash
export NOTION_API_KEY="secret_..."  # 위에서 복사한 토큰
claude mcp add notion -s user \
  --env NOTION_API_KEY=$NOTION_API_KEY \
  -- npx -y @notionhq/notion-mcp-server
```

### 3. Jira — @rui.branco/jira-mcp v1.7.5 (권장—Claude 최적화)

**준비 (Atlassian Cloud)**:
```bash
# 1. https://id.atlassian.com/manage/api-tokens → Create API token
# 2. Email: your-email@domain.com
# 3. Token: jira_... 형식 (만료 불가)
# 4. Host: https://your-domain.atlassian.net
```

**준비 (On-premise)**:
```bash
# Jira admin → User profile → API tokens
```

**설치**:
```bash
export JIRA_HOST="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="jira_..."

claude mcp add jira -s user \
  --env JIRA_HOST=$JIRA_HOST \
  --env JIRA_EMAIL=$JIRA_EMAIL \
  --env JIRA_API_TOKEN=$JIRA_API_TOKEN \
  -- npx -y @rui.branco/jira-mcp
```

### 4. Trello — trello-mcp v1.0.3 (권장—최신 종합)

**준비**:
```bash
# 1. https://trello.com/app-key → API Key 발급
# 2. Token link → Generate Token (No expiration 권장)
# 3. Key + Token 모두 저장
```

**설치**:
```bash
export TRELLO_API_KEY="abc123..."
export TRELLO_API_TOKEN="def456..."

claude mcp add trello -s user \
  --env TRELLO_API_KEY=$TRELLO_API_KEY \
  --env TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -- npx -y trello-mcp
```

### 5. Telegram — telegram-bot-mcp-server v1.0.0 (Bot API · 알림용)

**왜 Bot API?**: 알림·메시지 전송이 주 목적이면 Bot 이 가장 단순. MTProto(`mcp-telegram`·`telegram-mcp-server`)는 phone 인증·세션 키 필요 → 알림 자동화엔 과함.

**준비**:
```bash
# 1. Telegram 앱에서 @BotFather 검색 → /newbot → 이름·username 입력
# 2. 출력된 토큰 복사 (예: 7820123456:AAH...) → TELEGRAM_BOT_TOKEN 설정
# 3. 봇과 1:1 채팅 시작 후 아무 메시지 → /start
# 4. 다음 URL 로 chat_id 확인:
#    https://api.telegram.org/bot<TOKEN>/getUpdates
#    → "chat":{"id": 123456789, ...} 의 id 복사 → TELEGRAM_CHAT_ID
```

**설치 (Windows / 모든 OS 공통, npx 래퍼)**:
```bash
export TELEGRAM_BOT_TOKEN="7820123456:AAH..."
export TELEGRAM_CHAT_ID="123456789"

# Windows 는 cmd /c 래퍼 권장
claude mcp add telegram -s user \
  --env TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
  --env TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID \
  -- npx -y telegram-bot-mcp-server
```

**3주차 활용 예 — 작업 완료 알림**:
```bash
# Claude 가 task 끝날 때 자동 알림 (.claude/hooks/SessionEnd.sh 참조)
# Hook 안에서 MCP 호출하거나, scripts/notify-telegram.sh 로 직접 curl 도 가능
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d text=" Claude task 완료: $(date)"
```

> **보안 주의**: 토큰이 채팅을 보낼 수 있는 모든 권한을 가짐 → `.env` (gitignore)에만 저장. `docs/ini/telegram.ini` 도 가능.

## 설치 확인

```bash
claude mcp list | grep -E "slack|notion|jira|trello|telegram"
```

기대 결과:
```
slack    @sigmacomputing/slack-mcp-server
notion   @notionhq/notion-mcp-server
jira     @rui.branco/jira-mcp
trello   trello-mcp
telegram telegram-bot-mcp-server
```

## 미지원 (또는 대체 경로)

| 서비스 | 상태 | 이유 | 대안 |
|--------|------|------|------|
| **Gmail** | 내장 | claude.ai 에 기본 포함 | https://claude.ai 로 로그인 → 권한 요청 |
| **Google Calendar** | 내장 | claude.ai 에 기본 포함 | https://claude.ai 로 로그인 → 권한 요청 |

Gmail/Calendar 는 설치 불필요. claude.ai 계정 인증만으로 작동.

## 트러블슈팅

| 오류 | 원인 | 해결 |
|------|------|------|
| "404 not found" | 패키지명 오타 | 위 명령어 정확히 복사 |
| "401 Unauthorized" | 토큰 만료/잘못됨 | 해당 서비스 콘솔에서 토큰 재발급 |
| "npx: command not found" | Node.js 미설치 | `node -v` (14+ 필요), 설치 후 재시도 |
| "EACCES" (권한 에러) | sudo 부족 | `sudo` 앞에 추가 또는 npm config 수정 |
