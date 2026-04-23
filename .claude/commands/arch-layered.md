---
description: "레이어 케이크 아키텍처 다이어그램 1페이지 생성 — 위→아래 계층 구조 인포그래픽"
allowed-tools: Bash(where:*), Bash(claude mcp list:*), Write, Bash(python:*)
---

## Context
- python-pptx:   !`python -c "import pptx" 2>/dev/null && echo OK || echo 없음`
- ReportLab:     !`python -c "import reportlab" 2>/dev/null && echo OK || echo 없음`
- wkhtmltopdf:   !`where wkhtmltopdf 2>/dev/null && echo OK || echo 없음`
- Pandoc:        !`where pandoc 2>/dev/null && echo OK || echo 없음`

## Your task

주제: `$ARGUMENTS`
스타일: Brij Pandey "Claude Code Complete Architecture Reference" 레이어 케이크

---

### Step 1 — 레이어 분석 (Claude)

`skill-arch-layered` 활성화 후 주제에서 5~7개 레이어 추출:

```json
{
  "title": "<주제> Architecture Reference",
  "layers": [
    {
      "level": "TOP|LAYER 5|...|LAYER 1",
      "name": "<별칭>",
      "icon": "<이모지 또는 SVG>",
      "items": ["항목1", "항목2"],
      "code": "<선택, 1~2줄>"
    }
  ],
  "foundation": {
    "name": "<런타임 이름>",
    "table": [["컬럼1", "컬럼2"], ["행1", "값1"]]
  }
}
```

규칙:
- 레이어 5~7개
- TOP = 사용자에게 가까움 / FOUNDATION = 인프라
- 각 레이어 본문 3~6 항목

`$ARGUMENTS` 모호하면 1회 질문.

### Step 2 — 렌더 도구 선택

Context 결과에 따라:
1. **python-pptx 있음** → A4 1슬라이드 PPTX → `outputs/arch/layered-{slug}-{date}.pptx`
2. **ReportLab 있음** → 직접 PDF → `.pdf`
3. **wkhtmltopdf 있음** → HTML 작성 후 PDF 변환
4. **모두 없음** → Markdown 만 저장 + 설치 안내

### Step 3 — python-pptx 렌더 코드 (1순위)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

COLORS = {
    "apricot": RGBColor(0xF4, 0xD5, 0xC2),
    "lilac":   RGBColor(0xD5, 0xC7, 0xE8),
    "blue":    RGBColor(0xC2, 0xD5, 0xE8),
    "green":   RGBColor(0xC7, 0xE8, 0xC2),
    "yellow":  RGBColor(0xE8, 0xDC, 0xC2),
    "coral":   RGBColor(0xE8, 0xC2, 0xC2),
    "gray":    RGBColor(0xE0, 0xE0, 0xE0),
}

# A4 가로 비율 슬라이드 1장 생성
# 좌측 80px 아이콘 컬럼 + 본문
# 레이어별 사각형 + 텍스트 박스
```

전체 스크립트는 outputs 에 함께 저장: `outputs/arch/layered-{slug}-{date}.gen.py`

### Step 4 — 결과 보고

```
✅ 레이어 케이크 생성 완료
- 결과: outputs/arch/layered-{slug}-{date}.{pdf|pptx}
- 원본: outputs/arch/layered-{slug}-{date}.md
- 레이어: N개 (TOP → FOUNDATION)

레이어 미리보기:
  TOP:    <name> — <items 요약>
  L5:     <name> — ...
  ...
```

### 품질 게이트
- [ ] 레이어 5~7
- [ ] 각 색 구별
- [ ] 1 페이지 수렴
- [ ] 위→아래 의미 흐름 명확
