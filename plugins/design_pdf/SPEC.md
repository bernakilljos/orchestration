# design_pdf — 상세 스펙 (Phase 2)

> **2026-04-30 R51 흡수**: design_ppt 의 디자인 시스템 + 차트/SVG/카드 그리드 패턴 + Screens 워크플로우 적용.
> **핵심**: HTML/CSS → Playwright → PDF · A4 / Letter / 1920×1080 (디지털 PDF) 모두 지원.

## 목표

- PDF 생성·양식·서명·암호화 (mcp_docs 는 파싱만)
- design_ppt 와 동일한 디자인 시스템 공유 (gold/sage/plum/terra/deep-gold)
- README 표지 · 마케팅 1페이지 · 보고서 N페이지 모두 동일 워크플로우

## 워크플로우 (HTML/CSS → PDF)

```
[1] HTML 작성 (design-system.css 임포트) → [2] Playwright PDF 출력
                                                   ↓
                                              outputs/pdf/<date>/<name>.pdf
```

### Step 1 — HTML 템플릿
- `outputs/pdf/<name>/html-source/` 에 단일 또는 N 개 HTML
- design_ppt 의 `_styles.css` 또는 design-system.css 그대로 import 가능
- A4 비율 = `width: 794px; height: 1123px` (96dpi 기준) / Letter = `816×1056`
- 디지털 PDF (16:9) = `1920×1080`

### Step 2 — Playwright PDF 출력
```python
await page.goto(html_url, wait_until="networkidle")
await page.pdf(
    path=str(out),
    format="A4",                         # 또는 width/height 직접 지정
    print_background=True,               # 배경 그라디언트 출력
    margin={"top":0,"right":0,"bottom":0,"left":0},
)
```

## 커맨드 스펙

### `/pdf-generate`
HTML·Markdown → PDF 변환

**입력**: HTML 또는 Markdown 파일 경로 / 형식 (A4 / Letter / Digital)
**출력**: `outputs/pdf/<date>/<name>.pdf`
**공통**: `--dry-run` 지원, 구조화 로그

### `/pdf-fill`
양식(form) 자동 채우기 — PyPDF2 / pdfplumber

**입력**: 원본 PDF + 데이터 매핑 JSON
**출력**: 채워진 PDF

### `/pdf-sign`
전자서명·직인 삽입

**입력**: PDF + 서명 이미지 / 좌표 / 페이지 번호
**출력**: 서명된 PDF
**참조**: 전자서명법 — `skill-pdf-compliance`

### `/pdf-secure`
암호화·워터마크

**입력**: PDF + 비밀번호 / 워터마크 텍스트·이미지
**출력**: 보호된 PDF

## 스킬 스펙

### `skill-pdf-form`
PDF 양식 필드 매핑·검증

### `skill-pdf-compliance`
전자서명 법적 요건 (전자서명법)

### `skill-pdf-design-system` ⭐ (R51 추가)
HTML/CSS 디자인 시스템 공유 — design_ppt 와 동일 팔레트·폰트·차트 패턴.

**핵심 가이드**:
- `_styles.css` (docs/screens/our-html/) 또는 design-system.css 임포트
- A4 PDF 시 padding 80px / 1920px PDF 시 padding 100px
- 차트 / SVG / 카드 그리드 패턴은 `design_ppt/skills/skill-ppt-pitfalls.md § 13` 참조
- Screens 워크플로우는 § 14 참조

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] **A4 / Letter / Digital 3 모드 지원**
- [ ] **design-system.css 임포트 검증**
- [ ] **차트 / SVG 정상 출력 (`print_background: true`)**

## 워크플로우 비교

| 도구 | 출력 | 디자인 시스템 | 차트 / SVG |
|------|------|--------------|-----------|
| `/design_ppt` | PPTX | ✓ | ✓ |
| `/pdf-generate` (R51) | PDF | ✓ (공유) | ✓ |
| `/render-screens` | PNG | ✓ (공유) | ✓ |

세 도구 모두 동일 디자인 시스템 (gold/sage/plum/terra/deep-gold) 사용 — **HTML 한 번 작성하면 PPT/PDF/PNG 모두 출력 가능**.
