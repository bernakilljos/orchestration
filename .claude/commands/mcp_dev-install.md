---
description: "개발/코드 MCP 설치 — GitHub·GitLab·Docker·K8s·AWS·Firebase·Supabase·Vercel (npm 실측 2026-04)"
allowed-tools: Bash(claude:*), Bash(npm:*), Bash(powershell:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## 검증된 패키지 (npm 실존 확인 2026-04-23)

아래 MCP 중 **미설치된 것만** 설치한다. 이미 있으면 건너뜀.

### 인증 불필요 (즉시 설치 가능)

```bash
# GitHub (공식 MCP, 2025-04-08)
claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github

# GitLab (공식 MCP, 2025-04-25)
claude mcp add gitlab -s user -- npx -y @modelcontextprotocol/server-gitlab

# Kubernetes (활성 유지, 2026-03-19)
claude mcp add kubernetes -s user -- npx -y mcp-server-kubernetes

# Firebase Firestore (npm: firebase-mcp, 2026-02-10)
claude mcp add firebase -s user -- npx -y firebase-mcp

# Supabase (npm: @supabase/mcp-server-supabase, 2026-03-11)
claude mcp add supabase -s user -- npx -y @supabase/mcp-server-supabase

# Vercel (npm: @vercel/mcp-adapter, 2026-03-01)
claude mcp add vercel -s user -- npx -y @vercel/mcp-adapter
```

### Docker 대안 패키지 (공식 없음 → 커뮤니티 선택)

```bash
# Docker MCP (신뢰도 높은 커뮤니티: @hypnosis/docker-mcp-server, 2026-01-12)
claude mcp add docker -s user -- npx -y @hypnosis/docker-mcp-server
```

### AWS 대안 패키지 (공식 없음 → 경량 옵션)

```bash
# AWS (Readonly 경량: aws-mcp-readonly-lite, 2026-02-16)
claude mcp add aws-readonly -s user -- npx -y aws-mcp-readonly-lite
```

## 설치 안 됨 (대체 전략)

| 서비스 | 상태 | 대안 |
|---|---|---|
| Bitbucket/Atlassian | npm에 공식 패키지 없음 | GitLab/GitHub API 사용 또는 REST API 직접 호출 |
| Netlify | 2026-01-12 unpublished | Vercel MCP로 대체 또는 REST API 직접 호출 |

설치 완료 후 결과 표로 보고:

| MCP | 상태 |
|-----|------|
| github | 설치됨/이미존재/실패 |
| gitlab | 설치됨/이미존재/실패 |
| kubernetes | 설치됨/이미존재/실패 |
| firebase | 설치됨/이미존재/실패 |
| supabase | 설치됨/이미존재/실패 |
| vercel | 설치됨/이미존재/실패 |
| docker (hypnosis) | 설치됨/이미존재/실패 |
| aws-readonly | 설치됨/이미존재/실패 |

## 환경변수 (필요 시)

MCP 인증이 필요한 경우:
- `GITHUB_TOKEN` — GitHub API 접근 (선택)
- `GITLAB_TOKEN` — GitLab API 접근 (선택)
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — AWS (aws-readonly-lite 선택)
- `VERCEL_TOKEN` — Vercel API 접근 (선택)
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` — Supabase (선택)
