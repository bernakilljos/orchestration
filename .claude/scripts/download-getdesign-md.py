"""getdesign.md (VoltAgent/awesome-design-md) 71 brand DESIGN.md raw 다운로드.

URL 패턴: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/<brand>/DESIGN.md
저장: docs/screens/_brand-md/<brand>-DESIGN.md
"""
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "screens" / "_brand-md"
OUT.mkdir(parents=True, exist_ok=True)

BRANDS = [
    "airbnb", "airtable", "apple", "binance", "bmw-m", "bmw", "bugatti",
    "cal", "claude", "clay", "clickhouse", "cohere", "coinbase", "composio",
    "cursor", "elevenlabs", "expo", "ferrari", "figma", "framer", "hashicorp",
    "ibm", "intercom", "kraken", "lamborghini", "linear.app", "lovable",
    "mastercard", "meta", "minimax", "mintlify", "miro", "mistral.ai",
    "mongodb", "nike", "notion", "nvidia", "ollama", "opencode.ai",
    "pinterest", "playstation", "posthog", "raycast", "renault", "replicate",
    "resend", "revolut", "runwayml", "sanity", "sentry", "shopify", "slack",
    "spacex", "spotify", "starbucks", "stripe", "supabase", "superhuman",
    "tesla", "theverge", "together.ai", "uber", "vercel", "vodafone",
    "voltagent", "warp", "webflow", "wired", "wise", "x.ai", "zapier",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE = "https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md"


def safe_name(brand):
    """linear.app → linear, mistral.ai → mistral, x.ai → xai 같은 안전한 파일명"""
    return brand.replace(".", "-").replace("/", "-")


def download(url, out_path):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r, open(out_path, "wb") as f:
        f.write(r.read())


def main():
    print(f"[START] {len(BRANDS)} brands → {OUT}", flush=True)
    start = time.time()
    ok = 0
    fail = 0
    for i, brand in enumerate(BRANDS, 1):
        safe = safe_name(brand)
        out = OUT / f"{safe}-DESIGN.md"
        if out.exists() and out.stat().st_size > 5_000:
            print(f"  [{i}/{len(BRANDS)}] skip {safe} (existing {out.stat().st_size//1024}KB)", flush=True)
            ok += 1
            continue
        # 메인 DESIGN.md
        url = f"{BASE}/{brand}/DESIGN.md"
        try:
            download(url, out)
            size = out.stat().st_size // 1024
            print(f"  [{i}/{len(BRANDS)}] OK {safe} {size}KB", flush=True)
            ok += 1
        except Exception as e:
            print(f"  [{i}/{len(BRANDS)}] FAIL {safe}: {type(e).__name__} {str(e)[:60]}", flush=True)
            fail += 1
        # preview.html 도 시도 (있으면 추가 reference)
        prev_url = f"{BASE}/{brand}/preview.html"
        prev_out = OUT / f"{safe}-preview.html"
        if not prev_out.exists():
            try:
                download(prev_url, prev_out)
            except Exception:
                pass  # preview 없을 수 있음
        time.sleep(0.3)
    elapsed = int(time.time() - start)
    print(f"\n[DONE] OK {ok} / FAIL {fail} / elapsed {elapsed}s", flush=True)


if __name__ == "__main__":
    main()
