---
description: "Excel/스프레드시트 자동 생성 — 데이터 입력 → 차트·분석·리포트"
allowed-tools: Bash(where:*), Bash(python:*)
---

## Context
- Excel MCP: !`claude mcp list 2>/dev/null | grep -i excel && echo OK || echo 없음`
- Google Sheets MCP: !`claude mcp list 2>/dev/null | grep -i sheets && echo OK || echo 없음`
- Python openpyxl: !`python -c "import openpyxl; print('OK')" 2>/dev/null || echo 없음`

## Your task

### 요청 분석
$ARGUMENTS 를 분석해서:
- 데이터 구조 (행/열 설계)
- 계산식 (SUM, AVERAGE, VLOOKUP 등)
- 차트 종류 (막대/꺾은선/파이)

### 생성
- Excel MCP OK → Excel MCP로 직접 생성
- Google Sheets OK → Sheets MCP 사용
- openpyxl OK → Python으로 .xlsx 생성 → docs/YYYY-MM-DD/ 저장
- 없으면 → /status 실행 후 설치 안내

### 결과
파일 경로, 시트 수, 차트 수, 주요 수식 목록 보고
