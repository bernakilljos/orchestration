---
description: "Word 문서 자동 생성 — Claude 구조 → python-docx → 표·이미지·Mermaid 다이어그램 삽입"
allowed-tools: Bash(python:*), Bash(where:*), Write
---

## Context
- python-docx: !`python -c "import docx; print('OK')"    2>/dev/null || echo 없음`
- Mermaid MCP: !`claude mcp list 2>/dev/null | grep -i mermaid && echo OK || echo 없음`
- LibreOffice:  !`where soffice 2>/dev/null && echo OK || echo 없음`

## Your task

파이프라인: **Claude → 문서 구조 → python-docx → Mermaid → PDF 변환**

---

### Hook (사전 확인)
python-docx 없으면: `pip install python-docx`

---

### Step 1 — Planner: Claude가 문서 구조 설계
주제: `$ARGUMENTS`

문서 유형 분류:
- **계약서** → 당사자, 조항, 서명란
- **보고서** → 요약, 본문, 결론, 참고자료
- **기획서** → 배경, 목적, 실행계획, 예산, 일정
- **회의록** → 일시, 참석자, 안건, 결정사항, 액션아이템
- **제안서** → 문제정의, 해결방안, 기대효과, 비용

섹션 구성, 표 구조, 필요 다이어그램 목록 작성.

---

### Step 2 — Executor: 문서 생성

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime, os

doc = Document()

# 제목
doc.add_heading("[문서 제목]", level=0)

# 메타 정보
meta_table = doc.add_table(rows=3, cols=2)
meta_table.style = "Table Grid"
meta_table.cell(0,0).text = "작성일"
meta_table.cell(0,1).text = datetime.date.today().strftime("%Y-%m-%d")

# 본문 섹션 (설계 기반 자동 생성)
for section in [설계된 섹션 목록]:
    doc.add_heading(section["title"], level=1)
    doc.add_paragraph(section["content"])
    
    # 표 삽입 (해당 섹션)
    if section.get("table"):
        t = doc.add_table(rows=len(section["table"]), cols=len(section["table"][0]))
        # ... 데이터 삽입

today = datetime.date.today().strftime("%Y-%m-%d")
os.makedirs(f"docs/{today}", exist_ok=True)
out = f"docs/{today}/[문서명].docx"
doc.save(out)
print(f"저장: {out}")
```

---

### Step 3 — Mermaid 다이어그램 (필요 시)
Mermaid MCP OK → 다이어그램 이미지 생성 → 문서에 삽입
없으면 → 다이어그램 코드를 문서 부록에 텍스트로 포함

---

### Step 4 — PDF 변환 (LibreOffice 있으면)
```
soffice --headless --convert-to pdf docs/YYYY-MM-DD/문서명.docx
```

---

### Step 5 — Validator
- 파일 저장 성공 여부
- 필수 섹션 포함 여부 (계약서면 서명란 등)
- 표 구조 깨짐 여부

---

### Step 6 — 결과 보고
| 항목 | 결과 |
|------|------|
| 파일 경로 | docs/YYYY-MM-DD/파일명.docx |
| 페이지 수 | N페이지 (예상) |
| 섹션 수 | N개 |
| 표 | N개 |
| PDF | 생성됨/미생성 |
