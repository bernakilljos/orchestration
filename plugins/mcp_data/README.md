# mcp_data — 데이터 MCP 설치 — MySQL·PostgreSQL·MongoDB·BigQuery·Snowflake·Sheets·Airtable

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

데이터·분석 MCP — MySQL·PostgreSQL·MongoDB·BigQuery·Snowflake·Sheets·Airtable.

- **Why**: DB/분석 플랫폼 연결 자동화. SQL 쿼리·마이그레이션.
- **When**: 데이터 파이프라인 구축. BI 대시보드 연동.

## 📋 커맨드

- `/install` ⭐ 기본
- `/mcp_data`
- `/status`

## 🧠 스킬

- `skill-32-db-migration` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-04-architect`

## 🪝 훅

- `hook-01-pre-task`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 일괄 설치
```
/plug_data
```

### 예시 2: MySQL만
```
/install mysql
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
