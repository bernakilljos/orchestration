---
description: "치트시트(레퍼런스 카드) 1페이지 생성 — 트리+블록+코드 3컬럼"
allowed-tools: Bash(where:*), Bash(claude mcp list:*), Write, Bash(python:*)
---

## Context
- python-pptx:   !`python -c "import pptx" 2>/dev/null && echo OK || echo 없음`
- ReportLab:     !`python -c "import reportlab" 2>/dev/null && echo OK || echo 없음`
- wkhtmltopdf:   !`where wkhtmltopdf 2>/dev/null && echo OK || echo 없음`
- Pandoc:        !`where pandoc 2>/dev/null && echo OK || echo 없음`

## Your task

주제: `$ARGUMENTS`
스타일: Brij Pandey "Claude Code Project Structure" 3컬럼 치트시트

---

### Step 1 — 정보 수집 (Claude)

`skill-arch-cheatsheet` 활성화 후 주제 분석:

```json
{
  "title": "<주제> Cheatsheet",
  "author": "<who>",
  "tree": "...ASCII 트리...",
  "blocks": [{"title": "...", "items": [...]}],
  "snippets": [{"name": "...", "lang": "...", "code": "..."}]
}
```

규칙:
- 좌측 폴더 트리 (깊이 3~4 레벨)
- 중앙 6~10 블록
- 우측 1~3 코드 스니펫 (각 30줄 이하)

`$ARGUMENTS` 가 프로젝트 경로면 → 자동으로 폴더 구조·CLAUDE.md·plugin.json 스캔.
모호하면 1회 질문.

### Step 2 — 렌더 도구 선택

Context 결과에 따라:
1. **wkhtmltopdf 있음** → HTML 3컬럼 grid → PDF (1순위, 가장 예쁨)
2. **ReportLab 있음** → 직접 PDF
3. **python-pptx 있음** → A4 1슬라이드 PPTX
4. **모두 없음** → Markdown + 설치 안내

### Step 3 — HTML 템플릿 골격 (1순위 경로)

```html
<!DOCTYPE html>
<html><head><style>
  @page { size: A4; margin: 1cm; }
  body { display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 1em;
         font-family: -apple-system, sans-serif; }
  .col-tree { font-family: monospace; font-size: 9pt; }
  .col-blocks { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5em; }
  .block { background: #fff; padding: 0.5em; border-radius: 4px;
           border-top: 3px solid var(--accent); }
  .col-code pre { background: #2d2d2d; color: #7ec07e; padding: 0.5em;
                  font-size: 8pt; }
  h1 { grid-column: 1 / -1; }
</style></head>
<body>
  <h1>{title}</h1>
  <div class="col-tree"><pre>{tree}</pre></div>
  <div class="col-blocks">
    <!-- {blocks} 반복 -->
  </div>
  <div class="col-code">
    <!-- {snippets} 반복 -->
  </div>
</body></html>
```

생성 코드 함께 저장: `outputs/arch/cheatsheet-{slug}-{date}.gen.py`

### Step 4 — 결과 보고

```
✅ 치트시트 생성 완료
- PDF: outputs/arch/cheatsheet-{slug}-{date}.pdf
- 원본: outputs/arch/cheatsheet-{slug}-{date}.md
- 블록 N개 / 코드 M개

블록 미리보기:
  1. <block1 title>
  2. <block2 title>
  ...
```

### 품질 게이트
- [ ] 3컬럼 비율 유지
- [ ] 1 페이지 수렴
- [ ] 폰트 8pt 이상
- [ ] 트리·블록·코드 모두 채워짐
