#!/usr/bin/env python3
"""
auto-optimize-image.py ??PostToolUse Write 媛먯? ???먮룞 ?ㅽ뻾
1. ?좉퇋 PNG/JPG 媛먯?
2. 3MB 珥덇낵 ??由ъ궗?댁쫰 (max 2000횞2000)
3. .bak ?먮낯 ?좎?

洹쇨굅: .claude/rules/auto-optimization.md
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

# ?섍꼍 蹂??湲곕컲 ?숈쟻 寃쎈줈
ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = ROOT / ".claude" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# 濡쒓퉭
LOG_FILE = LOGS / "auto-optimize-image.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ?곸닔
SIZE_THRESHOLD = 3 * 1024 * 1024  # 3MB
MAX_DIM = 2000  # 理쒕? 2000횞2000
ALLOWED_EXTS = {".png", ".jpg", ".jpeg"}


def check_pil() -> bool:
    """PIL ?ㅼ튂 ?뺤씤."""
    if Image is None:
        logger.error("PIL/Pillow not installed. Install with: pip install pillow")
        return False
    return True


def optimize_image(file_path: Path, dry_run: bool = False) -> bool:
    """?대?吏 理쒖쟻??(由ъ궗?댁쫰)."""
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"file not found: {file_path}")
        return False

    # ?뺤옣???뺤씤
    if file_path.suffix.lower() not in ALLOWED_EXTS:
        logger.debug(f"skipped (not image): {file_path.name}")
        return False

    # ?ш린 ?뺤씤
    file_size = file_path.stat().st_size
    if file_size < SIZE_THRESHOLD:
        logger.debug(f"skipped (< 3MB): {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")
        return False

    logger.info(f"optimizing: {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")

    if dry_run:
        logger.info(f"[DRY] would optimize {file_path}")
        return True

    # PIL ?뺤씤
    if not check_pil():
        return False

    try:
        # 諛깆뾽 ?앹꽦
        bak_path = file_path.with_suffix(file_path.suffix + ".bak")
        if not bak_path.exists():
            import shutil

            shutil.copy2(file_path, bak_path)
            logger.info(f"backed up: {bak_path.name}")

        # ?대?吏 濡쒕뱶
        img = Image.open(file_path)
        original_size = img.size

        # 由ъ궗?댁쫰 ?꾩슂 ?щ? ?먯젙
        if max(original_size) > MAX_DIM:
            # 鍮꾩쑉 ?좎? 由ъ궗?댁쫰
            img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
            logger.info(f"resized: {original_size} ??{img.size}")
        else:
            # ?덉쭏 ?ъ븬異뺣쭔
            logger.info(f"recompressing: {original_size} (within max dims)")

        # ???(?덉쭏 議곗젙)
        quality = 85 if file_path.suffix.lower() in {".jpg", ".jpeg"} else None
        if quality:
            img.save(file_path, quality=quality, optimize=True)
        else:
            img.save(file_path, optimize=True)

        new_size = file_path.stat().st_size
        reduction_pct = 100 * (1 - new_size / file_size)
        logger.info(f"optimized: {file_size / 1024 / 1024:.1f}MB ??{new_size / 1024 / 1024:.1f}MB ({reduction_pct:.1f}% reduction)")
        return True

    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.error(f"failed to optimize {file_path}: {e}")
        return False


def scan_and_optimize(start_path: Path = None, dry_run: bool = False, recursive: bool = False) -> int:
    """?붾젆?좊━ ?ㅼ틪 諛??대?吏 理쒖쟻??"""
    if start_path is None:
        start_path = ROOT

    if not start_path.exists():
        logger.error(f"path not found: {start_path}")
        return 1

    logger.info(f"scanning: {start_path}")

    if recursive:
        images = list(start_path.rglob("*"))
    else:
        images = list(start_path.glob("*"))

    count = 0
    for p in images:
        if optimize_image(p, dry_run):
            count += 1

    logger.info(f"optimized {count} images")
    return 0


def main(file_path: str = None, dry_run: bool = False, recursive: bool = False) -> int:
    """CLI 吏꾩엯??"""
    logger.info("=== auto-optimize-image start ===")

    if file_path:
        # ?⑥씪 ?뚯씪
        p = Path(file_path)
        result = optimize_image(p, dry_run)
        logger.info("=== done ===")
        return 0 if result else 1

    # ?붾젆?좊━ ?ㅼ틪
    return scan_and_optimize(dry_run=dry_run, recursive=recursive)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-optimize images (resize/compress)")
    parser.add_argument("file", nargs="?", default=None, help="Image file to optimize (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no write)")
    parser.add_argument("--recursive", action="store_true", help="Scan recursively")

    args = parser.parse_args()

    sys.exit(main(file_path=args.file, dry_run=args.dry_run, recursive=args.recursive))

