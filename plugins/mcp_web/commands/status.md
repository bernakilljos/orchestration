---
description: "설치 상태 확인"
allowed-tools: Bash(claude:*)
---
## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task
위 MCP 목록에서 이 플러그인 관련 항목 유무를 확인하고 표로 출력.
없으면 `/install` 실행 안내.
