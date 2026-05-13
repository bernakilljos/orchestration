"""v6 — collectui /challenges/<X> 의 모든 작품 large 이미지 직접 다운로드.

전제: static.collectui.com/shots/<id>/<NNN-name>-large 패턴 직접 다운로드.
challenge 페이지에 pagination 있으면 모든 페이지 순회.

결과: docs/screens/<우리카테고리>/collectui-<shot_id>.jpg
"""
import asyncio
import re
import time
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_ROOT = ROOT / "docs" / "screens"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MAX_PER_CATEGORY = 1000

# 우리 카테고리 ↔ collectui challenge 매핑
CAT_MAP = [
    ("signup",       ["sign-up"]),
    ("checkout",     ["checkout"]),
    ("onboarding",   ["onboarding"]),
    ("pricing",      ["pricing"]),
    ("form",         ["form"]),
    ("search",       ["search"]),
    ("settings",     ["settings"]),
    ("profile",      ["user-profile"]),
    ("notification", ["notifications"]),
    ("menu",         ["header-navigation", "mobile-menu"]),
    ("dashboard",    ["monitoring-dashboard"]),
    ("404",          ["404-page"]),
    ("color-typo",   ["color-picker"]),
    ("template",     ["landing-page"]),
    ("illustration", ["illustration"]),
]


def download(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://collectui.com/"})
    with urllib.request.urlopen(req, timeout=30) as r, open(out_path, "wb") as f:
        f.write(r.read())


async def collect_image_urls(page, challenge):
    """challenge 페이지의 모든 작품 image URL 추출. pagination 있으면 순회."""
    urls = []
    seen = set()
    p_num = 1
    while True:
        url = f"https://collectui.com/challenges/{challenge}"
        if p_num > 1:
            url = f"{url}?page={p_num}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                await asyncio.sleep(3)
            await asyncio.sleep(1.0)
            # large 이미지 URL 추출
            page_urls = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href*="static.collectui.com/shots/"]'))
                    .map(a => a.href)
                    .filter(h => h.includes('-large'))
            """)
            added = 0
            for u in page_urls:
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
                    added += 1
            # pagination 정보
            pagination = await page.evaluate("""
                () => {
                    const p = document.getElementById('pagination');
                    if (!p) return {current: 1, total: 1};
                    return {
                        current: parseInt(p.dataset.currentPage || '1'),
                        total: parseInt(p.dataset.totalPages || '1'),
                    };
                }
            """)
            print(f"    [{challenge} p.{p_num}] +{added} ({len(urls)} total)  pagination={pagination}")
            if added == 0 or p_num >= pagination.get("total", 1):
                break
            p_num += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"    [{challenge} p.{p_num}] FAIL {type(e).__name__}: {str(e)[:80]}")
            break
    return urls


async def main():
    print(f"[START v6 collectui] {len(CAT_MAP)} categories")
    start = time.time()
    summary = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=USER_AGENT)
        page = await ctx.new_page()
        for our_cat, challenges in CAT_MAP:
            out_dir = OUT_ROOT / our_cat
            out_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n=== {our_cat} ← {challenges} ===")
            all_urls = []
            for ch in challenges:
                urls = await collect_image_urls(page, ch)
                all_urls.extend(urls)
                if len(all_urls) >= MAX_PER_CATEGORY:
                    break
            # 중복 제거 (different challenge 에 같은 shot 있을 수 있음)
            uniq = []
            seen = set()
            for u in all_urls:
                if u not in seen:
                    seen.add(u)
                    uniq.append(u)
            print(f"  {our_cat} = {len(uniq)} URLs (cap {MAX_PER_CATEGORY})")
            ok = 0
            fail = 0
            for i, url in enumerate(uniq[:MAX_PER_CATEGORY], 1):
                # shot id 추출
                m = re.search(r"/shots/(\d+)/([^/?]+)", url)
                if not m:
                    fail += 1
                    continue
                shot_id = m.group(1)
                slug = m.group(2).replace("-large", "")
                out_path = out_dir / f"collectui-{shot_id}-{slug}.jpg"
                if out_path.exists() and out_path.stat().st_size > 20_000:
                    ok += 1
                    continue
                try:
                    download(url, out_path)
                    ok += 1
                except Exception as e:
                    fail += 1
                    print(f"    [FAIL {shot_id}] {type(e).__name__}: {str(e)[:80]}")
            summary[our_cat] = {"ok": ok, "fail": fail, "total": len(uniq)}
            print(f"  {our_cat}: OK {ok} / FAIL {fail}")
        await browser.close()
    elapsed = int(time.time() - start)
    print(f"\n[DONE v6 collectui] elapsed {elapsed}s")
    print("\n=== 요약 ===")
    total_ok = 0
    for cat, s in summary.items():
        total_ok += s["ok"]
        print(f"  {cat}: {s['ok']} (대상 {s['total']})")
    print(f"\n총 다운로드: {total_ok}")


if __name__ == "__main__":
    asyncio.run(main())
