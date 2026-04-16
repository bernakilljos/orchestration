---
description: "개발/코드 MCP 설치 — GitHub·GitLab·Docker·K8s·AWS·Firebase·Supabase·Vercel·Netlify"
allowed-tools: Bash(claude:*), Bash(where:*), Bash(powershell:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task

아래 MCP 중 **미설치된 것만** 설치한다. 이미 있으면 건너뜀.

```
# GitHub
claude mcp add github -s user -- npx -y @modelcontextprotocol/server-github

# GitLab
claude mcp add gitlab -s user -- npx -y @modelcontextprotocol/server-gitlab

# Bitbucket (Atlassian)
claude mcp add bitbucket -s user -- npx -y @atlassian/mcp-atlassian

# Docker
claude mcp add docker -s user -- npx -y @docker/mcp-server

# Kubernetes
claude mcp add kubernetes -s user -- npx -y mcp-server-kubernetes

# AWS
claude mcp add aws -s user -- npx -y @aws/mcp-server

# Firebase
claude mcp add firebase -s user -- npx -y firebase-mcp

# Supabase
claude mcp add supabase -s user -- npx -y @supabase/mcp-server-supabase

# Vercel
claude mcp add vercel -s user -- npx -y @vercel/mcp-adapter

# Netlify
claude mcp add netlify -s user -- npx -y netlify-mcp
```

설치 완료 후 결과 표로 보고:

| MCP | 상태 |
|-----|------|
| github | 설치됨/이미존재/실패 |
| ... | ... |

"Codex 워커가 이 MCP들을 바로 사용할 수 있습니다."
