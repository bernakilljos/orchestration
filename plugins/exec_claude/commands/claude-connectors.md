---
description: "외부 SaaS 커넥터 관리 — Slack·Drive·Notion·GitHub 등 1-click 인증"
allowed-tools: Bash(claude mcp list:*), Bash(claude mcp add:*), Bash(claude mcp remove:*)
---

## Context
- 현재 MCP: !`claude mcp list 2>/dev/null`
- 인자: `$ARGUMENTS` (`list` | `add <name>` | `remove <name>` | 비워둠 = 추천)

## Your task

Claude 의 "Connectors" (50+ SaaS 사전 통합) 개념을 우리 MCP 시스템 위에 1-click 흐름으로 구현.

### Anthropic Connectors vs 우리 MCP

| | Anthropic | 우리 |
|---|---|---|
| 카탈로그 | 50+ 사전 등록 | mcp_collab/data/dev/web/docs/media 6 그룹 |
| 인증 | 1-click OAuth | 수동 토큰 입력 다수 |
| 등록 | 자동 | `claude mcp add` 호출 |

→ 이 커맨드는 **추천·검색·1-click 등록 흐름**을 우리 시스템에 추가.

### Step 1 — 분기

```
$ARGUMENTS = ""           → 추천 모드
$ARGUMENTS = "list"       → 설치된 + 가능한 커넥터 표
$ARGUMENTS = "add <name>" → 등록 (인증 안내 포함)
$ARGUMENTS = "remove <n>" → 제거 (확인 후)
```

### Step 2 — 추천 카탈로그

12개 인기 커넥터 (Anthropic 기준):

```
[협업·소통]
  slack       — Slack 메시지·검색·채널
  notion      — Notion 페이지·DB
  asana       — 태스크 관리
  google-cal  — 일정 조회·생성

[데이터·문서]
  google-drive — Drive 파일
  google-sheets — 스프레드시트
  postgres    — DB 쿼리
  bigquery    — 분석 쿼리

[개발]
  github      — repo·PR·issue
  gitlab      — repo·MR·issue
  sentry      — 에러 모니터링

[기타]
  brave-search — 웹 검색
```

### Step 3 — 카테고리별 출력

추천 모드 출력:
```
🔌 추천 커넥터 (현재 사용 패턴 기반)

[협업·소통] (당신은 ...)
  ✅ slack          (이미 설치)
  ⬜ notion         /claude-connectors add notion
  ⬜ google-cal     /claude-connectors add google-cal

[데이터·문서] (현재 0개)
  ⬜ google-drive   가장 자주 함께 쓰임
  ⬜ google-sheets

[개발]
  ✅ github         (이미 설치)

→ 추가하려면: /claude-connectors add <name>
→ 그룹 일괄: /mcp_collab-install
```

### Step 4 — Add 흐름

`/claude-connectors add notion`:
1. `claude mcp add notion <transport> <url>` 실행
2. 인증 필요 시 OAuth URL 제시 또는 토큰 입력 안내
3. 검증: `claude mcp list | grep notion`
4. 연결 테스트 1회 호출
5. 결과 보고

### Step 5 — 결과 보고 (공통)

```
✅ <action> 완료
- 커넥터: <name>
- 상태: connected | needs-auth | failed

다음 단계 제안:
- /claude-status     전체 가용 도구
- /<usage example>   바로 써보기
```

### 통합 안내

대규모 일괄 설치 → `/mcp_collab-install` 등 그룹 커맨드 사용 권장.
이 커맨드는 **개별 추가·관리** 용.
