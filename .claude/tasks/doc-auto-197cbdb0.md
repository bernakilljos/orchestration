# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\collect-design-refs.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/collect-design-refs.py b/.claude/scripts/collect-design-refs.py
new file mode 100644
index 0000000..ae7e37c
--- /dev/null
+++ b/.claude/scripts/collect-design-refs.py
@@ -0,0 +1,189 @@
+#!/usr/bin/env python3
+"""collect-design-refs.py — 매시간 카테고리별 디자인 레퍼런스 자동 수집
+
+용도: docs/screens/<category>/ 에 웹사이트 캡처 또는 이미지 다운로드
+중복: 파일명 해시로 중복 방지
+호출: python .claude/scripts/collect-design-refs.py [--category dashboard]
+"""
+import hashlib
+import json
+import os
+import random
+import sys
+import time
+from datetime import datetime
+from pathlib import Path
+
+PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
+SCREENS_DIR = PROJECT_ROOT / "docs" / "screens"
+LOG_FILE = PROJECT_ROOT / ".claude" / "logs" / "collect-design-refs.log"
+HASH_FILE = PROJECT_ROOT / ".claude" / "state" / "design-refs-hashes.json"
+
+# 카테고리별 수집 소스 (Unsplash/Dribbble/Behance API 또는 curated URLs)
+CATEGORY_SOURCES = {
+    "dashboard": [
+        "https://dribbble.com/search/dashboard-design",
+        "https://www.behance.net/search/projects?search=dashboard+ui",
+    ],
+    "login": [
+        "https://dribbble.com/search/login-page",
+    ],
+    "signup": [
+        "https://dribbble.com/search/signup-form",
+    ],
+    "pricing": [
+        "https://dribbble.com/search/pricing-page",
+    ],
+    "form": [
+        "https://dribbble.com/search/form-design",
+    ],
+    "checkout": [
+        "https://dribbble.com/search/checkout-page",
+    ],
+    "profile": [
+        "https://dribbble.com/search/profile-page",
+    ],
+    "settings": [
+        "https://dribbble.com/search/settings-page",
+    ],
+    "notification": [
+        "https://dribbble.com/search/notification-design",
+    ],
+    "onboarding": [
+        "https://dribbble.com/search/onboarding-flow",
+    ],
+    "search": [
+        "https://dribbble.com/search/search-ui",
+    ],
+    "menu": [
+        "https://dribbble.com/search/navigation-menu",
+    ],
+    "404": [
+        "https://dribbble.com/search/404-page",
+    ],
+    "illustration": [
+        "https://dribbble.com/search/illustration-web",
+    ],
+    "color-typo": [
+        "https://dribbble.com/search/color-palette-typography",
+    ],
+    "template": [
+        "https://dribbble.com/search/website-template",
+    ],
+    "arch": [
+        "https://dribbble.com/search/system-architecture",
+    ],
+}
+
+
+def load_hashes() -> set:
+    """기존 수집된 이미지 해시 로드 (중복 방지)"""
+    if HASH_FILE.exists():
+        try:
+            return set(json.loads(HASH_FILE.read_text(encoding="utf-8")))
+        except Exception:
+            return set()
+    return set()
+
+
+def save_hashes(hashes: set):
+    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
+    HASH_FILE.write_text(json.dumps(list(hashes)), encoding="utf-8")
+
+
+def hash_content(content: bytes) -> str:
+    return hashlib.md5(content).hexdigest()
+
+
+def capture_screenshot(url: str, output_path: Path, width: int = 1920, height: int = 1080) -> bool:
+    """Playwright로 웹사이트 캡처"""
+    try:
+        from playwright.sync_api import sync_playwright
+        with sync_playwright() as p:
+            browser = p.chromium.launch(headless=True)
+            page = browser.new_page(viewport={"width": width, "height": height})
+            page.goto(url, timeout=30000, wait_until="networkidle")
+            page.wait_for_timeout(2000)
+            page.screenshot(path=str(output_path), full_page=False)
+            browser.close()
+            return True
+    except Exception as e:
+        print(f"[WARN] Screenshot failed for {url}: {e}", file=sys.stderr)
+        return False
+
+
+def download_image(url: str, output_path: Path) -> bool:
+    """이미지 URL 다운로드"""
+    try:
+        import requests
+        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
+        if r.status_code == 200 and len(r.content) > 1000:
+            output_path.write_bytes(r.content)
+            return True
+    except Exception as e:
+        print(f"[WARN] Download failed for {url}: {e}", file=sys.stderr)
+    return False
+
+
+def collect_for_category(category: str, hashes: set) -> int:
+    """카테고리 1개에서 이미지 1장 수집"""
+    cat_dir = SCREENS_DIR / category
+    cat_dir.mkdir(parents=True, exist_ok=True)
+
+    sources = CATEGORY_SOURCES.get(category, [])
+    if not sources:
+        return 0
+
+    ts = datetime.now().strftime("%Y%m%d_%H%M")
+    url = random.choice(sources)
+
+    # Playwright 캡처 시도
+    output = cat_dir / f"ref-{ts}-{hash_content(url.encode())[:8]}.png"
+    if capture_screenshot(url, output):
+        content_hash = hash_content(output.read_bytes())
+        if content_hash in hashes:
+            output.unlink()  # 중복 삭제
+            return 0
+        hashes.add(content_hash)
+        return 1
+    return 0
+
+
+def main():
+    import argparse
+    parser = argparse.ArgumentParser(description="디자인 레퍼런스 자동 수집")
+    parser.add_argument("--category", help="특정 카테고리만 수집")
+    parser.add_argument("--all", action="store_true", help="전체 카테고리 수집")
+    args = parser.parse_args()
+
+    hashes = load_hashes()
+    collected = 0
+
+    if args.category:
+        categories = [args.category]
+    elif args.all:
+        categories = list(CATEGORY_SOURCES.keys())
+    else:
+        # 기본: 랜덤 3개 카테고리
+        categories = random.sample(list(CATEGORY_SOURCES.keys()), min(3, len(CATEGORY_SOURCES)))
+
+    for cat in categories:
+        n = collect_for_category(cat, hashes)
+        collected += n
+        if n > 0:
+            print(f"  ✅ {cat}: 1장 수집")
+        else:
+            print(f"  ⏭️ {cat}: 중복 또는 실패")
+
+    save_hashes(hashes)
+
+    # 로그
+    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
+    with open(LOG_FILE, "a", encoding="utf-8") as f:
+        f.write(f"[{datetime.now()}] collected={collected} categories={categories}\n")
+
+    print(f"\n총 {collected}장 수집 완료")
+
+
+if __name__ == "__main__":
+    main()
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
