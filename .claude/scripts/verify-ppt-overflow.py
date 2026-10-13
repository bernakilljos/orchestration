"""
verify-ppt-overflow.py ??PPT ?뚮뜑 ???섎┝(overflow) ?섏떖 ?곸뿭 ?먮룞 ?먯?

湲곕뒫:
- outputs/ppt*/html-source/png-output/slide-*.png 紐⑤몢 遺꾩꽍
- 媛?μ옄由?(?섎떒 + ?곗륫) ?쎌? 遺꾪룷濡?肄섑뀗痢??섎┝ ?섏떖 slides ?앸퀎
- 寃곌낵瑜?markdown 由ы룷?몃줈 ???+ stdout ?붿빟

?먮━:
- slides 媛?μ옄由?(?섎떒 30px-?곗륫 30px) ???ㅽ겕 ?쎌? (?띿뒪??肄붾뱶-諛뺤뒪 蹂대뜑) 鍮꾩쑉 痢≪젙
- ?꾧퀎移?珥덇낵 = 肄섑뀗痢좉? ?곸뿭 ?앷퉴吏 李⑥엳??= ?섎┝ 媛?μ꽦
- ?⑥닚 ?쎌? 遺꾩꽍?대씪 100% ?뺥솗?섏? ?딆쓬 ??Claude ??Read tool OCR 蹂댁셿??

?ъ슜:
  python .claude/scripts/verify-ppt-overflow.py
  python .claude/scripts/verify-ppt-overflow.py --dir outputs/ppt-automation
  python .claude/scripts/verify-ppt-overflow.py --threshold 0.15
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[ERR] Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

EDGE_BAND_PX = 30
DARK_THRESHOLD_RGB = 80
DEFAULT_THRESHOLD = 0.10


def edge_dark_ratio(img: Image.Image, band_px: int = EDGE_BAND_PX) -> tuple[float, float]:
    """slides ?섎떒-?곗륫 媛?μ옄由??곸뿭???ㅽ겕 ?쎌? 鍮꾩쑉."""
    rgb = img.convert("RGB")
    w, h = rgb.size

    bottom = rgb.crop((0, h - band_px, w, h))
    right = rgb.crop((w - band_px, 0, w, h))

    def dark_ratio(region: Image.Image) -> float:
        pixels = list(region.getdata())
        dark = sum(
            1 for r, g, b in pixels
            if r < DARK_THRESHOLD_RGB and g < DARK_THRESHOLD_RGB and b < DARK_THRESHOLD_RGB
        )
        return dark / max(1, len(pixels))

    return dark_ratio(bottom), dark_ratio(right)


def scan_dir(png_dir: Path, threshold: float) -> list[dict]:
    results = []
    pngs = sorted(png_dir.glob("slide-*.png"))
    for p in pngs:
        try:
            img = Image.open(p)
            bottom, right = edge_dark_ratio(img)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            results.append({"file": p.name, "error": str(e)})
            continue

        suspect = bottom > threshold or right > threshold
        results.append({
            "file": p.name,
            "bottom": round(bottom, 4),
            "right": round(right, 4),
            "suspect": suspect,
        })
    return results


def write_report(results: list[dict], out_path: Path, threshold: float, src_dir: Path):
    suspects = [r for r in results if r.get("suspect")]
    lines = [
        "# PPT Overflow Verification Report",
        "",
        f"- Source: `{src_dir}`",
        f"- Total slides: {len(results)}",
        f"- Suspect (>{threshold:.0%} edge dark): **{len(suspects)}**",
        f"- Threshold: bottom + right band {EDGE_BAND_PX}px, dark = RGB < {DARK_THRESHOLD_RGB}",
        "",
        "## All slides",
        "",
        "| slide | bottom | right | suspect |",
        "|-------|-------:|------:|:-------:|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['file']} | ERR | ERR | ??|")
        else:
            mark = "[!] YES" if r["suspect"] else "[OK]"
            lines.append(f"| {r['file']} | {r['bottom']:.3f} | {r['right']:.3f} | {mark} |")

    if suspects:
        lines += [
            "",
            "## Suspect slides ??Claude OCR 吏곸젒 ?뺤씤 沅뚯옣",
            "",
        ]
        for r in suspects:
            lines.append(f"- **{r['file']}** ??bottom {r['bottom']:.3f}, right {r['right']:.3f}")
        lines += [
            "",
            "**?ㅼ쓬 ?≪뀡:**",
            "```python",
            "# Claude 媛 ?섏떖 slides瑜?Read tool 濡?吏곸젒 OCR",
        ]
        for r in suspects[:5]:
            lines.append(f"Read('{src_dir}/{r['file']}')")
        lines += ["```"]
    else:
        lines += ["", "## [OK] 紐⑤뱺 slides ?듦낵 ???섎┝ ?섏떖 ?놁쓬", ""]

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None,
                    help="PPT ?묒뾽 ?대뜑 (?? outputs/ppt-automation). 誘몄??뺤떆 outputs/ppt* ?꾨?")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                    help="媛?μ옄由??ㅽ겕 ?쎌? 鍮꾩쑉 ?꾧퀎移?(default: 0.10)")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent

    if args.dir:
        targets = [project_root / args.dir]
    else:
        targets = sorted((project_root / "outputs").glob("ppt*"))

    any_suspect = False
    for t in targets:
        png_dir = t / "html-source" / "png-output"
        if not png_dir.exists():
            continue

        print(f"\n=== Scanning: {t.name} ===")
        results = scan_dir(png_dir, args.threshold)
        if not results:
            print("  (no PNGs)")
            continue

        report_path = t / "overflow-report.md"
        write_report(results, report_path, args.threshold, png_dir)

        suspects = [r for r in results if r.get("suspect")]
        total = len(results)

        if suspects:
            any_suspect = True
            print(f"  [!]  {len(suspects)}/{total} slides - possible overflow:")
            for r in suspects:
                print(f"     - {r['file']}  bottom={r['bottom']:.3f}  right={r['right']:.3f}")
            print(f"  [report] {report_path.relative_to(project_root)}")
        else:
            print(f"  [OK] {total}/{total} slides clean")

    print()
    if any_suspect:
        print("[ACTION] Claude needs to OCR suspect slides via Read tool")
        sys.exit(2)
    else:
        print("[OK] All clean - no overflow suspects")


if __name__ == "__main__":
    main()

