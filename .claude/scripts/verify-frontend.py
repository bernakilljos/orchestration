"""Frontend visual + console error verifier.

Playwright headless 로 페이지 N개 로드 -> console error / pageerror / network 4xx-5xx 캡처.
hook-09-ocr-verify.sh 의 build-*-html 패턴 또는 사용자 명시 호출로 발동.

Usage:
  python .claude/scripts/verify-frontend.py <url-or-html-file> [<url-or-html-file>...]
  python .claude/scripts/verify-frontend.py --dir <html-root-dir>  (재귀 *.html 스캔)

Whitelist (noise 제거):
  - favicon.ico 404
  - .map (sourcemap) 404
  - chrome-extension://
  - DevTools listening

Exit:
  0 = PASS (오류 0)
  1 = FAIL (콘솔 에러 / pageerror / 4xx-5xx 검출)
  2 = SKIP (Playwright 미설치)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[SKIP] Playwright 미설치 — pip install playwright + playwright install chromium")
    sys.exit(2)

WHITELIST_PATTERNS = [
    r"favicon\.ico.*404",
    r"\.map.*404",
    r"chrome-extension://",
    r"DevTools listening",
    r"^\[HMR\]",
    r"\[vite\] connecting",
    r"^\[webpack-dev-server\]",
]


def is_whitelisted(msg: str) -> bool:
    for pat in WHITELIST_PATTERNS:
        if re.search(pat, msg, re.IGNORECASE):
            return True
    return False


def verify_url(url: str, timeout_ms: int = 10000) -> dict:
    result = {
        "url": url,
        "console_errors": [],
        "page_errors": [],
        "failed_requests": [],
        "warnings": [],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.on("console", lambda msg: (
            result["console_errors"].append(f"{msg.location.get('url','?')}:{msg.location.get('lineNumber','?')} {msg.text}")
            if msg.type == "error" and not is_whitelisted(msg.text)
            else result["warnings"].append(msg.text) if msg.type == "warning" and not is_whitelisted(msg.text)
            else None
        ))
        page.on("pageerror", lambda err: result["page_errors"].append(str(err)))
        page.on("requestfailed", lambda req: (
            result["failed_requests"].append(f"{req.url} - {req.failure}")
            if not is_whitelisted(req.url) else None
        ))
        page.on("response", lambda resp: (
            result["failed_requests"].append(f"{resp.url} - HTTP {resp.status}")
            if resp.status >= 400 and not is_whitelisted(resp.url)
            else None
        ))

        try:
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            page.wait_for_timeout(1000)  # JS 실행 시간 부여
        except Exception as e:
            result["page_errors"].append(f"navigation failed: {e}")

        browser.close()
    return result


def to_url(target: str) -> str:
    p = Path(target)
    if p.is_file():
        return p.resolve().as_uri()
    return target


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", help="URL 또는 HTML 파일 경로")
    ap.add_argument("--dir", help="HTML 루트 디렉토리 (재귀 *.html 스캔)")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    urls = [to_url(t) for t in args.targets]
    if args.dir:
        for html in Path(args.dir).rglob("*.html"):
            urls.append(html.resolve().as_uri())
    if not urls:
        print("usage: verify-frontend.py <url|file> [...] | --dir <root>")
        sys.exit(2)

    reports = [verify_url(u) for u in urls]
    fail_count = sum(
        len(r["console_errors"]) + len(r["page_errors"]) + len(r["failed_requests"])
        for r in reports
    )

    if args.json:
        print(json.dumps({"reports": reports, "fail_count": fail_count}, ensure_ascii=False, indent=2))
    else:
        print(f"=== verify-frontend ({len(reports)} pages) ===")
        for r in reports:
            errs = len(r["console_errors"]) + len(r["page_errors"]) + len(r["failed_requests"])
            mark = "[OK]" if errs == 0 else f"[FAIL {errs}]"
            print(f"  {mark} {r['url']}")
            for e in r["console_errors"][:3]:
                print(f"        console: {e[:150]}")
            for e in r["page_errors"][:3]:
                print(f"        pageerror: {e[:150]}")
            for e in r["failed_requests"][:3]:
                print(f"        request: {e[:150]}")
        print(f"\nTotal errors: {fail_count}")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
