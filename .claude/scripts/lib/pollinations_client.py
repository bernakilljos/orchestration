"""Pollinations.ai 무료 image gen 클라이언트.

API: https://image.pollinations.ai/prompt/<text>?width=&height=&model=&seed=
- 인증 X · rate limit 합리적
- model: flux (default · 좋음), turbo (빠름)
- 결과: image binary (PNG/JPG)

사용:
    >>> from pollinations_client import generate, generate_to_file
    >>> path = generate_to_file("기린 일러스트, flat design, cream background", "giraffe")
"""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CUSTOM_DIR = PROJECT_ROOT / "docs" / "screens" / "custom"
CACHE_DIR = PROJECT_ROOT / ".claude" / "state" / "image-cache"
CUSTOM_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) orchestration_v1/1.0"

# Brand → Pollinations style hint (선택적, brand 시각 일치)
BRAND_STYLE_HINT = {
    "warm-editorial": "warm cream background, editorial illustration, soft coral accents",
    "dark-minimal": "dark minimalist background, neon accent, clean lines",
    "corporate-blue": "corporate blue palette, professional, geometric",
    "neon-acid": "vibrant neon colors on dark, electric energy",
    "colorful": "bright vibrant colors, playful, energetic",
}


def _safe_filename(keyword: str, max_len: int = 60) -> str:
    """keyword → safe filename (ascii only)."""
    h = hashlib.md5(keyword.encode("utf-8")).hexdigest()[:8]
    # ASCII 만 추출
    ascii_part = "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "-"
                         for c in keyword.lower())[:max_len].strip("-")
    if not ascii_part:
        ascii_part = "img"
    return f"{ascii_part}-{h}"


def generate(prompt: str, width: int = 1024, height: int = 1024,
             model: str = "flux", seed: int = 42, timeout: int = 60) -> bytes:
    """Pollinations.ai 호출 → image binary 반환.

    Args:
        prompt: 자연어 설명 (한글 OK, 영어 더 정확)
        width/height: 이미지 사이즈 (기본 1024×1024)
        model: flux (좋음) / turbo (빠름)
        seed: 같은 (prompt, seed) 면 동일 결과 — 캐시 일관성
        timeout: HTTP timeout 초

    Returns:
        image binary (JPEG/PNG)
    """
    encoded = urllib.parse.quote(prompt, safe="")
    url = (f"https://image.pollinations.ai/prompt/{encoded}"
           f"?width={width}&height={height}&model={model}&nologo=true&seed={seed}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def generate_to_file(prompt: str, keyword: str, brand_cluster: Optional[str] = None,
                     width: int = 1024, height: int = 1024,
                     seed: int = 42, force: bool = False) -> str:
    """prompt → docs/screens/custom/<keyword>-<hash>.jpg 저장.

    Args:
        prompt: API 에 보낼 자연어
        keyword: 우리 시스템 keyword (filename 기반)
        brand_cluster: dark-minimal/warm-editorial/etc — style hint 자동 추가
        force: True 면 캐시 무시 + 재생성

    Returns:
        저장된 절대경로 문자열
    """
    # Brand style hint 추가
    if brand_cluster and brand_cluster in BRAND_STYLE_HINT:
        prompt = f"{prompt}, {BRAND_STYLE_HINT[brand_cluster]}"

    fname = _safe_filename(keyword) + ".jpg"
    out_path = CUSTOM_DIR / fname

    # 캐시 적중
    if out_path.exists() and out_path.stat().st_size > 5000 and not force:
        return str(out_path)

    # 메타 기록
    meta_path = CACHE_DIR / (fname + ".json")
    meta = {
        "keyword": keyword,
        "prompt": prompt,
        "brand_cluster": brand_cluster,
        "seed": seed,
        "model": "flux",
        "generated_at": int(time.time()),
    }
    try:
        binary = generate(prompt, width=width, height=height, seed=seed)
        with open(out_path, "wb") as f:
            f.write(binary)
        meta["size_kb"] = len(binary) // 1024
        meta["status"] = "ok"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return str(out_path)
    except Exception as e:
        meta["status"] = "fail"
        meta["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        raise


def list_cached() -> list:
    """캐시된 image meta list."""
    out = []
    for f in CACHE_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                meta = json.load(fp)
            jpg = CUSTOM_DIR / f.stem
            meta["path"] = str(jpg) if jpg.exists() else None
            out.append(meta)
        except Exception:
            pass
    return sorted(out, key=lambda x: x.get("generated_at", 0), reverse=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: pollinations_client.py <prompt> [keyword] [cluster]")
        print("       pollinations_client.py --list")
        print("       pollinations_client.py --stats")
        sys.exit(2)
    if sys.argv[1] == "--list":
        for m in list_cached()[:20]:
            print(f"  [{m.get('status')}] {m.get('keyword', '?'):20s}  {m.get('size_kb', 0)}KB  {m.get('prompt', '')[:50]}")
        sys.exit(0)
    if sys.argv[1] == "--stats":
        cached = list_cached()
        print(f"총 캐시: {len(cached)}")
        ok = sum(1 for m in cached if m.get("status") == "ok")
        fail = sum(1 for m in cached if m.get("status") == "fail")
        print(f"OK: {ok}  FAIL: {fail}")
        sys.exit(0)
    prompt = sys.argv[1]
    keyword = sys.argv[2] if len(sys.argv) > 2 else _safe_filename(prompt)
    cluster = sys.argv[3] if len(sys.argv) > 3 else None
    path = generate_to_file(prompt, keyword, brand_cluster=cluster)
    size_kb = Path(path).stat().st_size // 1024
    print(f"[OK] {path}  {size_kb}KB")
