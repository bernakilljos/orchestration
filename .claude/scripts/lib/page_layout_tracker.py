"""page_layout_tracker.py — 페이지 콘텐츠 fit 추적 라이브러리

룰: .claude/rules/teaching-doc.md § 페이지 콘텐츠 fit
출처: feedback_full_page_content_fit.md

목적: H1·callout·이미지·표 등 요소들의 height 합산 → 페이지 한계 검증.
빌더 (build-*-doc.py) 가 IMG/INSERT 함수 호출 전 PageLayoutTracker 로 max_height 계산.

사용 예:
    from page_layout_tracker import PageLayoutTracker
    tracker = PageLayoutTracker("docx-landscape")  # A4 landscape
    tracker.add("h1")
    tracker.add("callout")
    max_h = tracker.image_max_height(png_ratio=0.75)
    IMG(doc, png, max_height=max_h)
    tracker.add("image", height=max_h)
    tracker.add("caption")
"""
from __future__ import annotations

# 페이지별 사용 가능 height (inch). margin 제외.
PAGE_USABLE_HEIGHT = {
    "docx-portrait":   10.0,   # A4 portrait
    "docx-landscape":   7.33,  # A4 landscape
    "pptx-16-9":        7.5,   # 1080 / 144
    "pptx-4-3":         7.5,
    "pdf-portrait":    10.0,
    "pdf-landscape":    7.33,
    "letter-portrait": 10.5,
    "letter-landscape": 8.0,
}

# 요소별 평균 height (inch)
ELEMENT_HEIGHT = {
    "h1":          0.55,
    "h2":          0.42,
    "h3":          0.32,
    "callout":     0.5,
    "bullet":      0.2,   # 1 줄당
    "paragraph":   0.18,  # 1 줄당
    "caption":     0.25,
    "table_row":   0.3,
    "image":       3.0,   # 기본값 — image_max_height 로 동적 결정
    "code_block":  0.5,   # +0.2 per line
    "spacer":      0.3,
    "safety":      0.3,   # 안전 여유
}


class PageLayoutTracker:
    """페이지 콘텐츠 height 누적 추적."""

    def __init__(self, page_type: str = "docx-landscape"):
        if page_type not in PAGE_USABLE_HEIGHT:
            raise ValueError(f"unknown page_type: {page_type}")
        self.page_type = page_type
        self.usable = PAGE_USABLE_HEIGHT[page_type]
        self.used = ELEMENT_HEIGHT["safety"]  # 시작부터 안전여유 차감
        self.elements: list[tuple[str, float]] = []

    def add(self, kind: str, height: float | None = None, lines: int = 1) -> float:
        """요소 추가. 반환 = 현재 누적 height."""
        if height is None:
            h = ELEMENT_HEIGHT.get(kind, 0.2)
            if kind in ("bullet", "paragraph"):
                h *= lines
        else:
            h = height
        self.used += h
        self.elements.append((kind, h))
        return self.used

    def remaining(self) -> float:
        """남은 페이지 height (inch)."""
        return max(0.0, self.usable - self.used)

    def image_max_height(self, png_ratio: float = 0.75) -> float:
        """이미지 삽입 시 max_height 계산.
        png_ratio = height / width (PIL 로 측정한 값).
        - 남은 height 와 너비 기준 height 중 작은 값
        """
        rem = self.remaining()
        # caption + safety 미리 차감
        rem -= ELEMENT_HEIGHT["caption"]
        return max(0.5, rem - 0.2)

    def can_fit(self, kind: str, height: float | None = None, lines: int = 1) -> bool:
        """다음 요소 fit 가능? add 하지 않고 검사."""
        if height is None:
            h = ELEMENT_HEIGHT.get(kind, 0.2)
            if kind in ("bullet", "paragraph"):
                h *= lines
        else:
            h = height
        return self.used + h <= self.usable

    def report(self) -> dict:
        return {
            "page_type": self.page_type,
            "usable_height": self.usable,
            "used": round(self.used, 2),
            "remaining": round(self.remaining(), 2),
            "fit": self.used <= self.usable,
            "elements": self.elements,
        }


# CLI: stdout 보고
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    # 시연: docx landscape 에 H1 + callout + bullet*5 + image
    pt = sys.argv[1] if len(sys.argv) > 1 else "docx-landscape"
    t = PageLayoutTracker(pt)
    t.add("h1")
    t.add("callout")
    t.add("bullet", lines=5)
    img_h = t.image_max_height(png_ratio=0.75)
    t.add("image", height=img_h)
    t.add("caption")
    print(json.dumps(t.report(), ensure_ascii=False, indent=2))
