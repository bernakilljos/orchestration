---
description: "Excel·스프레드시트 자동 생성 — Claude 구조 → Sheets/openpyxl → 차트 → 데이터 시각화"
allowed-tools: Bash(python:*), Bash(where:*), Write
---

## Context
- Excel MCP:   !`claude mcp list 2>/dev/null | grep -i excel  && echo OK || echo 없음`
- Sheets MCP:  !`claude mcp list 2>/dev/null | grep -i sheets && echo OK || echo 없음`
- openpyxl:    !`python -c "import openpyxl; print('OK')" 2>/dev/null || echo 없음`
- pandas:      !`python -c "import pandas; print('OK')"  2>/dev/null || echo 없음`

## Your task

파이프라인: **Claude → 데이터 구조 → openpyxl/Sheets → 차트 → 시각화**

---

### Hook (사전 확인)
openpyxl 없으면: `pip install openpyxl pandas`

---

### Step 1 — Planner: Claude가 구조 설계
주제: `$ARGUMENTS`

스프레드시트 구성:
- 시트 목록 (각 시트 역할)
- 열 구성 (헤더, 데이터 타입)
- 계산식 (SUM, AVERAGE, VLOOKUP, COUNTIF 등)
- 차트 종류 (막대/꺾은선/파이/산점도)
- 조건부 서식 (색상 강조 규칙)

---

### Step 2 — Executor: 파일 생성

**openpyxl 방식:**
```python
import openpyxl
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import PatternFill, Font
import datetime, os

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "데이터"

# 헤더 설정
headers = [설계된 헤더 목록]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = Font(bold=True)
    cell.fill = PatternFill("solid", fgColor="4472C4")

# 샘플 데이터 + 계산식 삽입
# ... 설계 기반 자동 생성

# 차트 추가
chart = BarChart()
data_ref = Reference(ws, min_col=2, max_col=4, min_row=1, max_row=ws.max_row)
chart.add_data(data_ref, titles_from_data=True)
ws.add_chart(chart, "F2")

today = datetime.date.today().strftime("%Y-%m-%d")
os.makedirs(f"docs/{today}", exist_ok=True)
out = f"docs/{today}/[주제].xlsx"
wb.save(out)
print(f"저장: {out}")
```

**Google Sheets MCP 있으면 추가로:**
`sheets-mcp 호출 → 온라인 공유 링크 생성`

---

### Step 3 — Validator
- 파일 열기 성공 여부 확인
- 계산식 결과값 검증
- 차트 데이터 범위 확인

---

### Step 4 — 결과 보고
| 항목 | 결과 |
|------|------|
| 파일 경로 | docs/YYYY-MM-DD/파일명.xlsx |
| 시트 수 | N개 |
| 계산식 | N개 |
| 차트 | N개 |
| Sheets 링크 | URL (있으면) |
