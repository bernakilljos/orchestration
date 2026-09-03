"""PNG 콘텐츠 밀도 그리드 검사 — 내부 빈 박스 탐지 (외곽 흰 띠 X).
"""
# Force UTF-8 stdout on Windows (avoid cp949 encode errors for Korean output)
import io
import os
import sys as _sys
if hasattr(_sys.stdout, "buffer"):
    _sys.stdout = io.TextIOWrapper(_sys.stdout.buffer, encoding="utf-8")
    _sys.stderr = io.TextIOWrapper(_sys.stderr.buffer, encoding="utf-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
__doc__ = """PNG 콘텐츠 밀도 그리드 검사 — 내부 빈 박스 탐지 (외곽 흰 띠 X).

배경:
- verify-image-whitespace.py 는 PNG 외곽 흰 띠만 검출
- 콘텐츠 영역 안에 cream-bg 채워진 빈 박스 (svg-deco 가 flex 로 grow 했지만 SVG 가 작음)
  같은 케이스는 못 잡음
- 사용자 "에너지 흐름 아래 여백", "뿌리 깊은 나무 위 공백" 같은 호소가 이 케이스

해결:
- PNG 를 N×M 그리드로 분할 (기본 6×8 = 48 cells)
- 각 셀의 콘텐츠 픽셀 밀도 (non-bg + non-near-bg) 측정
- 밀도 < threshold (기본 18%) = "비어 보임"
- 인접 빈 셀 2개+ 클러스터 = "빈 영역" -> WARN + crop PNG 자동 생성

사용:
  python verify-render-coverage.py <png>                       # 단일 검사
  python verify-render-coverage.py <dir>                       # 디렉토리 일괄
  python verify-render-coverage.py <png> --cols 3              # 컬럼 3 분할 (좌/중/우)
  python verify-render-coverage.py <png> --threshold 0.15      # 밀도 임계치
  python verify-render-coverage.py <png> --crop-dir _coverage  # crop 저장 폴더

종료 코드:
  0 — PASS (빈 클러스터 없음)
  1 — WARN (빈 클러스터 있음, crop PNG 생성됨)
  2 — usage error
"""
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("[SKIP] PIL/numpy 없음 — verify-render-coverage 건너뜀")
    sys.exit(0)


def density_grid(png_path: Path, rows: int = 6, cols: int = 8) -> tuple:
    """PNG 를 rows×cols 그리드로 분할 후 각 셀의 콘텐츠 픽셀 밀도 반환.

    밀도 = non-bg 픽셀 비율 (배경색 평균과 diff sum > 45 인 픽셀)
    배경색은 모서리 4개 평균 사용 (PNG body 배경).
    """
    img = Image.open(str(png_path)).convert("RGB")
    arr = np.array(img)
    h, w = arr.shape[:2]
    gray = arr.astype(int).mean(axis=2)
    # Edge density (텍스트 stroke / 아이콘 / 차트 가장자리)
    gy = np.abs(np.diff(gray, axis=0))
    gx = np.abs(np.diff(gray, axis=1))
    edge = np.zeros_like(gray)
    edge[:-1, :] += gy
    edge[:, :-1] += gx
    edge_mask = edge > 12
    # Color variance (사진처럼 그라데이션 풍부한 영역 보존)
    # cream (245,239,230) 자체 RGB std≈6.16, white (255,255,255) std=0
    # -> 임계 >8 로 cream/white 배경 제외, 사진-아이콘 (std>15) 만 콘텐츠로
    rgb_std = arr.astype(int).std(axis=2)
    color_mask = rgb_std > 8
    # Brightness — 텍스트-진한색 카드 (gray<200) 만 콘텐츠
    # cream gray≈238, white=255 -> 둘 다 제외
    bright_mask = gray < 200
    # 콘텐츠 = edge OR color variance OR brightness (셋 중 하나만 있어도 콘텐츠)
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
    """밀도 < threshold 인 셀 중 인접 (상하좌우) 셀 클러스터 반환.

    반환: [{"cells": [(r,c), ...], "bbox": (r0,c0,r1,c1)}, ...]
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
    """빈 클러스터 영역을 crop 해서 _coverage/<png>_empty_<idx>.png 저장."""
    img = Image.open(str(png_path)).convert("RGB")
    r0, c0, r1, c1 = cluster["bbox"]
    # 여유 1셀 padding (시각 확인용)
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
    """target (PNG/JPG 또는 디렉토리) 검사. 빈 클러스터 있으면 WARN."""
    pngs = []
    if target.is_file() and target.suffix.lower() in (".png", ".jpg", ".jpeg"):
        pngs = [target]
    elif target.is_dir():
        # 언더스코어로 시작하는 파일 (temp) 제외
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            pngs.extend(p for p in target.glob(ext) if not p.name.startswith("_"))
        pngs = sorted(pngs)
    if not pngs:
        print(f"[INFO] {target} — PNG/JPG 없음")
        return 0

    if crop_dir is None:
        crop_dir = (pngs[0].parent if pngs[0].is_file() else target) / "_coverage"

    all_warns = []
    for p in pngs:
        try:
            grid, (h, w), (cell_h, cell_w), bg = density_grid(p, rows, cols)
        except Exception as e:
            print(f"[ERR] {p.name}: {e}")
            continue

        clusters = find_empty_clusters(grid, threshold=threshold, min_cluster=min_cluster)
        if not clusters:
            continue

        # 외곽 한 줄 (page padding) 클러스터는 제외 — 진짜 외부 흰 띠
        # 외곽 셀만 있는 클러스터 (bbox 가 page 경계에 붙은 작은 띠) 는 skip
        interior_clusters = []
        for cl in clusters:
            r0, c0, r1, c1 = cl["bbox"]
            edge_only = (
                (r1 - r0 == 1 and (r0 == 0 or r1 == rows)) or
                (c1 - c0 == 1 and (c0 == 0 or c1 == cols))
            )
            # 페이지 ≥30% 면적은 외곽이라도 큰 빈 영역 -> 포함
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
        print(f"[WARN] 콘텐츠 밀도 부족 영역 {len(all_warns)}/{len(pngs)} 개 PNG 에서 발견 (밀도 < {threshold:.0%}):")
        for png, warns in all_warns:
            print(f"\n  [PNG] {png.name}")
            for w in warns:
                r0, c0, r1, c1 = w["bbox_grid"]
                px = w["bbox_px"]
                print(f"    [{w['idx']}] 그리드 ({r0},{c0})~({r1},{c1}) "
                      f"= {w['cells']} 셀, 평균밀도 {w['avg_density']:.1%}")
                print(f"        픽셀 bbox: {px}")
                print(f"        crop -> {w['crop']}")
        print(f"\n-> 위 crop PNG 들을 Read tool 로 시각 확인 -> 빈 영역이면 콘텐츠 추가")
        return 1

    print(f"[PASS] 콘텐츠 밀도 그리드 검증 — {len(pngs)}/{len(pngs)} 모두 통과 (빈 클러스터 없음)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="PNG 콘텐츠 밀도 그리드 검사 — 내부 빈 박스 탐지")
    ap.add_argument("target", help="PNG/JPG 파일 또는 디렉토리")
    ap.add_argument("--rows", type=int, default=6, help="그리드 행 수 (기본 6)")
    ap.add_argument("--cols", type=int, default=8, help="그리드 열 수 (기본 8)")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="콘텐츠 밀도 임계치 (기본 0.05 = 5%%; 진짜 빈 영역 ≈0%%, "
                         "텍스트 카드 6-15%%, 사진 30%%+. 5%% 이하만 WARN)")
    ap.add_argument("--min-cluster", type=int, default=2,
                    help="최소 클러스터 셀 수 (기본 2)")
    ap.add_argument("--crop-dir", default=None, help="crop PNG 저장 폴더 (기본: target/_coverage)")
    args = ap.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"[ERR] 대상 없음: {target}")
        return 2

    crop_dir = Path(args.crop_dir) if args.crop_dir else None
    return verify(target, rows=args.rows, cols=args.cols,
                  threshold=args.threshold, min_cluster=args.min_cluster,
                  crop_dir=crop_dir)


if __name__ == "__main__":
    sys.exit(main())
