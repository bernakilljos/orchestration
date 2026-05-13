"""빌더 통합 helper — brand tokens + illustration lookup 하나로.

빌더 (build-korean-html-diagrams.py / build-arch-lecture-doc.py / design_word / design_ppt)
가 호출:

    from builder_helpers import page_assets, brand_css

    assets = page_assets("기린", use_case="lecture-docx", auto_gen=True)
    css = brand_css(assets["brand"])
    # css 변수 빌더 HTML 에 삽입
    img_path = assets["image_path"]
"""
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from brand_tokens import get_brand, get_use_case, BRAND_TOKENS  # noqa: E402
from illustration_lookup import find  # noqa: E402


def page_assets(keyword: str,
                use_case: str = "lecture-docx",
                brand_name: Optional[str] = None,
                auto_gen: bool = True) -> dict:
    """1 페이지에 필요한 brand 토큰 + illustration jpg 한번에 조회.

    Args:
        keyword: illustration 검색어 (한·영, 예: "기린", "차트", "로그인")
        use_case: lecture-docx / exec-dashboard / dev-docs / saas-landing / data-viz / fintech / corporate / consumer
        brand_name: 명시 brand (예: "claude", "linear-app") — use_case 무시
        auto_gen: 매치 없으면 Pollinations.ai 자동 호출 (~30초)

    Returns:
        {
            "brand": {primary, canvas, ink, headline_font, body_font, signature, cluster, ...},
            "image_path": "...jpg" 절대경로 또는 None,
            "image_source": "custom" | "library" | "generated" | None,
        }
    """
    if brand_name:
        brand = get_brand(brand_name)
    else:
        brand = get_use_case(use_case)

    cluster = brand.get("cluster")
    # 매치 + 자동 생성 (auto_gen=True 면 30초 까지 wait)
    img = find(keyword, auto_generate=auto_gen, brand_cluster=cluster)
    # source 판정 (path 안 검사)
    source = None
    if img:
        if "/custom/" in img.replace("\\", "/"):
            # custom/ 안에 있으면 사용자 import 또는 Pollinations 생성
            from pathlib import Path
            meta = Path(img).parent.parent.parent / ".claude" / "state" / "image-cache" / (Path(img).name + ".json")
            source = "generated" if meta.exists() else "custom"
        else:
            source = "library"

    return {
        "brand": brand,
        "image_path": img,
        "image_source": source,
    }


def brand_css(brand: dict) -> str:
    """brand 토큰 dict → CSS custom property 문자열.

    빌더 HTML <style> 안에 삽입:
        <style>:root { ...brand_css... }</style>
    """
    return f"""
:root {{
  --brand-primary: {brand.get('primary', '#1F3864')};
  --brand-primary-active: {brand.get('primary_active', brand.get('primary', '#1F3864'))};
  --brand-canvas: {brand.get('canvas', '#FFFAF0')};
  --brand-surface-card: {brand.get('surface_card', '#f7f9fc')};
  --brand-ink: {brand.get('ink', '#1F3864')};
  --brand-body: {brand.get('body', '#333333')};
  --brand-muted: {brand.get('muted', '#5C6B84')};
  --brand-headline-font: {brand.get('headline_font', 'Pretendard, sans-serif')};
  --brand-body-font: {brand.get('body_font', 'Pretendard, sans-serif')};
}}
""".strip()


def example_usage(keyword: str = "기린", use_case: str = "lecture-docx") -> dict:
    """CLI demo — keyword 받으면 전체 assets 반환."""
    assets = page_assets(keyword, use_case=use_case, auto_gen=False)
    return {
        "keyword": keyword,
        "use_case": use_case,
        "brand_name": assets["brand"].get("signature", "?"),
        "cluster": assets["brand"].get("cluster"),
        "primary": assets["brand"].get("primary"),
        "canvas": assets["brand"].get("canvas"),
        "image_path": assets["image_path"],
        "image_source": assets["image_source"],
    }


if __name__ == "__main__":
    import json
    kw = sys.argv[1] if len(sys.argv) > 1 else "기린"
    uc = sys.argv[2] if len(sys.argv) > 2 else "lecture-docx"
    result = example_usage(kw, uc)
    print(json.dumps(result, ensure_ascii=False, indent=2))
