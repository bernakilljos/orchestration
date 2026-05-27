# 강의·교재·가이드 문서 작성 규칙

> **출처**: 2026-05-11 사용자 깐깐 검토 — "그림 풀이만 하고 우리 시스템 매핑·강점/약점·강추 빠짐 = 전수조사 위반"

## 적용 범위

다음과 같은 산출물 작성 시 **반드시 적용**:
- 강의 노트 (.docx, .md, .pdf)
- 교재
- 사용 가이드
- 튜토리얼
- 외국어 자료의 한글 번안
- **인포그래픽 / HTML 렌더링 산출물** (render-*.py 포함)

## 각 챕터 필수 8 섹션

| # | 섹션 | 빠지면 |
|---|---|---|
| 1 | 📚 핵심 한 줄 | 챕터 의미 모호 → 위반 |
| 2 | 📊 표 (비교·구조) | 글로만 풀면 전수조사 위반 |
| 3 | 🌊 흐름도 / 단계 | 인과·순서 없음 → 전수조사 위반 |
| 4 | 💪 강점 | 왜 좋은지 모름 → 위반 |
| 5 | ⚠️ 약점·주의 | 함정 못 피함 → 위반 |
| 6 | ⭐ 강추 시점 | 언제 써야 할지 모름 → 위반 |
| 7 | 🎯 우리 시스템 매핑 | 외부 개념만 정리 → 전수조사 위반 (orchestration_v1 안 봤다) |
| 8 | 🧪 점검 1줄 | 자가 검증 없음 → 위반 |

## 톤 규칙

- **5살 청자 가정**. 어려운 단어 즉시 풀이.
- 1인칭 "저", 친근.
- 약어 (RAG, MCP, LRM 등) 첫 등장 시 풀어쓰기 (한글 + 영문).
- 일상 비유 풍부. 회사·도서관·요리 같은 익숙한 영역.

## 이미지 규칙 (강화 — 2026-05-11 v2)

### 원칙: **한글로 대체** (영어 + 한글 X)
- 외국어 인포그래픽 = 한글 다이어그램으로 **대체**.
- 영어 원본은 부록·참고에만. 본문 챕터엔 한글만.

### 품질 기준: **다이어그램 = SVG + 화살표 + 흐름**
- 단순 박스/표만 = 다이어그램 아님. 그것은 표.
- 다이어그램이려면:
  - ✅ **화살표** (방향성 있는 흐름)
  - ✅ **SVG 또는 HTML/CSS 기반** (matplotlib 박스만은 부족)
  - ✅ **시각적 위계** (색·크기·아이콘·그라데이션)
  - ✅ **인포그래픽 수준의 미관** (영어 원본 대비 부족하면 위반)

### 도구 우선순위
1. **HTML/CSS + SVG → Playwright PNG** (가장 강력 — design_ppt 패턴)
2. **Mermaid CLI** (flowchart·tree 표준)
3. matplotlib (마지막 수단, 단순 도표 OK)

### 금기
- 단순 박스만 = "다이어그램 아닌 표" — 위반
- 화살표 없음 = 흐름 없음 — 위반
- 영어 원본과 같이 둠 = "대체 안 함" — 위반

## 막힐 때

답이 안 나오면 — task-instruction.md 작성 후 codex/gemini 한테 위임.
단 "우리 시스템 매핑" 같은 메타 분석은 Claude 가 직접 (외부 모델은 우리 코드베이스 모름).

## 페이지 콘텐츠 fit (H1+callout+이미지+표 합산)

이미지 비율 검증만으로 부족. 페이지에 들어가는 **모든 요소 합산** 후 fit 검증.

### 페이지 콘텐츠 누적 (landscape A4 7.33 inch 사용 height)

| 요소 | 평균 height (inch) |
|---|---|
| H1 제목 | 0.55 |
| callout | 0.5 |
| 본문 줄 | 0.18 / 줄 |
| bullet | 0.2 / 줄 |
| caption | 0.25 |
| 표 row | 0.3 |
| 안전 여유 | 0.3 |

### 자동 계산 의무

빌더 script 의 IMG 호출 시 누적 height 추적:
```python
tracker = PageLayoutTracker("docx-landscape")
tracker.add("h1"); tracker.add("callout")
max_h = tracker.image_max_height(png_ratio)
IMG(doc, png, max_height=max_h)
```

### 증상 = 같은 문제

| 증상 | 원인 |
|---|---|
| 핵심 한 줄 후 빈 여백 | 이미지 페이지 한계 초과 → 다음 페이지 |
| 이미지 짤림 | full_page=True + 콘텐츠 길음 |
| 글씨 안 보임 | 이미지 작아져서 폰트 비율 ↓ |

→ 셋 다 PageLayoutTracker 로 한 번에 해결.

상세 skill: `plugins/exec_orch/skills/auto-layout-fit.md`

## 페이지 fit 사전검증 (모든 산출물 — docx · pptx · pdf)

이미지를 어떤 산출물에 넣기 **전에 반드시** 검증.

### 산출물별 페이지 비율표 (margin 제외 사용 영역)

| 카테고리 | 산출물 | 비율 (h/w) | 권장 viewport |
|---|---|---|---|
| **문서** | docx portrait A4 | 1.46 | 1100×1600 |
| | docx landscape A4 | 0.69 | 1600×1100 |
| | pdf A4 portrait | 1.41 | 1100×1550 |
| | pdf A4 landscape | 0.71 | 1600×1130 |
| | letter portrait | 1.29 | 1100×1420 |
| | letter landscape | 0.77 | 1600×1230 |
| | A3 / A5 (portrait) | 1.41 | 비율 동일 |
| **슬라이드** | pptx 16:9 / Google Slides / Keynote | 0.54 | 1920×1040 |
| | pptx 4:3 | 0.71 | 1440×1020 |
| **전자책** | epub | 1.50 | 1100×1650 |
| | kindle | 1.60 | 1100×1760 |
| **영상** | video 16:9 (YouTube) | 0.5625 | 1920×1080 |
| | video 9:16 (Shorts·Reels·TikTok) | 1.78 | 1080×1920 |
| | youtube-thumbnail | 0.5625 | 1280×720 |
| **소셜** | instagram-square | 1.0 | 1080×1080 |
| | instagram-story | 1.78 | 1080×1920 |
| | instagram-portrait (4:5) | 1.25 | 1080×1350 |
| | facebook-cover | 0.524 | 1640×859 |
| | twitter-card | 0.563 | 1200×675 |
| | linkedin-post | 1.0 | 1080×1080 |
| **기타** | business-card | 0.572 | 1050×600 |
| | poster-a2 | 1.41 | 1100×1550 |

→ 전체 RATIOS dict 는 `.claude/scripts/verify-image-fit.py` (환경변수 `FIT_TARGET=<key>`)

### 검증 방법 (PIL 로 PNG 비율 측정)
```python
from PIL import Image
ratio = h / w   # 측정
diff = abs(ratio - EXPECTED_PAGE_RATIO)
if diff > 0.05: FAIL — 짤림 또는 빈 공간
```

### 자동화
- 빌더 script 의 IMG/INSERT 함수에 **PIL 비율 측정 + 자동 width/height 선택** 의무
- 사후 검증: `.claude/scripts/verify-image-fit.py` (hook-09 자동 발동)
- hook-09 패턴: `(build|generate|render)-*-(ppt|doc|diagrams|pdf|html).py`

### PNG 빌드 (Playwright)
- **viewport 비율을 페이지 비율로 강제**: `viewport={"width":1600, "height":1100}` = 1.45:1 (landscape)
- `full_page=False` + `clip` 사용 — 콘텐츠 늘어남 방지

### 임베드 (python-docx)
- `width=W` 만 주지 말 것 — height 비율 유지로 페이지 초과 위험
- `PIL` 로 비율 확인 후 `width` 또는 `height` 자동 선택
- `max_height` 파라미터로 페이지 한계 자동 적용

### 전수조사 위반 안티 패턴
- 비율 검증 없이 빌드 → 사용자가 짤린다 알림 → fix = **사용자 노동 ↑, 위반**
- PIL 한 줄로 측정 가능. 빌드 전 하라.

## 산출물 종류별 visual 검증 의무 (PNG OCR ≠ 산출물 안)

원본 PNG 의 OCR 통과 ≠ docx/pptx/pdf 안 실제 출력 OK. **산출물 종류별로 그 산출물을 직접 봐야**.

| 산출물 | visual 검증 방법 | 도구 |
|---|---|---|
| docx | docx → PDF → 페이지 PNG → Read tool | `verify-docx-visual.py` (Word COM + PyMuPDF) |
| pptx | pptx → 슬라이드 PNG → Read tool | `verify-ppt-overflow.py` + python-pptx export |
| pdf | pdf 페이지 PNG → Read tool | PyMuPDF |
| html | Playwright headless 캡쳐 PNG → Read tool | `build-*-html-diagrams.py` 자체 |
| 원본 PNG | OCR/visual | `verify-image-fit.py` + Read tool |

### 의무 흐름 (산출물 빌드 시)
1. 빌드 (`build-*-doc.py` / `build-*-ppt.py` 등)
2. **1차 검증**: paragraph/slide 구조 (`verify-docx-pages.py` / `verify-ppt-overflow.py`)
3. **2차 visual 검증**: 산출물 → PNG export → Read tool 로 시각 확인 (필수)
4. PASS 후 보고. FAIL → 자동 재수정 (max 3) → 보고

### 금기
- PNG OCR 만 보고 "통과" 보고 = 위반 (산출물 안에서는 다를 수 있음)
- 빌드 후 visual 확인 안 하고 "수정했습니다" = 전수조사 위반
- docx 작업 중인데 PNG 만 봄 = 위반 (docx 봐야)
- ppt 작업 중인데 pptx 안 봄 = 위반

### 자동 발동 (hook-09)
- `build-*-doc.py` PostToolUse → `verify-docx-visual.py` 자동 export → systemMessage 로 Read 의무 알림
- `build-*-(ppt|pptx).py` PostToolUse → `verify-ppt-overflow.py` + 슬라이드 PNG export → Read 의무 알림
- `build-*-(diagrams|doc|html).py` PostToolUse → `verify-image-whitespace.py` (PNG 흰 여백 ≥5% 검출)

## PNG 빌더 작성 공통 원칙 — 짤림·여백 동시 방지 (산출물 비율별)

PNG 콘텐츠가 viewport 안에 **정확히 fit**. 초과 = 잘림. 부족 = 흰 여백.
**산출물 비율 일치 우선** — viewport 비율 ≠ 산출물 inside 비율이면 둘 중 하나 발생.

### 산출물별 viewport 비율 (height/width)

| 산출물 | inside 비율 | 권장 viewport |
|---|---|---|
| docx A4 landscape | 0.70 | 1300×910 또는 1300×900 |
| docx A4 portrait | 1.46 | 1100×1600 |
| pdf A4 landscape | 0.71 | 1300×920 |
| pptx 16:9 | 0.54 | 1920×1040 |
| pptx 4:3 | 0.71 | 1440×1020 |
| 영상 16:9 | 0.56 | 1920×1080 |
| 인스타 square | 1.0 | 1080×1080 |
| 카카오 카드뉴스 | 1.0 | 1080×1080 |

→ 산출물 비율과 PNG viewport 비율 일치 = 흰 여백 0 + 잘림 0

### 공통 한계 (viewport size 무관)

| 항목 | 한계 | 비율 기준 |
|---|---|---|
| **body padding** (위/좌·우/아래) | ≤2% / ≤2% / ≤1.5% viewport size | viewport 1300×900 = 24/24/14px |
| **banner content** | **한 줄 이내** — `<br>` 금지 | content ≥2 줄 = 잘림 트리거 |
| **banner padding** (위·아래) | ≤1% viewport height | 1300×900 = 10px |
| **table row 개수** | viewport height / row height (안전 25px) | 1300×900 = 25 row 이론, 안전 **7 row** |
| **grid 카드 (1 column)** | row × col ≤ viewport / (card_min+gap) | 1300×900 + 카드 300×300 = 3×3 = 9 |
| **flow-step (수직 흐름)** | (viewport - title - banner) / step_height | 1300×900 + step 80px = 6 step |
| **콘텐츠 margin** | ≤1.5% viewport size | 1300×900 = 14px |
| **page() h param 우선순위** | viewport 강제 (height:fixed) | h>viewport_height = overflow:hidden 잘림 |

### 빌더 작성 공통 패턴 (모든 산출물 공통)

```css
/* 산출물 비율 = viewport 비율 (필수) */
body {
  width:{W}px; height:{H}px;              /* 산출물 비율 일치 */
  padding:{H*0.02}px {W*0.018}px;         /* 비율 기반 */
  display:flex; flex-direction:column;
  justify-content:space-between;           /* 콘텐츠 자연 분배 — 흰 여백 0 */
  overflow:hidden;                         /* 초과 잘림 명시 */
}
.banner {
  padding:{H*0.012}px {W*0.012}px;
  margin-top:auto;                         /* 페이지 끝 fixed */
}
.banner-title { font-size:{H*0.024}px; }   /* 비율 기반 폰트 */
.banner-content { font-size:{H*0.018}px; } /* 한 줄만! */
```

### 사후 검증 (산출물 무관 자동 발동)

| 단계 | 도구 | hook |
|---|---|---|
| PNG 생성 후 | `verify-image-whitespace.py` (흰 여백 ≥5% WARN) | hook-09 |
| 산출물 임베드 후 | `verify-docx-visual.py` / `verify-ppt-overflow.py` 등 산출물별 | hook-09 |
| 진짜 잘림 검출 | OCR (easyocr/tesseract) | 미설치 시 Read tool |

### 공통 금기

- viewport 비율 ≠ 산출물 inside 비율 → 잘림 또는 흰 여백 (둘 중 하나)
- banner content `<br>` 또는 두 줄 → 마지막 줄 잘림
- body padding > 2% viewport → 흰 여백 자투리
- table row > 안전한계 → 마지막 row 안 보임
- body height < 콘텐츠 + min-height 큼 → overflow:hidden 잘림
- 콘텐츠 stretch X (flex-grow 없음) → 박스 위로 몰림 + 아래 여백

### 학습 사례 (참고 — 보편 원칙 적용)

| 사건 | 위반 원칙 | Fix |
|---|---|---|
| 13 banner 잘림 | banner content 2 줄 (1줄 한계 위반) | 한 줄로 |
| 17 트리 잘림 | font 큼 (viewport size 무시) | 비율 기반 축소 |
| 19 5 RULES 안 보임 | section title 32px (viewport 4% 위반) | 비율 기반 |
| 02 banner 안 보임 | context-arrow height 누적 (콘텐츠 분배 X) | display:none |
| 09 box 잘림 | h param > viewport (overflow 위반) | height 강제 |
| 10 9 row 중 6 만 | card padding > 2% (한계 위반) | 비율 기반 |

## 듀얼 모니터 환경 — visual 검증 도구 선택

사용자 환경 = **듀얼 모니터**. screenshot 도구는 모니터 영향 받음. headless visual 우선.

| 도구 | 모니터 영향 | 권장 |
|---|---|---|
| `verify-docx-visual.py` (Word COM → PDF → PyMuPDF PNG) | ❌ 없음 (headless) | ✅ 1순위 |
| `build-*-html-diagrams.py` (Playwright headless) | ❌ 없음 | ✅ |
| Read tool (PNG 직접) | ❌ 없음 (파일 기반) | ✅ |
| pyautogui / mss screenshot | ⚠️ 메인 모니터 또는 듀얼 합산 | ❌ 금지 (모니터 의존) |

### 금기
- 듀얼 모니터에서 `pyautogui.screenshot()` / `mss.grab()` 으로 캡처 → 잘못된 모니터 캡처 위험
- 사용자에게 "스크린샷 보내주세요" 노동 떠넘김 — verify-docx-visual.py 로 헤드리스 자동

### 강추 패턴
- docx 안 visual 확인 → `verify-docx-visual.py docx_path "pages"` → `_visual/page-NNN.png` Read
- PNG OCR 확인 → `Read` tool 로 직접 (모니터 무관)

## PNG 흰 여백 자동 검증 의무 (banner 아래 흰 공간 등)

PNG 자체 안 콘텐츠 끝 ~ PNG 끝 사이 흰 공간 (banner 아래 등) **5% 초과 = 위반**.
사용자가 docx 열어보면 "이미지 아래 여백 많네" 호소 → 미리 방지.

### 검출 패턴

| 위치 | 측정 | 한계 |
|---|---|---|
| 상하 흰 띠 | row 별 콘텐츠 픽셀 분석 | ≥5% PNG 높이 = WARN |
| 좌우 흰 띠 | col 별 콘텐츠 픽셀 분석 | ≥5% PNG 폭 = WARN |

### 자동 도구
- `.claude/scripts/verify-image-whitespace.py` — PIL bbox 측정
- hook-09 가 build/generate/render-*-(diagrams|doc|html).py PostToolUse 자동 발동

### 금기
- PNG 빌더에서 콘텐츠 컨테이너 height < viewport height = WARN
- body padding 큼 + 콘텐츠 끝까지 안 감 = WARN
- viewport 비율 ≠ 산출물 inside 비율 = 사용자 "여백" 호소 트리거

### 강추 패턴
- viewport height = docx inside height × (PNG width / docx inside width) — 비율 일치
- body padding ≤ 24px
- 마지막 콘텐츠 (banner) margin-bottom 0
- 콘텐츠 부족 시 flex-grow + 자연 stretch, 보기 어색하면 콘텐츠 추가

## 산출물 명명 — 버전 접미사 금지

빌드 결과물 (.docx/.pptx/.pdf 등) 에 **자동 -v2, -v3 폴백 금지**.

### 올바른 패턴 (백업 + 덮어쓰기)
- 빌드 전: `original.docx → original.docx.bak`
- 빌드: `original.docx` 자리에 새로 저장
- 원본 잠겨있으면: 사용자에게 알림 ("원본 닫아주세요"), 자동 -v2 X

### 금지
- `if locked: save("...-v2.docx")` ❌
- 같은 산출물에 v2, v3, v4 누적 ❌

### 허용 (사용자 명시 요청 시)
- "v2 로 저장해" → OK
- "스냅샷 만들어줘" → OK

## 렌더링 기반 전수검사 (render-*.py / HTML 인포그래픽)

HTML/CSS 기반 인포그래픽·카드 레이아웃 산출물은 **렌더링 후 시각 검사** 필수.
CSS 코드만 보고 "여백 없다" 판단 = 전수조사 위반.

### 의무 사이클

1. **렌더링** — Playwright 로 screenshot (viewport = 산출물 비율)
2. **시각 검사** — Read tool 로 출력 이미지 페이지별 전수 검사
3. **여백 탐지** — 아래 검사 항목 모두 체크
4. **수정** — 레이아웃 대변경 X, 콘텐츠 추가로 채움
5. **재렌더링** — 수정 후 다시 렌더링
6. **재검사** — 2~5 반복 (최소 2회 사이클)

### 검사 항목 (시각 기준, 코드 X)

| 항목 | 판정 |
|---|---|
| 빈 배경 면적 (카드 외부) | 카드 간 gap > 8px 가시 = 위반 |
| 카드 사이 공백 | 카드 내 마지막 항목 → 카드 하단 여백 가시 = 위반 |
| 중앙 주변 공백 | 이미지 주변 빈 영역 가시 = 위반 |
| 텍스트 밀도 부족 | 카드 안 항목 3개 이하 = 위반 |
| 아이콘 부족 | SVG 아이콘 없는 리스트 = 위반 |
| 정보량 부족 | 전체 페이지에서 빈 공간 > 정보 면적 = 위반 |
| 치우친 레이아웃 | 한쪽 컬럼만 긴 경우 = 위반 |
| 비어 보이는 영역 | 주관적 "비어 보임" = 위반 |

### 여백 수정 도구 (레이아웃 대변경 X)

빈 공간 발견 시 다음 요소를 추가:
- 짧은 설명 문장 / 키워드 / 미니 카드 / 포스트잇
- 아이콘 / 메모 / 체크리스트 / 태그
- 화살표 설명 / 작은 인사이트 박스

### 성공 기준

> 페이지를 처음 봤을 때 빈 공간보다 정보가 먼저 보이는 상태.

### 자동화

- hook-09 가 `render-*.py` 실행 감지 → systemMessage 로 전수검사 의무 알림
- `verify-image-whitespace.py` 가 렌더 출력 폴더 자동 스캔

### 금기

- CSS 코드만 보고 "여백 없다" 보고 = 전수조사 위반
- 1회 렌더링만 하고 "완료" = 전수조사 위반 (최소 2회 사이클)
- 사용자가 여백 지적한 후에야 fix = 전수조사 위반
- 페이지별 하드코딩 = 최후 수단 (전역 Rule/Token 우선)
- 샘플링 검사 = 전수조사 위반 (1페이지부터 마지막까지 전부)

## 디자인 시스템 토큰 (멀티페이지 일관성)

멀티페이지 HTML 렌더링 산출물은 **CSS 변수 토큰** 기반으로 통일.
페이지별 다른 스타일 = 시스템 결함.

### 필수 토큰 카테고리

| 카테고리 | 토큰 예시 | 규칙 |
|---|---|---|
| **Spacing** | `--gap-section`, `--gap-card`, `--pad-card` | 전 페이지 동일 |
| **Typography** | `--font-h3`, `--font-body-size`, `--line-height` | 계층 고정 |
| **Color** | `--color-accent`, `--color-border`, `--color-card` | 팔레트 통일 |
| **Radius** | `--radius-card`, `--radius-tag` | 곡률 통일 |
| **Shadow** | `--shadow-card` | 깊이 통일 |

### 컴포넌트 일관성 규칙

- `.card` — 모든 카드 동일 padding/border/shadow
- `.tag` — 모든 태그 동일 font/padding/radius
- `.btm-card` — 하단 카드 동일 구조
- `h3` — 모든 카드 제목 동일 font-size/color/border

### 전역 Rule 승격 기준

동일 문제가 **2페이지 이상**에서 발견되면:
1. 개별 수정 X
2. CSS 변수 토큰으로 승격
3. COMMON_CSS 에 반영
4. 전 페이지 자동 적용

## 강화 (5중 박기)

1. memory: `feedback_teaching_doc_format.md`
2. CLAUDE.md § 7-13번
3. 이 파일
4. 글로벌 CLAUDE.md + setup/templates/global-CLAUDE.md
5. `plugins/exec_orch/hooks/hook-00-init.sh` 매 세션 출력

## 참조

- `.claude/rules/failure-mode.md` § 전수조사 위반 안티패턴
- `.claude/rules/best-practices.md` § 전수조사 의무 (5단계 완주) 5단계
