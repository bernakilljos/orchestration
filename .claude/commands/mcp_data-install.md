---
description: "데이터 MCP 일괄 설치 — PostgreSQL·MongoDB·BigQuery·Snowflake·Sheets·Airtable (npm 검증)"
allowed-tools: Bash(claude:*), Bash(where:*), Bash(npm:*)
---

## 검증된 패키지 기반 설치

**2026-04-23 npm 실측 기준** — 모든 패키지 확인됨.

### 필수 (권장 설치)

```bash
# PostgreSQL (공식 Anthropic MCP)
claude mcp add postgres -s user -- npx -y @modelcontextprotocol/server-postgres

# MongoDB (공식 MongoDB MCP, 2026-04-20 최신)
claude mcp add mongodb -s user -- npx -y mongodb-mcp-server

# BigQuery (커뮤니티 MCP, 활발한 유지보수)
claude mcp add bigquery -s user -- npx -y bigquery-mcp-server

# Snowflake (커뮤니티 MCP)
claude mcp add snowflake -s user -- npx -y snowflake-mcp

# Google Sheets (권한 제어 포함)
claude mcp add google-sheets -s user -- npx -y @shivaduke28/google-sheets-mcp

# Airtable (공식 패키지)
claude mcp add airtable -s user -- npx -y airtable-mcp-server
```

### MySQL 대안

**MySQL 공식 MCP 없음** (2026-04-23 현재). 옵션:

1. **PostgreSQL으로 대체**: 동일한 기능 (권장)
2. **직접 API 호출**: Node.js `mysql2` 라이브러리 사용
3. **메타 패키지**: `@modelcontextprotocol/server-everything` (모든 공식 서버 포함, 크기 큼)

```bash
# Meta-package 옵션 (모든 공식 Anthropic 서버)
claude mcp add mcp-everything -s user -- npx -y @modelcontextprotocol/server-everything
```

---

## 설치 확인

```bash
claude mcp list
```

| MCP | 패키지명 | 버전 | 상태 |
|-----|---------|------|------|
| postgres | @modelcontextprotocol/server-postgres | 0.6.2 | ✅ 검증 |
| mongodb | mongodb-mcp-server | 1.10.0+ | ✅ 검증 |
| bigquery | bigquery-mcp-server | 0.1.16+ | ✅ 검증 |
| snowflake | snowflake-mcp | 1.1.0+ | ✅ 검증 |
| google-sheets | @shivaduke28/google-sheets-mcp | 1.2.2+ | ✅ 검증 |
| airtable | airtable-mcp-server | 1.13.0+ | ✅ 검증 |

---

## 보안 주의사항

각 MCP는 **연결 문자열 또는 API 토큰 필요**. `.env` 에서 로드:

```bash
# PostgreSQL
export POSTGRES_CONNECTION_STRING="postgresql://user:pass@host/db"

# MongoDB
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/db"

# BigQuery
export GOOGLE_PROJECT_ID="my-project"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

# Snowflake
export SNOWFLAKE_ACCOUNT="xy12345"
export SNOWFLAKE_USER="user"
export SNOWFLAKE_PASSWORD="pass"
export SNOWFLAKE_DATABASE="db"

# Google Sheets
export GOOGLE_SHEETS_TOKEN="oauth2_token"

# Airtable
export AIRTABLE_PAT="pat_xxx..."
```

**절대 금지**: 커맨드 라인에 직접 입력 또는 git 커밋
