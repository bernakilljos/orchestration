#!/usr/bin/env python3
"""
render-screens.py — docs/screens/our-html/*.html → arch/ 또는 func/ PNG.

prefix 로 분류:
  arch-*.html → docs/screens/our-arch/<name>.png
  func-*.html → docs/screens/our-func/<name>.png

Usage:
  python .claude/scripts/render-screens.py                # all
  python .claude/scripts/render-screens.py arch-system    # one (no extension)
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
HTML_DIR = ROOT / "docs/screens/our-html"
ARCH_DIR = ROOT / "docs/screens/our-arch"
FUNC_DIR = ROOT / "docs/screens/our-func"

W, H, SCALE = 1920, 1080, 2


def out_path_for(html: Path) -> Path:
    name = html.stem
    if name.startswith("arch-"):
        return ARCH_DIR / f"{name}.png"
    if name.startswith("func-"):
        return FUNC_DIR / f"{name}.png"
    return ARCH_DIR / f"{name}.png"


async def render(only: list[str] | None):
    ARCH_DIR.mkdir(parents=True, exist_ok=True)
    FUNC_DIR.mkdir(parents=True, exist_ok=True)

    htmls = sorted(p for p in HTML_DIR.glob("*.html"))
    if only:
        htmls = [h for h in htmls if h.stem in only]
    print(f"Rendering {len(htmls)} screen(s)")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=SCALE,
        )
        page = await ctx.new_page()
        for html in htmls:
            url = html.resolve().as_uri()
            out = out_path_for(html)
            await page.goto(url, wait_until="networkidle", timeout=20000)
            try:
                await page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass
            await page.wait_for_timeout(900)
            await page.screenshot(path=str(out), full_page=False, omit_background=False,
                                  clip={"x": 0, "y": 0, "width": W, "height": H})
            print(f"  {html.name:38s} -> {out.relative_to(ROOT)}")
        await browser.close()
    print("DONE")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    only = args if args else None
    asyncio.run(render(only))


if __name__ == "__main__":
    main()
