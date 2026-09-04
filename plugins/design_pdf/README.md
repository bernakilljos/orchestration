# design_pdf — PDF 생성·양식·서명·암호화 (mcp_docs 는 파싱만)

> **Prefix**: `design_` | **버전**: 0.2 | **Status**: spec-only | **Phase**: 2
> **2026-04-30 R51 흡수**: design_ppt 의 디자인 시스템·차트·SVG 패턴 + Screens 워크플로우 적용.

##  현재 상태

**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.

## 🎨 디자인 시스템 (R51)

design_ppt 와 동일한 시각 시스템 공유:
- **팔레트**: gold #B8864E · sage #6B8E7F · plum #7A4E6B · terracotta #B25A3E · deep-gold #8A6235
- **폰트**: Pretendard Variable + JetBrains Mono + Fraunces
- **차트 / SVG / 카드 그리드** 패턴: `design_ppt/skills/skill-ppt-pitfalls.md § 13`
- **공통 CSS**: `docs/screens/our-html/_styles.css` 그대로 임포트

## 📋 커맨드

- `/pdf-generate`  기본 — HTML/CSS → Playwright → PDF (A4·Letter·Digital 1920×1080)
- `/pdf-fill` — 양식(form) 자동 채우기
- `/pdf-sign` — 전자서명·직인 삽입
- `/pdf-secure` — 암호화·워터마크

## 🧠 스킬

- **`skill-pdf-design-system`**  (R51 신규) — HTML→PDF 워크플로우 + 12 계명 + 안티패턴
- `skill-pdf-form` — PDF 양식 필드 매핑·검증
- `skill-pdf-compliance` — 전자서명 법적 요건 (전자서명법)

## 🔗 의존성

- **플러그인**: `exec_orch`, `design_ppt` (디자인 시스템 공유)
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env)
- **외부**: Playwright (HTML→PDF), pdf2image (검증용 PNG 변환)

## 🚀 빠른 사용

```bash
# A4 보고서
/pdf-generate "월간 보고서" A4

# 1920×1080 디지털 PDF (README 표지)
/pdf-generate "주제" Digital
```

워크플로우:
1. `outputs/pdf/<date>/html-source/<name>.html` 작성 (`_styles.css` 임포트)
2. Playwright 가 `print_background: true` 로 PDF 출력
3. pdf2image 로 PNG 변환 → Read tool 로 OCR 검증

## 상세 워크플로우

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

### 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] **A4 / Letter / Digital 3 모드 지원**
- [ ] **design-system.css 임포트 검증**
- [ ] **차트 / SVG 정상 출력 (`print_background: true`)**

### 워크플로우 비교

| 도구 | 출력 | 디자인 시스템 | 차트 / SVG |
|------|------|--------------|-----------|
| `/design_ppt` | PPTX | ✓ | ✓ |
| `/pdf-generate` (R51) | PDF | ✓ (공유) | ✓ |
| `/render-screens` | PNG | ✓ (공유) | ✓ |

세 도구 모두 동일 디자인 시스템 (gold/sage/plum/terra/deep-gold) 사용 — **HTML 한 번 작성하면 PPT/PDF/PNG 모두 출력 가능**.

## 📝 참조

- 워크플로우 + 함정: `skills/skill-pdf-design-system.md`
- 공통 디자인 시스템: `docs/screens/our-html/_styles.css`
- 차트 / SVG 패턴: `plugins/design_ppt/skills/skill-ppt-pitfalls.md § 13~14`
- 로드맵: `docs/2026-04-19/로드맵.md`
