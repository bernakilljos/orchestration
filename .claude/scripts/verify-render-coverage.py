"""PNG 肄섑뀗痢?諛??洹몃━??寃?????대? 鍮?諛뺤뒪 ?먯? (?멸낸 ????X).
"""
# Force UTF-8 stdout on Windows (avoid cp949 encode errors for Korean output)
import io
import os
import sys as _sys
if hasattr(_sys.stdout, "buffer"):
    _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding="utf-8")
    _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding="utf-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
__doc__ = """PNG 肄섑뀗痢?諛??洹몃━??寃?????대? 鍮?諛뺤뒪 ?먯? (?멸낸 ????X).

諛곌꼍:
- verify-image-whitespace.py ??PNG ?멸낸 ???좊쭔 寃異?
- 肄섑뀗痢??곸뿭 ?덉뿉 cream-bg 梨꾩썙吏?鍮?諛뺤뒪 (svg-deco 媛 flex 濡?grow ?덉?留?SVG 媛 ?묒쓬)
  媛숈? 耳?댁뒪??紐??≪쓬
- ?ъ슜??"?먮꼫吏 ?먮쫫 ?꾨옒 ?щ갚", "肉뚮━ 源딆? ?섎Т ??怨듬갚" 媛숈? ?몄냼媛 ??耳?댁뒪

?닿껐:
- PNG 瑜?N횞M 洹몃━?쒕줈 遺꾪븷 (湲곕낯 6횞8 = 48 cells)
- 媛????肄섑뀗痢??쎌? 諛??(non-bg + non-near-bg) 痢≪젙
- 諛??< threshold (湲곕낯 18%) = "鍮꾩뼱 蹂댁엫"
- ?몄젒 鍮?? 2媛? ?대윭?ㅽ꽣 = "鍮??곸뿭" -> WARN + crop PNG ?먮룞 ?앹꽦

?ъ슜:
  python verify-render-coverage.py <png>                       # ?⑥씪 寃??
  python verify-render-coverage.py <dir>                       # ?붾젆?좊━ ?쇨큵
  python verify-render-coverage.py <png> --cols 3              # 而щ읆 3 遺꾪븷 (醫?以???
  python verify-render-coverage.py <png> --threshold 0.15      # 諛???꾧퀎移?
  python verify-render-coverage.py <png> --crop-dir _coverage  # crop ????대뜑

醫낅즺 肄붾뱶:
  0 ??PASS (鍮??대윭?ㅽ꽣 ?놁쓬)
  1 ??WARN (鍮??대윭?ㅽ꽣 ?덉쓬, crop PNG ?앹꽦??
  2 ??usage error
"""
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("[SKIP] PIL/numpy ?놁쓬 ??verify-render-coverage 嫄대꼫?")
    sys.exit(0)


def density_grid(png_path: Path, rows: int = 6, cols: int = 8) -> tuple:
    """PNG 瑜?rows횞cols 洹몃━?쒕줈 遺꾪븷 ??媛????肄섑뀗痢??쎌? 諛??諛섑솚.

    諛??= non-bg ?쎌? 鍮꾩쑉 (諛곌꼍???됯퇏怨?diff sum > 45 ???쎌?)
    諛곌꼍?됱? 紐⑥꽌由?4媛??됯퇏 ?ъ슜 (PNG body 諛곌꼍).
    """
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    gray = arr.astype(int).mean(axis=2)
    # Edge density (?띿뒪??stroke / ?꾩씠肄?/ 李⑦듃 媛?μ옄由?
    gy = np.abs(np.diff(gray, axis=0))
    gx = np.abs(np.diff(gray, axis=1))
    edge = np.zeros_like(gray)
    edge[:-1, :] += gy
    edge[:, :-1] += gx
    edge_mask = edge > 12
    # Color variance (?ъ쭊泥섎읆 洹몃씪?곗씠???띾????곸뿭 蹂댁〈)
    # cream (245,239,230) ?먯껜 RGB std??.16, white (255,255,255) std=0
    # -> ?꾧퀎 >8 濡?cream/white 諛곌꼍 ?쒖쇅, ?ъ쭊-?꾩씠肄?(std>15) 留?肄섑뀗痢좊줈
    rgb_std = arr.astype(int).std(axis=2)
    color_mask = rgb_std > 8
    # Brightness ???띿뒪??吏꾪븳??移대뱶 (gray<200) 留?肄섑뀗痢?
    # cream gray??38, white=255 -> ?????쒖쇅
    bright_mask = gray < 200
    # 肄섑뀗痢?= edge OR color variance OR brightness (??以??섎굹留??덉뼱??肄섑뀗痢?
    content_mask = edge_mask | color_mask | bright_mask
    bg = np.array([245, 239, 230])

    cell_h, cell_w = h / rows, w / cols
    grid = np.zeros((rows, cols), dtype=float)
    for r in range(rows):
        for c in range(cols):
            y0, y1 = int(r * cell_h), int((r + 1) * cell_h)
            x0, x1 = int(c * cell_w), int((c + 1) * cell_w)
            cell = content_mask[y0:y1, x0:x1]
            grid[r, c] = cell.mean() if cell.size else 0.0
    return grid, (h, w), (cell_h, cell_w), bg


def find_empty_clusters(grid: np.ndarray, threshold: float = 0.05, min_cluster: int = 2):
    """諛??< threshold ??? 以??몄젒 (?곹븯醫뚯슦) ? ?대윭?ㅽ꽣 諛섑솚.

    諛섑솚: [{"cells": [(r,c), ...], "bbox": (r0,c0,r1,c1)}, ...]
    """
    rows, cols = grid.shape
    empty = grid < threshold
    visited = np.zeros_like(empty, dtype=bool)
    clusters = []

    for r in range(rows):
        for c in range(cols):
            if not empty[r, c] or visited[r, c]:
                continue
            stack = [(r, c)]
            cells = []
            while stack:
                rr, cc = stack.pop()
                if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                    continue
                if visited[rr, cc] or not empty[rr, cc]:
                    continue
                visited[rr, cc] = True
                cells.append((rr, cc))
                stack.extend([(rr + 1, cc), (rr - 1, cc), (rr, cc + 1), (rr, cc - 1)])
            if len(cells) >= min_cluster:
                rs = [rc[0] for rc in cells]
                cs = [rc[1] for rc in cells]
                clusters.append({
                    "cells": cells,
                    "bbox": (min(rs), min(cs), max(rs) + 1, max(cs) + 1),
                    "size": len(cells),
                })
    return clusters


def crop_cluster(png_path: Path, cluster: dict, cell_h: float, cell_w: float,
                 crop_dir: Path, idx: int) -> Path:
    """鍮??대윭?ㅽ꽣 ?곸뿭??crop ?댁꽌 _coverage/<png>_empty_<idx>.png ???"""
    img = Image.open(str(png_path)).convert("RGB")
    r0, c0, r1, c1 = cluster["bbox"]
    # ?ъ쑀 1? padding (?쒓컖 ?뺤씤??
    pad_r, pad_c = 1, 1
    y0 = max(0, int((r0 - pad_r) * cell_h))
    y1 = min(img.size[1], int((r1 + pad_r) * cell_h))
    x0 = max(0, int((c0 - pad_c) * cell_w))
    x1 = min(img.size[0], int((c1 + pad_c) * cell_w))
    crop = img.crop((x0, y0, x1, y1))
    crop_dir.mkdir(parents=True, exist_ok=True)
    out = crop_dir / f"{png_path.stem}_empty_{idx}.png"
    crop.save(str(out))
    return out


def verify(target: Path, rows: int = 6, cols: int = 8, threshold: float = 0.20,
           min_cluster: int = 2, crop_dir: Path = None) -> int:
    """target (PNG/JPG ?먮뒗 ?붾젆?좊━) 寃?? 鍮??대윭?ㅽ꽣 ?덉쑝硫?WARN."""
    pngs = []
    if target.is_file() and target.suffix.lower() in (".png", ".jpg", ".jpeg"):
        pngs = [target]
    elif target.is_dir():
        # ?몃뜑?ㅼ퐫?대줈 ?쒖옉?섎뒗 ?뚯씪 (temp) ?쒖쇅
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            pngs.extend(p for p in target.glob(ext) if not p.name.startswith("_"))
        pngs = sorted(pngs)
    if not pngs:
        print(f"[INFO] {target} ??PNG/JPG ?놁쓬")
        return 0

    if crop_dir is None:
        crop_dir = (pngs[0].parent if pngs[0].is_file() else target) / "_coverage"

    all_warns = []
    for p in pngs:
        try:
            grid, (h, w), (cell_h, cell_w), bg = density_grid(p, rows, cols)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[ERR] {p.name}: {e}")
            continue

        clusters = find_empty_clusters(grid, threshold=threshold, min_cluster=min_cluster)
        if not clusters:
            continue

        # ?멸낸 ??以?(page padding) ?대윭?ㅽ꽣???쒖쇅 ??吏꾩쭨 ?몃? ????
        # ?멸낸 ?留??덈뒗 ?대윭?ㅽ꽣 (bbox 媛 page 寃쎄퀎??遺숈? ?묒? ?? ??skip
        interior_clusters = []
        for cl in clusters:
            r0, c0, r1, c1 = cl["bbox"]
            edge_only = (
                (r1 - r0 == 1 and (r0 == 0 or r1 == rows)) or
                (c1 - c0 == 1 and (c0 == 0 or c1 == cols))
            )
            # ?섏씠吏 ??0% 硫댁쟻? ?멸낸?대씪????鍮??곸뿭 -> ?ы븿
            area_ratio = cl["size"] / (rows * cols)
            if edge_only and area_ratio < 0.10:
                continue
            interior_clusters.append(cl)

        if not interior_clusters:
            continue

        warns_for_png = []
        for idx, cl in enumerate(interior_clusters, 1):
            r0, c0, r1, c1 = cl["bbox"]
            avg_density = float(np.mean([grid[r, c] for r, c in cl["cells"]]))
            crop_path = crop_cluster(p, cl, cell_h, cell_w, crop_dir, idx)
            warns_for_png.append({
                "idx": idx,
                "bbox_grid": (r0, c0, r1, c1),
                "bbox_px": (int(c0 * cell_w), int(r0 * cell_h),
                            int(c1 * cell_w), int(r1 * cell_h)),
                "cells": cl["size"],
                "avg_density": avg_density,
                "crop": crop_path,
            })
        all_warns.append((p, warns_for_png))

    if all_warns:
        print(f"[WARN] 肄섑뀗痢?諛??遺議??곸뿭 {len(all_warns)}/{len(pngs)} 媛?PNG ?먯꽌 諛쒓껄 (諛??< {threshold:.0%}):")
        for png, warns in all_warns:
            print(f"\n  [PNG] {png.name}")
            for w in warns:
                r0, c0, r1, c1 = w["bbox_grid"]
                px = w["bbox_px"]
                print(f"    [{w['idx']}] 洹몃━??({r0},{c0})~({r1},{c1}) "
                      f"= {w['cells']} ?, ?됯퇏諛??{w['avg_density']:.1%}")
                print(f"        ?쎌? bbox: {px}")
                print(f"        crop -> {w['crop']}")
        print(f"\n-> ??crop PNG ?ㅼ쓣 Read tool 濡??쒓컖 ?뺤씤 -> 鍮??곸뿭?대㈃ 肄섑뀗痢?異붽?")
        return 1

    print(f"[PASS] 肄섑뀗痢?諛??洹몃━??寃利???{len(pngs)}/{len(pngs)} 紐⑤몢 ?듦낵 (鍮??대윭?ㅽ꽣 ?놁쓬)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="PNG 肄섑뀗痢?諛??洹몃━??寃?????대? 鍮?諛뺤뒪 ?먯?")
    ap.add_argument("target", help="PNG/JPG ?뚯씪 ?먮뒗 ?붾젆?좊━")
    ap.add_argument("--rows", type=int, default=6, help="洹몃━??????(湲곕낯 6)")
    ap.add_argument("--cols", type=int, default=8, help="洹몃━??????(湲곕낯 8)")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="肄섑뀗痢?諛???꾧퀎移?(湲곕낯 0.05 = 5%%; 吏꾩쭨 鍮??곸뿭 ??%%, "
                         "?띿뒪??移대뱶 6-15%%, ?ъ쭊 30%%+. 5%% ?댄븯留?WARN)")
    ap.add_argument("--min-cluster", type=int, default=2,
                    help="理쒖냼 ?대윭?ㅽ꽣 ? ??(湲곕낯 2)")
    ap.add_argument("--crop-dir", default=None, help="crop PNG ????대뜑 (湲곕낯: target/_coverage)")
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"[ERR] ????놁쓬: {target}")
        return 2

    crop_dir = Path(args.crop_dir) if args.crop_dir else None
    return verify(target, rows=args.rows, cols=args.cols,
                  threshold=args.threshold, min_cluster=args.min_cluster,
                  crop_dir=crop_dir)


if __name__ == "__main__":
    sys.exit(main())

