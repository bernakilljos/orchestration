"""getdesign.md 사이트의 /<brand>/design-md preview HTML 페이지 다운로드 + PNG 캡쳐.

이 페이지 = brand 의 전체 9 섹션 디자인 spec 을 시각적으로 보여주는 detail page.
71 brand × HTML + PNG fullpage 캡쳐.
"""
import asyncio
import time
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "screens" / "_brand-preview"
OUT.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BRANDS = [
    "airbnb","airtable","apple","binance","bmw-m","bmw","bugatti","cal","claude","clay","clickhouse",
    "cohere","coinbase","composio","cursor","elevenlabs","expo","ferrari","figma","framer","hashicorp",
    "ibm","intercom","kraken","lamborghini","linear.app","lovable","mastercard","meta","minimax",
    "mintlify","miro","mistral.ai","mongodb","nike","notion","nvidia","ollama","opencode.ai",
    "pinterest","playstation","posthog","raycast","renault","replicate","resend","revolut","runwayml",
    "sanity","sentry","shopify","slack","spacex","spotify","starbucks","stripe","supabase","superhuman",
    "tesla","theverge","together.ai","uber","vercel","vodafone","voltagent","warp","webflow","wired",
    "wise","x.ai","zapier",
]


def safe_name(brand):
    return brand.replace(".", "-").replace("/", "-")


async def main():
    print(f"[START] {len(BRANDS)} brand previews → {OUT}", flush=True)
    start = time.time()
    ok, fail = 0, 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for i, brand in enumerate(BRANDS, 1):
            safe = safe_name(brand)
            png_out = OUT / f"{safe}-preview.jpg"
            html_out = OUT / f"{safe}-preview.html"
            if png_out.exists() and png_out.stat().st_size > 50_000:
                ok += 1
                continue
            try:
                ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=USER_AGENT)
                page = await ctx.new_page()
                url = f"https://getdesign.md/{brand}/design-md"
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    await asyncio.sleep(3)
                # 스크롤
                await page.evaluate("""
                    () => new Promise(r => {
                        let y = 0;
                        const step = () => {
                            window.scrollBy(0, 1000);
                            y += 1000;
                            if (y < document.body.scrollHeight && y < 50000) {
                                setTimeout(step, 300);
                            } else { window.scrollTo(0, 0); setTimeout(r, 1000); }
                        };
                        step();
                    })
                """)
                await asyncio.sleep(1.5)
                # HTML 저장
                html = await page.content()
                html_out.write_text(html, encoding="utf-8")
                # PNG full_page 캡쳐
                await page.screenshot(path=str(png_out), full_page=True, type="jpeg", quality=85)
                size_kb = png_out.stat().st_size // 1024
                html_kb = html_out.stat().st_size // 1024
                print(f"  [{i}/{len(BRANDS)}] OK {safe} png={size_kb}KB html={html_kb}KB", flush=True)
                ok += 1
                await ctx.close()
            except Exception as e:
                fail += 1
                print(f"  [{i}/{len(BRANDS)}] FAIL {safe}: {type(e).__name__} {str(e)[:60]}", flush=True)
                try: await ctx.close()
                except: pass
            await asyncio.sleep(0.5)
        await browser.close()
    elapsed = int(time.time() - start)
    print(f"\n[DONE] OK {ok} / FAIL {fail} / {elapsed}s", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
