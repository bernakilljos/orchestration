---
name: auto-layout-fit
description: docx/pptx/pdf 빌드 시 페이지 콘텐츠 (H1·callout·이미지·표·캡션 등) 합산 height 자동 계산 후 이미지 max_height 동적 조정. 빈 여백·짤림·글씨 작음 동시 해결.
---

# Auto Layout Fit — 페이지 자동 조정

빌더 script 에서 IMG/INSERT 호출 시 페이지에 이미 들어간 콘텐츠 height 누적 추적 → 남은 공간에 맞춰 이미지 자동 축소.

## 적용 시점

다음 도구를 사용하는 빌더 script:
- `build-arch-lecture-doc.py` (lecture 강의 doc)
- `generate-*-ppt.py` (PPT 빌더)
- 향후 `build-epub.py`, `render-pdf.py` 등

## 핵심 함수

```python
class PageLayoutTracker:
    """페이지 콘텐츠 height 누적 추적."""
    PAGE_LIMITS = {
        "docx-landscape": 7.33,  # A4 landscape 사용 영역 (inch)
        "docx-portrait":  9.5,
        "pptx-16:9":      6.7,
    }
    HEIGHTS = {  # 각 요소 평균 height
        "h1": 0.55,
        "h2": 0.4,
        "callout": 0.5,
        "para_line": 0.18,    # 줄당
        "bullet_line": 0.2,
        "caption": 0.25,
        "table_row": 0.3,
        "image_caption_pad": 0.15,
        "page_break_safety": 0.3,
    }

    def __init__(self, target="docx-landscape"):
        self.target = target
        self.used = 0.0

    def add(self, kind, count=1):
        self.used += self.HEIGHTS.get(kind, 0.2) * count

    def remaining(self):
        return self.PAGE_LIMITS[self.target] - self.used - self.HEIGHTS["page_break_safety"]

    def image_max_height(self, image_ratio):
        """남은 공간에서 이미지 max_height 자동 결정."""
        avail = self.remaining()
        return max(2.0, avail)  # 최소 2 inch 보장
```

## 빌더 통합 패턴

```python
tracker = PageLayoutTracker("docx-landscape")
H(doc, ch["title"], level=1); tracker.add("h1")
callout(doc, " 핵심 한 줄", ch["핵심"]); tracker.add("callout")

# 이미지 max_height 자동 계산
with Image.open(png) as im:
    ratio = im.size[1] / im.size[0]
max_h = tracker.image_max_height(ratio)
IMG(doc, png, max_height=max_h)
tracker.add_image(max_h)
```

## 검증

- 빌드 후 docx 페이지에 빈 여백 없음
- 이미지 짤림 없음
- 글씨 비율 적정 (PNG viewport 작을수록 화면 표시 ↑)

## PNG 빌더 공통 원칙 — 산출물 무관 보편 적용

PNG 콘텐츠가 viewport 안에 **정확히 fit**. viewport 비율 = 산출물 inside 비율 일치 시 잘림·여백 0.

### 산출물 비율 표 (보편 — 추가 시 확장)

| 산출물 | inside 비율 (h/w) | 권장 viewport |
|---|---|---|
| docx A4 landscape | 0.70 | 1300×910 |
| docx A4 portrait | 1.46 | 1100×1600 |
| pdf A4 landscape | 0.71 | 1300×920 |
| pptx 16:9 | 0.54 | 1920×1040 |
| pptx 4:3 | 0.71 | 1440×1020 |
| 영상 16:9 | 0.56 | 1920×1080 |
| 인스타 1:1 | 1.0 | 1080×1080 |

### 공통 한계 (viewport size 무관 — 비율 기반)

| 항목 | 한계 비율 | 1300×900 예시 |
|---|---|---|
| body padding (위/좌·우) | ≤2% viewport size | 24 / 24 px |
| body padding (아래) | ≤1.5% | 14 px |
| banner content | **한 줄 이내** (`<br>` 금지) | — |
| banner padding (위·아래) | ≤1% viewport height | 10 px |
| banner font (content) | ≤1.8% viewport height | 16 px |
| table row 개수 | ≤(viewport_h - title - banner) / 25px | 7 row |
| grid 카드 | ≤viewport / (card_min + gap) | 3×3 = 9 |
| flow-step | ≤(viewport_h - title - banner) / step_height | 6 |
| 콘텐츠 margin | ≤1.5% viewport size | 14 px |

### 공통 패턴 (모든 빌더 — 산출물 무관)

```css
body {
  width:{W}px; height:{H}px;            /* 산출물 비율 일치 */
  padding:{H*0.02}px {W*0.018}px;       /* 비율 기반 */
  display:flex; flex-direction:column;
  justify-content:space-between;         /* 콘텐츠 자연 분배 */
  overflow:hidden;
}
.banner { padding:{H*0.012}px {W*0.012}px; margin-top:auto; }
.banner-content { font-size:{H*0.018}px; /* 한 줄만 */ }
```

### 공통 금기 (보편)

- viewport 비율 ≠ 산출물 inside 비율 → 잘림 or 여백
- banner content 두 줄 → 마지막 줄 잘림
- body min-height > viewport height → overflow 잘림
- table row > 한계 → 마지막 안 보임
- body padding > 2% → 흰 여백 자투리
- 콘텐츠 stretch X → 박스 위로 몰림 + 아래 여백

### 학습 사례 (참고 — 원칙 적용 예시)

| 사건 | 위반 원칙 | Fix |
|---|---|---|
| 13 banner 잘림 | banner 1줄 한계 위반 | 한 줄로 |
| 17 트리 잘림 | font 크기 비율 무시 | 비율 기반 |
| 19 5 RULES 안 보임 | section title 4% 초과 | 비율 기반 |
| 02 banner 안 보임 | 콘텐츠 분배 X | display:none + flex |
| 09 box 잘림 | h > viewport | height 강제 |
| 10 9 row 중 6 만 | padding > 2% | 비율 기반 |

## 강화 (5중 박기)

teaching-doc.md § 페이지 콘텐츠 fit / failure-mode.md § 전수조사 위반 안티패턴 / hook-00-init.sh / global-CLAUDE.md / memory feedback_full_page_content_fit.md

## flex 박스 안 SVG / 이미지 — 빈 영역 방지 (svg-deco 패턴)

`flex:1 1 0` 으로 grow 하는 박스 안에 max-width/max-height 제한된 SVG 를 두면
**박스는 큰데 SVG 는 작은 빈 영역** 발생. 사용자 "여백 있네" 호소의 대표 원인.

### 진단

```css
/*  빈 영역 트리거 */
.svg-deco { flex:1 1 0; min-height:60px; }
.svg-deco svg { max-width:200px; max-height:280px; }  /* 박스 > SVG → 여백 */

/*  빈 영역 0 */
.svg-deco { flex:1 1 0; min-height:60px; padding:4px; }
.svg-deco svg { width:100%; height:100%; display:block; }
/* viewBox 비율 = 컨테이너 비율 + preserveAspectRatio="xMidYMid meet" */
```

### 정량 임계치

| 항목 | 한계 | 위반 시 |
|---|---|---|
| `flex:1` 박스 내 SVG `max-width` | **금지** (또는 컨테이너 100%) | 좌우 여백 |
| `flex:1` 박스 내 SVG `max-height` | **금지** (또는 컨테이너 100%) | 상하 여백 |
| SVG viewBox 비율 (h/w) | 컨테이너 비율 ±20% 이내 | preserveAspectRatio 로 letterbox 발생 |
| SVG 요소 분포 | **viewBox 모서리 4구역에 각 1개+** | 중앙만 채워서 여백 |
| svg 안 텍스트만 / 단일 도형만 | 금지 | 빈 영역 |

### svg-deco 작성 체크리스트 (산출물 무관 보편)

- [ ] `width:100%; height:100%; display:block` (max-width/height 제거)
- [ ] viewBox 비율을 컨테이너에 맞춰 설정 (예: 240×290 ≈ 0.83)
- [ ] `preserveAspectRatio="xMidYMid meet"` 명시
- [ ] 요소를 viewBox 4 모서리에 분산 (별·잎·식물·텍스트)
- [ ] 배경 halo / 그라데이션으로 cream 단색 영역 < 30%
- [ ] 본문 텍스트 1줄 (다른 요소와 겹치지 않게)

### 사후 검증 (verify-render-coverage.py)

```bash
python .claude/scripts/verify-render-coverage.py <png-or-dir>
# 그리드 셀별 콘텐츠 밀도 (edge+color variance) 측정 → 20% 미만 셀 클러스터 = WARN
# crop PNG 자동 생성 → Read tool 로 시각 확인 의무
```

hook-09 가 `render-*.py` / `build-*.py` / `generate-*.py` PostToolUse 자동 발동.

## 트리거

- "이미지 짤려", "여백 큰데", "글씨 안 보여", "공백 있네" 같은 사용자 피드백
- 또는 새 빌더 script 작성 시 PageLayoutTracker + svg-deco 패턴 사용 의무
