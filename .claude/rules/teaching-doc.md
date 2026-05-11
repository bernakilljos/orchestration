# 강의·교재·가이드 문서 작성 규칙

> **출처**: 2026-05-11 사용자 깐깐 검토 — "그림 풀이만 하고 우리 시스템 매핑·강점/약점·강추 빠짐 = 전수조사 위반"

## 적용 범위

다음과 같은 산출물 작성 시 **반드시 적용**:
- 강의 노트 (.docx, .md, .pdf)
- 교재
- 사용 가이드
- 튜토리얼
- 외국어 자료의 한글 번안

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

## 강화 (5중 박기)

1. memory: `feedback_teaching_doc_format.md`
2. CLAUDE.md § 7-13번
3. 이 파일
4. 글로벌 CLAUDE.md + setup/templates/global-CLAUDE.md
5. `plugins/exec_orch/hooks/hook-00-init.sh` 매 세션 출력

## 참조

- `.claude/rules/failure-mode.md` § 전수조사 위반 안티패턴
- `.claude/rules/best-practices.md` § 전수조사 의무 (5단계 완주) 5단계
