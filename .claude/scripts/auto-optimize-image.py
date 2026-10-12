#!/usr/bin/env python3
"""
auto-optimize-image.py — PostToolUse Write 감지 시 자동 실행
1. 신규 PNG/JPG 감지
2. 3MB 초과 시 리사이즈 (max 2000×2000)
3. .bak 원본 유지

근거: .claude/rules/auto-optimization.md
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

# 환경 변수 기반 동적 경로
ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = ROOT / ".claude" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# 로깅
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

# 상수
SIZE_THRESHOLD = 3 * 1024 * 1024  # 3MB
MAX_DIM = 2000  # 최대 2000×2000
ALLOWED_EXTS = {".png", ".jpg", ".jpeg"}


def check_pil() -> bool:
    """PIL 설치 확인."""
    if Image is None:
        logger.error("PIL/Pillow not installed. Install with: pip install pillow")
        return False
    return True


def optimize_image(file_path: Path, dry_run: bool = False) -> bool:
    """이미지 최적화 (리사이즈)."""
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"file not found: {file_path}")
        return False

    # 확장자 확인
    if file_path.suffix.lower() not in ALLOWED_EXTS:
        logger.debug(f"skipped (not image): {file_path.name}")
        return False

    # 크기 확인
    file_size = file_path.stat().st_size
    if file_size < SIZE_THRESHOLD:
        logger.debug(f"skipped (< 3MB): {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")
        return False

    logger.info(f"optimizing: {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")

    if dry_run:
        logger.info(f"[DRY] would optimize {file_path}")
        return True

    # PIL 확인
    if not check_pil():
        return False

    try:
        # 백업 생성
        bak_path = file_path.with_suffix(file_path.suffix + ".bak")
        if not bak_path.exists():
            import shutil

            shutil.copy2(file_path, bak_path)
            logger.info(f"backed up: {bak_path.name}")

        # 이미지 로드
        img = Image.open(file_path)
        original_size = img.size

        # 리사이즈 필요 여부 판정
        if max(original_size) > MAX_DIM:
            # 비율 유지 리사이즈
            img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
            logger.info(f"resized: {original_size} → {img.size}")
        else:
            # 품질 재압축만
            logger.info(f"recompressing: {original_size} (within max dims)")

        # 저장 (품질 조정)
        quality = 85 if file_path.suffix.lower() in {".jpg", ".jpeg"} else None
        if quality:
            img.save(file_path, quality=quality, optimize=True)
        else:
            img.save(file_path, optimize=True)

        new_size = file_path.stat().st_size
        reduction_pct = 100 * (1 - new_size / file_size)
        logger.info(f"optimized: {file_size / 1024 / 1024:.1f}MB → {new_size / 1024 / 1024:.1f}MB ({reduction_pct:.1f}% reduction)")
        return True

    except Exception as e:
        logger.error(f"failed to optimize {file_path}: {e}")
        return False


def scan_and_optimize(start_path: Path = None, dry_run: bool = False, recursive: bool = False) -> int:
    """디렉토리 스캔 및 이미지 최적화."""
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
    """CLI 진입점."""
    logger.info("=== auto-optimize-image start ===")

    if file_path:
        # 단일 파일
        p = Path(file_path)
        result = optimize_image(p, dry_run)
        logger.info("=== done ===")
        return 0 if result else 1

    # 디렉토리 스캔
    return scan_and_optimize(dry_run=dry_run, recursive=recursive)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-optimize images (resize/compress)")
    parser.add_argument("file", nargs="?", default=None, help="Image file to optimize (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no write)")
    parser.add_argument("--recursive", action="store_true", help="Scan recursively")

    args = parser.parse_args()

    sys.exit(main(file_path=args.file, dry_run=args.dry_run, recursive=args.recursive))
