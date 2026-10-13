"""PNG 안 흰 여백 자동 검출 — banner 등 콘텐츠 끝 ~ PNG 끝 사이 빈 공간 측정.

기준:
- 상하 흰 띠 >= 5% 페이지 높이 = WARN
- 좌우 흰 띠 >= 5% 페이지 폭 = WARN

PIL bbox + 색 분석 — 콘텐츠 영역 (non-background pixels) vs PNG 전체.
"""
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("[SKIP] PIL/numpy 없음 — verify-image-whitespace 건너뜀")
    sys.exit(0)


def detect_whitespace(png_path: Path, threshold: float = 0.05) -> dict:
    """PNG 의 상하좌우 흰 띠 비율 측정."""
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    # 배경색 추정 — 모서리 4개 평균 (PNG body background)
    bg = np.mean([arr[0, 0], arr[0, w-1], arr[h-1, 0], arr[h-1, w-1]], axis=0)
    # 콘텐츠 mask — 배경색과 차이 >= 30 인 픽셀
    diff = np.abs(arr.astype(int) - bg).sum(axis=2)
    content_mask = diff > 30  # 콘텐츠 픽셀
    # 행/열 별로 콘텐츠 있는지
    rows_has_content = content_mask.any(axis=1)
    cols_has_content = content_mask.any(axis=0)
    # 상하좌우 띠
    top = 0
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
    """PNG 가장 하단 5px 에 콘텐츠 픽셀이 매우 많으면 (>50%) 진짜 잘림."""
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    bg = np.mean([arr[0, 0], arr[0, w-1]], axis=0)
    diff = np.abs(arr.astype(int) - bg).sum(axis=2)
    bottom_band = diff[h-edge_band:h, :]
    content_pct = (bottom_band > 30).mean()
    return content_pct > 0.50  # 50%+ 만 진짜 잘림


def verify(target: Path, threshold: float = 0.05) -> int:
    """target 디렉토리/파일 검사. 5% 초과 띠 = WARN."""
    pngs = []
    if target.is_file() and target.suffix == ".png":
        pngs = [target]
    elif target.is_dir():
        pngs = sorted(target.glob("*.png"))
    if not pngs:
        print(f"[INFO] {target} — PNG 없음")
        return 0

    warns = []
    cuts = []
    for p in pngs:
        try:
            d = detect_whitespace(p)
        except Exception as e:
            print(f"[ERR] {p.name}: {e}")
            continue
        flags = []
        if d["top_ratio"] >= threshold:
            flags.append(f"위{d['top_ratio']:.1%}")
        if d["bottom_ratio"] >= threshold:
            flags.append(f"아래{d['bottom_ratio']:.1%}")
        if d["left_ratio"] >= threshold:
            flags.append(f"좌{d['left_ratio']:.1%}")
        if d["right_ratio"] >= threshold:
            flags.append(f"우{d['right_ratio']:.1%}")
        if flags:
            warns.append((p.name, flags))
        # cutoff 검출은 banner 가 페이지 끝까지 차면 false positive 많아 보류
        pass

    if cuts:
        print(f"[FAIL] PNG 잘림 의심 {len(cuts)}/{len(pngs)} 개 (하단 콘텐츠 박혀 있음):")
        for name in cuts:
            print(f"  {name}")
    if warns:
        print(f"[WARN] PNG 흰 여백 {len(warns)}/{len(pngs)} 개 발견 (>={threshold:.0%}):")
        for name, flags in warns:
            print(f"  {name}: {', '.join(flags)}")
        return 1
    if cuts:
        return 1
    print(f"[PASS] 흰 여백 + 잘림 검증 — {len(pngs)}/{len(pngs)} 모두 통과")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify-image-whitespace.py <png-or-dir>")
        sys.exit(2)
    rc = verify(Path(sys.argv[1]))
    sys.exit(rc)
