#!/usr/bin/env python3
"""
Playwright F12 Console Error Capture Utility.

Captures browser console errors, warnings, network failures, and HTTP error codes.
Cross-platform (Windows/Mac/Linux) with dynamic browser executable detection.

Usage:
    python capture-browser-errors.py <url> [--headed] [--timeout 30]
"""

import asyncio
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright")
    sys.exit(1)


class BrowserErrorCapture:
    """Capture console errors, warnings, and network failures from browser."""

    def __init__(self, url: str, headed: bool = False, timeout_sec: int = 30):
        self.url = url
        self.headed = headed
        self.timeout = timeout_sec * 1000  # ms
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.network_fails: List[Dict[str, Any]] = []
        self.http_errors: List[Dict[str, Any]] = []

    async def capture(self) -> Dict[str, Any]:
        """Run browser, capture errors, and return results."""
        async with async_playwright() as p:
            # Auto-detect browser (Chrome/Edge)
            browser = await p.chromium.launch(headless=not self.headed)
            try:
                context: BrowserContext = await browser.new_context()
                page: Page = await context.new_page()

                # Listen for console messages
                page.on("console", self._on_console)
                # Listen for page errors (uncaught exceptions)
                page.on("pageerror", self._on_page_error)
                # Listen for failed network requests
                page.on("requestfailed", self._on_request_failed)
                # Listen for response errors
                page.on("response", self._on_response)

                # Navigate to URL
                try:
                    await page.goto(self.url, wait_until="networkidle", timeout=self.timeout)
                except Exception as e:
                    self.errors.append({
                        "type": "navigation_error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

                # Wait a bit for late errors
                await asyncio.sleep(2)

                await context.close()
            finally:
                await browser.close()

        return self._compile_results()

    def _on_console(self, msg) -> None:
        """Handle console message (log, error, warn, etc.)."""
        entry = {
            "type": msg.type,  # "log", "error", "warning", "info", etc.
            "text": msg.text,
            "location": msg.location if hasattr(msg, "location") else {},
            "timestamp": datetime.now().isoformat()
        }

        if msg.type == "error":
            self.errors.append(entry)
        elif msg.type in ("warning", "warn"):
            self.warnings.append(entry)
        else:
            self.warnings.append(entry)  # log/info as warnings

    def _on_page_error(self, error) -> None:
        """Handle uncaught page error."""
        self.errors.append({
            "type": "uncaught_error",
            "message": str(error),
            "timestamp": datetime.now().isoformat()
        })

    def _on_request_failed(self, request) -> None:
        """Handle failed network request."""
        self.network_fails.append({
            "url": request.url,
            "method": request.method,
            "reason": getattr(request, "failure", {}).get("errorText", "unknown"),
            "timestamp": datetime.now().isoformat()
        })

    def _on_response(self, response) -> None:
        """Handle HTTP response (capture 4xx, 5xx)."""
        if response.status >= 400:
            self.http_errors.append({
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text,
                "timestamp": datetime.now().isoformat()
            })

    def _compile_results(self) -> Dict[str, Any]:
        """Compile all captured errors/warnings/failures."""
        return {
            "url": self.url,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "network_failures": len(self.network_fails),
                "http_errors": len(self.http_errors)
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "network_failures": self.network_fails,
            "http_errors": self.http_errors
        }


async def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python capture-browser-errors.py <url> [--headed] [--timeout 30]")
        sys.exit(1)

    url = sys.argv[1]
    headed = "--headed" in sys.argv
    timeout = 30
    if "--timeout" in sys.argv:
        idx = sys.argv.index("--timeout")
        if idx + 1 < len(sys.argv):
            try:
                timeout = int(sys.argv[idx + 1])
            except ValueError:
                print("[WARN] Invalid timeout, using 30s")

    # Ensure URL has protocol
    if not url.startswith("http"):
        url = f"http://{url}"

    print(f"[*] Capturing F12 errors from {url}")
    print(f"[*] Headed: {headed}, Timeout: {timeout}s")

    capturer = BrowserErrorCapture(url, headed=headed, timeout_sec=timeout)
    results = await capturer.capture()

    # Save to .claude/logs/
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = logs_dir / f"browser-errors-{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Results saved to {output_file}")
    print(f"\nSummary:")
    for key, val in results["summary"].items():
        print(f"  {key}: {val}")

    # Exit with error code if errors found
    if results["summary"]["errors"] > 0 or results["summary"]["http_errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
