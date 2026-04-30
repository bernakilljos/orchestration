---
description: "HTML/CSS → Playwright → PDF · A4·Letter·Digital(1920×1080) 모두 지원"
allowed-tools: Bash(python:*), Bash(playwright:*), Read, Write, Edit, Glob
---

## Context

- 플러그인: `design_pdf` (status=spec-only, phase=2)
- 워크플로우: HTML/CSS → Playwright → PDF (design_ppt 와 동일 디자인 시스템)
- 출력: `outputs/pdf/<date>/<name>.pdf`
- DRY_RUN 환경변수: `${DRY_RUN:-false}`

## Your task

### 빠른 사용

```
/pdf-generate "주제" A4
/pdf-generate "주제" Digital   # 1920×1080 디지털 PDF (README 표지 등)
/pdf-generate "주제" Letter
```

### 워크플로우 (design_ppt 와 동일)

```
[1] HTML 작성 → [2] Playwright PDF → [3] OCR 검증 (pdf2image)
```

### Step 1 — HTML 작성

**A4 보고서**:
```html
<style>
  @page { size: A4; margin: 0; }
  .page { width: 794px; min-height: 1123px; padding: 60px 70px;
          page-break-after: always; }
</style>
```

**Digital 1920×1080**:
```html
<style>
  .canvas { width: 1920px; height: 1080px; padding: 80px 100px;
            display: flex; flex-direction: column; }
</style>
```

**공통**: `_styles.css` (docs/screens/our-html/) 또는 design_ppt 의 design-system.css 임포트.
색상 / 폰트 / 차트 / SVG 패턴 전부 그대로 활용 가능.

### Step 2 — Playwright PDF 출력

```python
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page(viewport={"width": 1920, "height": 1080})
    await page.goto(html_url, wait_until="networkidle", timeout=20000)
    await page.wait_for_timeout(900)            # 폰트·아이콘 로드 대기
    await page.pdf(
        path=str(out),
        format="A4",                            # 또는 width="1920px", height="1080px"
        print_background=True,                  # ← 필수, 배경 그라디언트 출력
        margin={"top":0,"right":0,"bottom":0,"left":0},
        prefer_css_page_size=True,
    )
    await browser.close()
```

### Step 3 — OCR 검증

```bash
# pdf2image 로 PNG 변환 후 Read tool 로 직접 봄
python -c "from pdf2image import convert_from_path; \
  [im.save(f'page_{i+1}.png') for i,im in enumerate(convert_from_path('out.pdf', dpi=150))]"
```

### 12 계명 (design_ppt 의 15 계명에서 PDF 적용 항목)

1. **`print_background: true`** 필수 — 배경 그라디언트 출력
2. **`wait_for_timeout(900~1500)`** — 폰트·Iconify 로드 대기
3. **`.canvas` 크기 = 출력 모드와 일치** (A4=794×1123 / Digital=1920×1080)
4. **인라인 SVG 만 사용** — `<img>` 외부 SVG 는 marker / gradient 깨짐
5. **페이지 분할 마커** = `page-break-after: always` (N 페이지 PDF 시)
6. **차트 막대 width 는 데이터 비율로 직접 계산** (예: `width: 8.3%`)
7. **SVG 다이어그램은 `<defs>` 에 gradient + marker 미리 정의**
8. **표 8 행+ 또는 폰트 16px 이하면 카드 그리드** (4×2 / 3×2 / 4×3)
9. **`.body` 에 `max-width` 절대 금지** — 우측 빈 여백
10. **design-system.css 임포트** — design_ppt 와 동일 시각 톤
11. **Sub-Agent "PASS" 거짓말에 속지 마라** — 직접 OCR 검증
12. **출력 후 PNG 변환해서 OCR** — Read tool 로 직접 보고 잘림 확인

### 참조

- 디자인 시스템 + 차트 패턴: `plugins/design_ppt/skills/skill-ppt-pitfalls.md § 13~14`
- PDF 전용 함정 / 안티패턴: `plugins/design_pdf/skills/skill-pdf-design-system.md`
- 공통 스타일: `docs/screens/our-html/_styles.css` 또는 `outputs/ppt-*/html-source/styles/design-system.css`
- 실구현은 플랫폼: `plugins/design_pdf/SPEC.md`

### 출력 구조

```
outputs/pdf/
├── <date>/
│   ├── <name>.pdf
│   └── html-source/
│       ├── <name>.html
│       └── _styles.css     (또는 ../docs/screens 참조)
```
