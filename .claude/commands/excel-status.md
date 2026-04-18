---
description: "Excel 관련 MCP/도구 설치 상태 확인"
allowed-tools: Bash(claude:*), Bash(python:*)
---
## Context
- Excel MCP: !`claude mcp list 2>/dev/null | grep -i excel && echo OK || echo 없음`
- Sheets MCP: !`claude mcp list 2>/dev/null | grep -i sheets && echo OK || echo 없음`
- openpyxl: !`python -c "import openpyxl; print('OK')" 2>/dev/null || echo 없음`

## Your task
상태 표 출력. 없는 항목 설치 안내:
- Excel MCP: `claude mcp add excel -s user -- npx -y excel-mcp-server`
- openpyxl: `pip install openpyxl`
