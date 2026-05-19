"""데모 — brand_tokens + illustration_lookup + builder_helpers 통합 1 페이지 PNG.

비교용 4 페이지 1920×1080:
1. Claude warm (lecture-docx) + dribbble 기린
2. Stripe corporate (exec-dashboard) + dribbble 차트
3. Linear dark (dev-docs) + dribbble 아이콘
4. Airbnb colorful (consumer) + Pollinations 자동 fetch
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from builder_helpers import page_assets, brand_css

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "demo"
OUT.mkdir(parents=True, exist_ok=True)

DEMO_PAGES = [
    {"title": "Claude warm — 강의 docx",
     "subtitle": "warm-editorial · cream + coral · Copernicus serif",
     "keyword": "기린",
     "use_case": "lecture-docx",
     "body": "5살 청자에게 \"AI 에이전트\"는 \"심부름꾼 친구\" 비유. 친절하고 따뜻한 어조로 풀어 쓰는 페이지입니다."},
    {"title": "Stripe corporate — 임원 dashboard",
     "subtitle": "corporate-blue · 결제·금융 신뢰 · Sohne sans",
     "keyword": "차트",
     "use_case": "exec-dashboard",
     "body": "월간 매출 추이 · 전년 대비 +24% · 핵심 KPI 4 개 요약. 임원이 5초 안에 의사결정 가능한 페이지."},
    {"title": "Linear dark — 개발자 docs",
     "subtitle": "dark-minimal · purple accent · Inter Display",
     "keyword": "아이콘",
     "use_case": "dev-docs",
     "body": "API reference · code blocks · 빠른 navigation. 개발자가 사랑하는 미니멀 다크 모드 docs."},
    {"title": "Airbnb consumer — 마케팅 랜딩",
     "subtitle": "colorful · bold single accent · 친근 storytelling",
     "keyword": "여행 일러스트, 친근한 모험",
     "use_case": "consumer",
     "body": "여행을 시작하는 사람들 · 일러스트 중심 · 감성 + bold CTA."},
]


def build_html(page: dict, assets: dict) -> str:
    import base64
    brand = assets["brand"]
    img_path = assets["image_path"]
    css = brand_css(brand)
    if img_path and Path(img_path).exists():
        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = Path(img_path).suffix.lstrip(".").lower()
        mime = "jpeg" if ext == "jpg" else ext
        img_tag = f'<img src="data:image/{mime};base64,{b64}" />'
    else:
        img_tag = '<div class="img-placeholder">No image</div>'
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
{css}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 1920px; height: 1080px;
  font-family: var(--brand-body-font);
  background: var(--brand-canvas);
  color: var(--brand-body);
  overflow: hidden;
}}
.page {{
  width: 100%; height: 100%; padding: 80px 120px;
  display: grid; grid-template-columns: 1fr 720px; gap: 80px;
  align-items: center;
}}
.left {{ display: flex; flex-direction: column; gap: 28px; }}
h1 {{
  font-family: var(--brand-headline-font);
  font-size: 76px; line-height: 1.05; letter-spacing: -1.5px;
  color: var(--brand-ink); font-weight: 500;
}}
.subtitle {{
  font-size: 22px; color: var(--brand-muted);
  letter-spacing: 1px; text-transform: uppercase; font-weight: 600;
}}
.body {{ font-size: 24px; line-height: 1.5; color: var(--brand-body); }}
.cta {{
  display: inline-block; background: var(--brand-primary); color: white;
  padding: 18px 36px; border-radius: 10px; font-weight: 600;
  font-size: 18px; margin-top: 16px; width: fit-content;
}}
.cluster-tag {{
  display: inline-block; padding: 6px 16px; border-radius: 999px;
  background: rgba(0,0,0,0.06); color: var(--brand-ink);
  font-size: 14px; font-weight: 600; margin-bottom: 8px; width: fit-content;
}}
.right {{
  width: 720px; height: 720px;
  display: flex; align-items: center; justify-content: center;
  background: var(--brand-surface-card);
  border-radius: 24px;
  overflow: hidden;
}}
.right img {{ width: 100%; height: 100%; object-fit: cover; }}
.img-placeholder {{ color: var(--brand-muted); font-size: 24px; }}
.meta {{
  position: absolute; bottom: 24px; left: 120px;
  font-size: 12px; color: var(--brand-muted); font-family: monospace;
}}
</style></head>
<body>
<div class="page">
  <div class="left">
    <span class="cluster-tag">{brand.get('cluster', '?')}</span>
    <h1>{page['title']}</h1>
    <p class="subtitle">{page['subtitle']}</p>
    <p class="body">{page['body']}</p>
    <a class="cta">View ←</a>
  </div>
  <div class="right">{img_tag}</div>
</div>
<div class="meta">
  primary={brand.get('primary')} · canvas={brand.get('canvas')} · img={assets.get('image_source', 'none')}
</div>
</body></html>"""


async def render(html: str, out_path: Path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await ctx.new_page()
        await page.set_content(html, wait_until="networkidle")
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(out_path), full_page=False, type="jpeg", quality=92)
        await browser.close()


async def main():
    print(f"[START] demo {len(DEMO_PAGES)} pages → {OUT}", flush=True)
    for i, page in enumerate(DEMO_PAGES, 1):
        keyword = page["keyword"]
        use_case = page["use_case"]
        # auto_gen=True 4번째 페이지만 (Pollinations 호출)
        auto_gen = (i == 4)
        assets = page_assets(keyword, use_case=use_case, auto_gen=auto_gen)
        print(f"  [{i}/4] {page['title'][:30]}  brand={assets['brand'].get('cluster')}  img={assets['image_source']}", flush=True)
        html = build_html(page, assets)
        out = OUT / f"demo-{i:02d}-{use_case}.jpg"
        await render(html, out)
        print(f"  → {out.name} ({out.stat().st_size//1024}KB)", flush=True)
    print(f"\n[DONE] {OUT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
