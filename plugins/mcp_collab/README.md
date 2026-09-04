# mcp_collab — 협업 MCP 설치 — Slack·Notion·Jira·Trello·Gmail·Google Calendar

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1100

## 📖 개요

협업 MCP 허브 — Slack·Notion·Jira·Gmail·Calendar.

## 📋 커맨드

- `/install`  기본
- `/mcp_collab`
- `/status`

## 🧠 스킬

- `skill-24-ai-handoff`  핵심

## 🤖 에이전트

- `agent-01-team-lead`

## 🪝 훅

- `hook-06-notify` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 일괄 설치
```bash
/plug_collab
```

### 예시 2: 상태 확인
```bash
/mcp_collab-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
