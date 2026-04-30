---
name: pdf-design-system
description: |
  PDF 생성 시 design_ppt 와 동일한 디자인 시스템 (gold/sage/plum/terra/deep-gold) 사용.
  HTML/CSS → Playwright → PDF 워크플로우. A4·Letter·1920×1080 디지털 PDF 모두 지원.
  사용자가 "PDF 만들어줘", "/pdf-generate", "보고서 PDF", "PDF 표지" 등을 언급할 때 자동 활성화.
---

# PDF Design System — design_ppt 패턴 흡수 (R51)

> **출처**: 2026-04-30 R51 작업 — design_ppt 의 차트·SVG·카드 그리드 패턴을 PDF 에도 적용.
> **목적**: HTML 한 번 작성 → PPT / PDF / PNG 모두 출력.

---

## 1. 워크플로우

```
[1] HTML 작성 → [2] Playwright PDF → [3] OCR 검증 (PDF→PNG)
     ↑ design-system.css 또는 _styles.css 임포트
```

### Step 1 — HTML 템플릿
3 종 비율 지원:

| 모드 | 크기 | 용도 |
|------|------|------|
| A4 | 794×1123 (96dpi) | 보고서 · 문서 |
| Letter | 816×1056 | 미국 표준 |
| Digital | 1920×1080 | README · 마케팅 1 페이지 |

### Step 2 — Playwright PDF 출력
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto(html_url, wait_until="networkidle")
    await page.pdf(
        path=str(out),
        format="A4",                          # 또는 width/height
        print_background=True,                # 배경 그라디언트 출력
        margin={"top":0,"right":0,"bottom":0,"left":0},
        prefer_css_page_size=True,
    )
    await browser.close()
```

### Step 3 — OCR 검증
PDF → PNG 변환 후 Read tool 로 직접 봄.
```bash
# pdf2image 사용
python -c "from pdf2image import convert_from_path; \
  [im.save(f'page_{i+1}.png') for i,im in enumerate(convert_from_path('out.pdf', dpi=150))]"
```

---

## 2. 공통 디자인 시스템

design_ppt 의 `outputs/ppt-*/html-source/styles/design-system.css` 또는
`docs/screens/our-html/_styles.css` 그대로 import.

```html
<link href="../../docs/screens/our-html/_styles.css" rel="stylesheet">
<!-- 또는 -->
<style>
  :root {
    --gold:       #B8864E;
    --sage:       #6B8E7F;
    --plum:       #7A4E6B;
    --terracotta: #B25A3E;
    --deep-gold:  #8A6235;
    --ink:        #1A1D24;
    --stone:      #6E685C;
    --fog:        #D8D2C2;
    --cream:      #FAF5EA;
  }
</style>
```

폰트:
- **Pretendard Variable** — 본문 한글
- **JetBrains Mono** — 코드 / 라벨
- **Fraunces** — 큰 제목 (italic accent)

---

## 3. PDF 만의 주의사항

### 함정 1. `print_background: true` 누락
**증상**: 배경 그라디언트 / 색상 안 출력 (흰 배경만).
**해결**: `await page.pdf(..., print_background=True)`

### 함정 2. A4 화면이 잘림
**증상**: 1920×1080 HTML 을 A4 로 출력 → 우측·하단 잘림.
**해결**: HTML 의 `.canvas` width/height 를 A4 (794×1123) 로 변경 또는
`format="A4"` 대신 `width="1920px", height="1080px"` 직접 지정.

### 함정 3. 페이지 분할 안 됨
**증상**: 긴 콘텐츠가 1 페이지 안에 압축.
**해결**: CSS `@page { size: A4; margin: 0 }` + 페이지 분할 마커
```css
.page-break { page-break-after: always; }
@media print {
  .canvas { page-break-after: always; }
}
```

### 함정 4. 폰트 깨짐
**증상**: 한글 폰트 fallback → 시스템 기본.
**해결**: Playwright `wait_until="networkidle"` 충분, 추가 `wait_for_timeout(1500)` 으로 폰트 로드 대기.

### 함정 5. SVG 화살표 marker 누락
**증상**: PDF 에서 화살표 head 안 보임.
**해결**: `<defs>` 안에 marker 정의 + `marker-end="url(#name)"` — 인라인 SVG 만 안전 (외부 SVG `<img>` 는 marker 잃음).

---

## 4. 차트 · 다이어그램 · 카드 패턴

전부 `design_ppt/skills/skill-ppt-pitfalls.md § 13` 의 코드 그대로 사용 가능.
PDF 출력 시 배경 그라디언트 / box-shadow 도 정상 출력.

| 패턴 | 사용처 (PDF) |
|------|------|
| BEFORE/AFTER 막대 차트 (§ 13.A) | 비용 보고서 · ROI 슬라이드 |
| KPI sparkline (§ 13.B) | 월간 보고서 · 대시보드 PDF |
| Timeline 막대 (§ 13.C) | 프로젝트 진행 · 마일스톤 |
| SVG 다이어그램 (§ 13.D) | 시스템 구조도 · 조직도 |
| 표 → 카드 그리드 (§ 13.E) | FAQ · 트러블슈팅 카드 |
| 결정 트리 배너 (§ 13.F) | 의사결정 흐름도 |

---

## 5. Screens 워크플로우 활용

`docs/screens/our-html/*.html` 의 HTML 그대로 PDF 로도 출력 가능.

```python
# render-screens.py 와 같은 패턴, 출력만 PDF
async def render_pdf(html: Path, out: Path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width":1920,"height":1080})
        await page.goto(html.resolve().as_uri(), wait_until="networkidle")
        await page.wait_for_timeout(900)
        await page.pdf(path=str(out),
                       width="1920px", height="1080px",
                       print_background=True,
                       margin={"top":0,"right":0,"bottom":0,"left":0})
        await browser.close()
```

활용:
- README 표지 → arch-system-overview.pdf (1 페이지 1920×1080)
- 마케팅 카드 → func-cost-saving.pdf
- 보고서 → arch-* + func-* 여러 장 묶어 N 페이지 PDF

---

## 6. 빠른 체크리스트

- [ ] HTML 에 `_styles.css` 또는 design-system.css 임포트
- [ ] `.canvas` width/height = A4 / Letter / 1920×1080 중 하나 명시
- [ ] Playwright `print_background: true`
- [ ] `wait_until="networkidle"` + `wait_for_timeout(900)` 폰트 로드 대기
- [ ] 인라인 SVG (외부 `<img>` X) — marker 정상 출력
- [ ] 한글 폰트 = Pretendard Variable (cdn.jsdelivr.net)
- [ ] PDF 출력 후 pdf2image 로 PNG 변환 → Read tool 로 OCR 검증

---

## 7. 안티패턴

- ❌ `print_background: false` (기본값) — 배경 그라디언트 사라짐
- ❌ 외부 SVG `<img src="...svg">` — marker / gradient 일부 깨짐. 인라인 SVG 사용
- ❌ A4 비율 HTML 을 1920px PDF 출력 — 우측 큰 여백
- ❌ 페이지 분할 마커 없이 N 페이지 콘텐츠 — 한 페이지에 압축
- ❌ Iconify 비동기 로드 → wait 부족 시 아이콘 누락 → `wait_for_timeout(1500)` 권장

---

## 8. 출처

- design_ppt R51 (2026-04-30): commit `bfed0f1`
- 디자인 시스템: `outputs/ppt-*/html-source/styles/design-system.css`
- Screens: `docs/screens/our-html/_styles.css`
- 패턴 코드: `plugins/design_ppt/skills/skill-ppt-pitfalls.md § 13~14`
