"""verify-image-fit.py ??docs/screens/arch-kor/*.png ??鍮꾩쑉???섏씠吏 鍮꾩쑉怨?鍮꾧탳.

teaching-doc.md 짠 ?섏씠吏 fit ?ъ쟾寃利??먮룞??
hook-09-ocr-verify.sh ?먯꽌 build-*-diagrams.py ?몄텧 ??諛쒕룞.

PASS: PNG 鍮꾩쑉???섏씠吏 鍮꾩쑉 (landscape 0.69 짹 0.05) ??
FAIL: 鍮꾩쑉 遺덉씪移?-> docx ?먯꽌 吏ㅻ┝ ?먮뒗 鍮?怨듦컙
"""
import sys
import io
from pathlib import Path

# Windows 肄섏넄 cp949 ?뚰뵾
try:
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except (AttributeError, Exception):
    pass

try:
    from PIL import Image
except ImportError:
    print("[SKIP] Pillow not installed - pip install Pillow")
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = ROOT / "docs" / "screens" / "arch-kor"

# ?곗텧臾쇰퀎 ?섏씠吏 鍮꾩쑉 (margin ?쒖쇅, h/w) ???뺤옣 媛??
RATIOS = {
    # === 臾몄꽌 (A4 湲곕낯) ===
    "docx-portrait":     1.46,    # 8.27횞11.69 -> ?ъ슜 6.5횞9.5
    "docx-landscape":    0.69,    # 11.69횞8.27 -> ?ъ슜 9.5횞6.6
    "pdf-portrait":      1.41,    # A4
    "pdf-landscape":     0.71,    # A4
    # === A3 / A5 / Letter ===
    "a3-portrait":       1.41,
    "a3-landscape":      0.71,
    "a5-portrait":       1.41,
    "a5-landscape":      0.71,
    "letter-portrait":   1.29,    # 8.5횞11
    "letter-landscape":  0.77,
    # === ?щ씪?대뱶 ===
    "pptx-16:9":         0.54,    # 13.33횞7.5 -> ?ъ슜 12.5횞6.7
    "pptx-4:3":          0.71,    # 10횞7.5
    "google-slides":     0.54,    # 16:9
    "keynote":           0.54,    # 16:9
    # === ?꾩옄梨?===
    "epub-portrait":     1.50,    # 6횞9 in
    "kindle":            1.60,    # ?쒖?
    # === ?곸긽 ===
    "video-16:9":        0.5625,  # 1920횞1080 YouTube
    "video-9:16":        1.78,    # 1080횞1920 Shorts/Reels
    "video-1:1":         1.0,     # ?뺤궗媛?Instagram
    "youtube-thumbnail": 0.5625,  # 1280횞720
    # === ?뚯뀥 ===
    "instagram-square":  1.0,
    "instagram-story":   1.78,    # 9:16
    "instagram-portrait": 1.25,   # 4:5
    "facebook-cover":    0.524,   # 820횞312
    "twitter-card":      0.563,   # 1200횞675
    "linkedin-post":     1.0,     # 1:1 沅뚯옣
    "tiktok":            1.78,    # 9:16
    # === ?몄뇙-湲고? ===
    "business-card":     0.572,   # 89횞51mm
    "poster-a2":         1.41,
    "card-3:2":          0.667,
}
TOLERANCE = 0.05

# ?숈쟻 ?곗텧臾??먮룞 ?깅줉 ???ъ슜???≪뀡 0 (RATIOS_USER.json ?쇰줈 ?뺤옣 媛??
import os, json
USER_RATIOS = Path(__file__).parent.parent / "state" / "fit-ratios-user.json"
if USER_RATIOS.exists():
    try:
        with open(USER_RATIOS, encoding="utf-8") as f:
            RATIOS.update(json.load(f))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass

# 湲곕낯: docx landscape (?꾩옱 lecture 鍮뚮뜑). ?ㅻⅨ ?곗텧臾쇱? FIT_TARGET=<key>
EXPECTED_KEY = os.environ.get("FIT_TARGET", "docx-landscape")
EXPECTED = RATIOS.get(EXPECTED_KEY, 0.69)


def auto_register_ratio(name: str, width: int, height: int) -> None:
    """鍮뚮뜑 script 媛 ?몄텧?댁꽌 RATIOS ?숈쟻 ?깅줉.

    ?? from verify_image_fit import auto_register_ratio
        auto_register_ratio("my-custom-doc", 1600, 1100)
    """
    USER_RATIOS.parent.mkdir(parents=True, exist_ok=True)
    cur = {}
    if USER_RATIOS.exists():
        try:
            with open(USER_RATIOS, encoding="utf-8") as f:
                cur = json.load(f)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass
    cur[name] = round(height / width, 4)
    with open(USER_RATIOS, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)

if not TARGET.exists():
    print(f"[SKIP] {TARGET} ?놁쓬")
    sys.exit(0)

problems = []
warnings = []
ok = 0
total = 0
for png in sorted(TARGET.glob("*.png")):
    total += 1
    try:
        with Image.open(png) as im:
            w, h = im.size
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        problems.append((png.name, f"PIL ?ㅻ쪟: {e}"))
        continue
    ratio = h / w
    diff = abs(ratio - EXPECTED)

    # FAIL: 鍮꾩쑉 ??李⑥씠 (吏ㅻ┝ ?먮뒗 鍮?怨듦컙 ??
    if diff > TOLERANCE:
        problems.append((png.name, f"鍮꾩쑉 {ratio:.2f} vs 湲곕? {EXPECTED:.2f} (李⑥씠 {diff:.2f}) ??吏ㅻ┝/?щ갚 ?꾪뿕"))
        continue

    # WARN: 異붽? 寃利?(鍮??щ갚-肄섑뀗痢?遺議?
    # 留ㅼ슦 ?묒? PNG = 肄섑뀗痢?遺議?(?? width < 800 px)
    if w < 900:
        warnings.append((png.name, f"width {w}px ?묒쓬 ???뺣낫 遺議??먮뒗 ?고듃 鍮꾩쑉 ??))
    # 留ㅼ슦 ??PNG = docx ?먯꽌 湲???묒븘 蹂댁엫 (?댁긽????醫뗭쓬 + ?붾㈃ ?쒖떆 ??
    elif w > 2000:
        warnings.append((png.name, f"width {w}px 怨쇰? ??docx 諛뺥옄 ???붾㈃ 湲???묒쓬"))

    ok += 1

if problems:
    print(f"[FAIL] image-fit 寃利???{len(problems)}/{total} 鍮꾩쑉 遺덉씪移?)
    for name, msg in problems[:5]:
        print(f"  - {name}: {msg}")
    if len(problems) > 5:
        print(f"  ... {len(problems) - 5} more")
    print()
    print("沅뚯옣: PNG viewport 鍮꾩쑉???섏씠吏 鍮꾩쑉怨??쇱튂?쒖폒 ?ъ깮??(FIT_TARGET ?섍꼍蹂??")
    sys.exit(2)

if warnings:
    print(f"[WARN] image-fit 寃利???{ok}/{total} PASS, ??{len(warnings)} 寃쎄퀬")
    for name, msg in warnings[:5]:
        print(f"  - {name}: {msg}")
    sys.exit(0)

print(f"[PASS] image-fit 寃利???{ok}/{total} 紐⑤몢 ?듦낵 (鍮꾩쑉 {EXPECTED:.2f} 짹 {TOLERANCE})")
sys.exit(0)

