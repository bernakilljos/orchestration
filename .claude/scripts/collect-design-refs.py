#!/usr/bin/env python3
"""collect-design-refs.py ??留ㅼ떆媛?移댄뀒怨좊━蹂??붿옄???덊띁?곗뒪 ?먮룞 ?섏쭛

?⑸룄: docs/screens/<category>/ ???뱀궗?댄듃 罹≪쿂 ?먮뒗 ?대?吏 ?ㅼ슫濡쒕뱶
以묐났: ?뚯씪紐??댁떆濡?以묐났 諛⑹?
?몄텧: python .claude/scripts/collect-design-refs.py [--category dashboard]
"""
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENS_DIR = PROJECT_ROOT / "docs" / "screens"
LOG_FILE = PROJECT_ROOT / ".claude" / "logs" / "collect-design-refs.log"
HASH_FILE = PROJECT_ROOT / ".claude" / "state" / "design-refs-hashes.json"

# 移댄뀒怨좊━蹂??섏쭛 ?뚯뒪 (Unsplash/Dribbble/Behance API ?먮뒗 curated URLs)
CATEGORY_SOURCES = {
    "dashboard": [
        "https://dribbble.com/search/dashboard-design",
        "https://www.behance.net/search/projects?search=dashboard+ui",
    ],
    "login": [
        "https://dribbble.com/search/login-page",
    ],
    "signup": [
        "https://dribbble.com/search/signup-form",
    ],
    "pricing": [
        "https://dribbble.com/search/pricing-page",
    ],
    "form": [
        "https://dribbble.com/search/form-design",
    ],
    "checkout": [
        "https://dribbble.com/search/checkout-page",
    ],
    "profile": [
        "https://dribbble.com/search/profile-page",
    ],
    "settings": [
        "https://dribbble.com/search/settings-page",
    ],
    "notification": [
        "https://dribbble.com/search/notification-design",
    ],
    "onboarding": [
        "https://dribbble.com/search/onboarding-flow",
    ],
    "search": [
        "https://dribbble.com/search/search-ui",
    ],
    "menu": [
        "https://dribbble.com/search/navigation-menu",
    ],
    "404": [
        "https://dribbble.com/search/404-page",
    ],
    "illustration": [
        "https://dribbble.com/search/illustration-web",
    ],
    "color-typo": [
        "https://dribbble.com/search/color-palette-typography",
    ],
    "template": [
        "https://dribbble.com/search/website-template",
    ],
    "arch": [
        "https://dribbble.com/search/system-architecture",
    ],
}


def load_hashes() -> set:
    """湲곗〈 ?섏쭛???대?吏 ?댁떆 濡쒕뱶 (以묐났 諛⑹?)"""
    if HASH_FILE.exists():
        try:
            return set(json.loads(HASH_FILE.read_text(encoding="utf-8")))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            return set()
    return set()


def save_hashes(hashes: set):
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASH_FILE.write_text(json.dumps(list(hashes)), encoding="utf-8")


def hash_content(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def capture_screenshot(url: str, output_path: Path, width: int = 1920, height: int = 1080) -> bool:
    """Playwright濡??뱀궗?댄듃 罹≪쿂"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(url, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(2000)
            page.screenshot(path=str(output_path), full_page=False)
            browser.close()
            return True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[WARN] Screenshot failed for {url}: {e}", file=sys.stderr)
        return False


def download_image(url: str, output_path: Path) -> bool:
    """?대?吏 URL ?ㅼ슫濡쒕뱶"""
    try:
        import requests
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 1000:
            output_path.write_bytes(r.content)
            return True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[WARN] Download failed for {url}: {e}", file=sys.stderr)
    return False


def collect_for_category(category: str, hashes: set) -> int:
    """移댄뀒怨좊━ 1媛쒖뿉???대?吏 1???섏쭛"""
    cat_dir = SCREENS_DIR / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    sources = CATEGORY_SOURCES.get(category, [])
    if not sources:
        return 0

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    url = random.choice(sources)

    # Playwright 罹≪쿂 ?쒕룄
    output = cat_dir / f"ref-{ts}-{hash_content(url.encode())[:8]}.png"
    if capture_screenshot(url, output):
        content_hash = hash_content(output.read_bytes())
        if content_hash in hashes:
            output.unlink()  # 以묐났 ??젣
            return 0
        hashes.add(content_hash)
        return 1
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="?붿옄???덊띁?곗뒪 ?먮룞 ?섏쭛")
    parser.add_argument("--category", help="?뱀젙 移댄뀒怨좊━留??섏쭛")
    parser.add_argument("--all", action="store_true", help="?꾩껜 移댄뀒怨좊━ ?섏쭛")
    args = parser.parse_args()

    hashes = load_hashes()
    collected = 0

    if args.category:
        categories = [args.category]
    elif args.all:
        categories = list(CATEGORY_SOURCES.keys())
    else:
        # 湲곕낯: ?쒕뜡 3媛?移댄뀒怨좊━
        categories = random.sample(list(CATEGORY_SOURCES.keys()), min(3, len(CATEGORY_SOURCES)))

    for cat in categories:
        n = collect_for_category(cat, hashes)
        collected += n
        if n > 0:
            print(f"  [OK] {cat}: 1???섏쭛")
        else:
            print(f"  ??{cat}: 以묐났 ?먮뒗 ?ㅽ뙣")

    save_hashes(hashes)

    # 濡쒓렇
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] collected={collected} categories={categories}\n")

    print(f"\n珥?{collected}???섏쭛 ?꾨즺")


if __name__ == "__main__":
    main()

