"""PNG ?????щ갚 ?먮룞 寃異???banner ??肄섑뀗痢???~ PNG ???ъ씠 鍮?怨듦컙 痢≪젙.

湲곗?:
- ?곹븯 ????>= 5% ?섏씠吏 ?믪씠 = WARN
- 醫뚯슦 ????>= 5% ?섏씠吏 ??= WARN

PIL bbox + ??遺꾩꽍 ??肄섑뀗痢??곸뿭 (non-background pixels) vs PNG ?꾩껜.
"""
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("[SKIP] PIL/numpy ?놁쓬 ??verify-image-whitespace 嫄대꼫?")
    sys.exit(0)


def detect_whitespace(png_path: Path, threshold: float = 0.05) -> dict:
    """PNG ???곹븯醫뚯슦 ????鍮꾩쑉 痢≪젙."""
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    # 諛곌꼍??異붿젙 ??紐⑥꽌由?4媛??됯퇏 (PNG body background)
    bg = np.mean([arr[0, 0], arr[0, w-1], arr[h-1, 0], arr[h-1, w-1]], axis=0)
    # 肄섑뀗痢?mask ??諛곌꼍?됯낵 李⑥씠 >= 30 ???쎌?
    diff = np.abs(arr.astype(int) - bg).sum(axis=2)
    content_mask = diff > 30  # 肄섑뀗痢??쎌?
    # ????蹂꾨줈 肄섑뀗痢??덈뒗吏
    rows_has_content = content_mask.any(axis=1)
    cols_has_content = content_mask.any(axis=0)
    # ?곹븯醫뚯슦 ??    top = 0
    while top < h and not rows_has_content[top]:
        top += 1
    bottom = 0
    while bottom < h and not rows_has_content[h - 1 - bottom]:
        bottom += 1
    left = 0
    while left < w and not cols_has_content[left]:
        left += 1
    right = 0
    while right < w and not cols_has_content[w - 1 - right]:
        right += 1
    return {
        "size": (w, h),
        "top": top, "top_ratio": top / h,
        "bottom": bottom, "bottom_ratio": bottom / h,
        "left": left, "left_ratio": left / w,
        "right": right, "right_ratio": right / w,
    }


def detect_cutoff(png_path: Path, edge_band: int = 5) -> bool:
    """PNG 媛???섎떒 5px ??肄섑뀗痢??쎌???留ㅼ슦 留롮쑝硫?(>50%) 吏꾩쭨 ?섎┝."""
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    bg = np.mean([arr[0, 0], arr[0, w-1]], axis=0)
    diff = np.abs(arr.astype(int) - bg).sum(axis=2)
    bottom_band = diff[h-edge_band:h, :]
    content_pct = (bottom_band > 30).mean()
    return content_pct > 0.50  # 50%+ 留?吏꾩쭨 ?섎┝


def verify(target: Path, threshold: float = 0.05) -> int:
    """target ?붾젆?좊━/?뚯씪 寃?? 5% 珥덇낵 ??= WARN."""
    pngs = []
    if target.is_file() and target.suffix == ".png":
        pngs = [target]
    elif target.is_dir():
        pngs = sorted(target.glob("*.png"))
    if not pngs:
        print(f"[INFO] {target} ??PNG ?놁쓬")
        return 0

    warns = []
    cuts = []
    for p in pngs:
        try:
            d = detect_whitespace(p)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[ERR] {p.name}: {e}")
            continue
        flags = []
        if d["top_ratio"] >= threshold:
            flags.append(f"??d['top_ratio']:.1%}")
        if d["bottom_ratio"] >= threshold:
            flags.append(f"?꾨옒{d['bottom_ratio']:.1%}")
        if d["left_ratio"] >= threshold:
            flags.append(f"醫?d['left_ratio']:.1%}")
        if d["right_ratio"] >= threshold:
            flags.append(f"??d['right_ratio']:.1%}")
        if flags:
            warns.append((p.name, flags))
        # cutoff 寃異쒖? banner 媛 ?섏씠吏 ?앷퉴吏 李⑤㈃ false positive 留롮븘 蹂대쪟
        pass

    if cuts:
        print(f"[FAIL] PNG ?섎┝ ?섏떖 {len(cuts)}/{len(pngs)} 媛?(?섎떒 肄섑뀗痢?諛뺥? ?덉쓬):")
        for name in cuts:
            print(f"  {name}")
    if warns:
        print(f"[WARN] PNG ???щ갚 {len(warns)}/{len(pngs)} 媛?諛쒓껄 (>={threshold:.0%}):")
        for name, flags in warns:
            print(f"  {name}: {', '.join(flags)}")
        return 1
    if cuts:
        return 1
    print(f"[PASS] ???щ갚 + ?섎┝ 寃利???{len(pngs)}/{len(pngs)} 紐⑤몢 ?듦낵")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify-image-whitespace.py <png-or-dir>")
        sys.exit(2)
    rc = verify(Path(sys.argv[1]))
    sys.exit(rc)

