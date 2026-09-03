# mcp_data — 데이터 MCP 설치 — MySQL·PostgreSQL·MongoDB·BigQuery·Snowflake·Sheets·Airtable

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1100

## 📖 개요

데이터 MCP 허브 — MySQL·MongoDB·BigQuery·Sheets.

## 📋 커맨드

- `/install`  기본
- `/mcp_data`
- `/status`

## 🧠 스킬

- `skill-32-db-migration`  핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-04-architect`

## 🪝 훅

- `hook-01-pre-task` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 일괄 설치
```bash
/plug_data
```

### 예시 2: 상태 확인
```bash
/mcp_data-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
