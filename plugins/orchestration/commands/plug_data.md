---
description: "데이터/분석 MCP 설치 — MySQL·PostgreSQL·MongoDB·BigQuery·Snowflake·Sheets·Airtable"
allowed-tools: Bash(claude:*), Bash(where:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task

아래 MCP 중 **미설치된 것만** 설치한다.

```
# MySQL + PostgreSQL (Google MCP Toolbox로 통합 커버)
claude mcp add mcp-toolbox -s user -- npx -y @googleapis/mcp-toolbox

# MongoDB
claude mcp add mongodb -s user -- npx -y @mongodb-js/mcp-server-mongodb

# BigQuery (Google 공식 remote MCP)
claude mcp add bigquery -s user --transport http https://bigquery.googleapis.com/mcp

# Snowflake
claude mcp add snowflake -s user -- npx -y @snowflake-labs/mcp

# Google Sheets (claude.ai 내장 확인 먼저, 없으면 설치)
claude mcp add google-sheets -s user -- npx -y @googleapis/mcp-server-sheets

# Airtable
claude mcp add airtable -s user -- npx -y airtable-mcp-server
```

설치 완료 후 결과 표로 보고:

| MCP | 상태 | 비고 |
|-----|------|------|
| mcp-toolbox | ... | MySQL + PostgreSQL 통합 |
| mongodb | ... | |
| bigquery | ... | remote HTTP |
| snowflake | ... | |
| google-sheets | ... | |
| airtable | ... | |

"PPT 자동화 파이프라인에서 바로 데이터를 끌어올 수 있습니다."
