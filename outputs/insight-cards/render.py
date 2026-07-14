"""Render AI 진화 10가족 HTML → PNG via Playwright."""
import asyncio
from pathlib import Path

HERE = Path(__file__).parent
HTML = HERE / "ai-evolution-10families.html"
PNG  = HERE / "ai-evolution-10families.png"

async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1200})
        await page.goto(HTML.resolve().as_uri())
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(PNG), full_page=False,
                              clip={"x": 0, "y": 0, "width": 1920, "height": 1200})
        await browser.close()
    print(f"OK -> {PNG}")

if __name__ == "__main__":
    asyncio.run(main())
