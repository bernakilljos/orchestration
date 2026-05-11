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
callout(doc, "📚 핵심 한 줄", ch["핵심"]); tracker.add("callout")

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

## 강화 (5중 박기)

teaching-doc.md § 페이지 콘텐츠 fit / failure-mode.md § 전수조사 위반 안티패턴 / hook-00-init.sh / global-CLAUDE.md / memory feedback_full_page_content_fit.md

## 트리거

- "이미지 짤려", "여백 큰데", "글씨 안 보여" 같은 사용자 피드백
- 또는 새 빌더 script 작성 시 PageLayoutTracker 사용 의무
