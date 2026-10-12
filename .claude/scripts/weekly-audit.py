#!/usr/bin/env python3
"""
weekly-audit.py — 주 1회 (일요일 04:00) 실행
1. 중복 파일 감지 (md5)
2. 유사 파일 감지 (Levenshtein)
3. 순수 숫자 파일명 리스트
4. 리포트: .claude/logs/weekly-audit-YYYYMMDD.md

근거: .claude/rules/auto-optimization.md
"""
from __future__ import annotations

import hashlib
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    from difflib import SequenceMatcher
except ImportError:
    SequenceMatcher = None

# 환경 변수 기반 동적 경로 (하드코딩 X)
ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = ROOT / ".claude" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# 로깅 설정
LOG_FILE = LOGS / f"weekly-audit-{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def file_md5(path: Path, chunk_size: int = 8192) -> str:
    """파일 MD5 해시 계산."""
    try:
        h = hashlib.md5()
        with path.open("rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return ""


def levenshtein_ratio(a: str, b: str) -> float:
    """Levenshtein 거리 기반 유사도 (0~1)."""
    if SequenceMatcher is None:
        return 0.0
    m = SequenceMatcher(None, a, b)
    return m.ratio()


def is_pure_number_name(name: str) -> bool:
    """순수 숫자 파일명 판정 (예: 1.jpg, 01.png)."""
    stem = Path(name).stem
    return stem.isdigit() and int(stem) >= 0


def scan_duplicates(root: Path) -> dict:
    """MD5 기반 중복 파일 감지."""
    md5_map = defaultdict(list)
    for p in root.rglob("*"):
        if p.is_file() and p.stat().st_size > 0:
            h = file_md5(p)
            if h:
                md5_map[h].append(p)

    duplicates = {h: paths for h, paths in md5_map.items() if len(paths) > 1}
    return duplicates


def scan_similar_files(root: Path, threshold: float = 0.8) -> list:
    """파일명 기반 유사 파일 감지."""
    files = [p for p in root.rglob("*") if p.is_file()]
    similar = []

    for i, f1 in enumerate(files):
        for f2 in files[i + 1 :]:
            ratio = levenshtein_ratio(f1.name, f2.name)
            if threshold <= ratio < 1.0:  # 완전 동일은 제외
                similar.append((f1, f2, ratio))

    # 상위 10건만
    similar.sort(key=lambda x: x[2], reverse=True)
    return similar[:10]


def scan_numbered_files(root: Path) -> list:
    """순수 숫자 파일명 리스트."""
    numbered = []
    for p in root.rglob("*"):
        if p.is_file() and is_pure_number_name(p.name):
            numbered.append(p)
    return sorted(numbered)


def main() -> int:
    """주간 감사 실행."""
    logger.info("=== weekly-audit start ===")

    report_lines = [
        f"# Weekly Audit Report\n",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        "\n",
    ]

    # 1. 중복 파일
    logger.info("scanning duplicates...")
    duplicates = scan_duplicates(ROOT)
    report_lines.append("## Duplicate Files (by MD5)\n")
    if duplicates:
        for h, paths in sorted(duplicates.items()):
            report_lines.append(f"\n**Hash**: `{h[:16]}...`\n")
            for p in paths:
                report_lines.append(f"- {p.relative_to(ROOT)}\n")
        logger.info(f"found {len(duplicates)} duplicate groups")
    else:
        report_lines.append("*(no duplicates detected)*\n")

    # 2. 유사 파일
    logger.info("scanning similar files...")
    similar = scan_similar_files(ROOT)
    report_lines.append("\n## Similar Files (by name, threshold 0.80)\n")
    if similar:
        for f1, f2, ratio in similar:
            report_lines.append(
                f"\n**{ratio:.2%}** similarity\n"
                f"- {f1.relative_to(ROOT)}\n"
                f"- {f2.relative_to(ROOT)}\n"
            )
        logger.info(f"found {len(similar)} similar pairs")
    else:
        report_lines.append("*(no similar files detected)*\n")

    # 3. 순수 숫자 파일명
    logger.info("scanning numbered files...")
    numbered = scan_numbered_files(ROOT)
    report_lines.append("\n## Numbered Files (pure digits)\n")
    if numbered:
        for p in numbered:
            report_lines.append(f"- {p.relative_to(ROOT)}\n")
        logger.info(f"found {len(numbered)} numbered files")
    else:
        report_lines.append("*(no numbered files detected)*\n")

    # 리포트 작성
    report_file = LOGS / f"weekly-audit-{datetime.now().strftime('%Y%m%d')}.md"
    report_file.write_text("".join(report_lines), encoding="utf-8")
    logger.info(f"report saved: {report_file.name}")
    logger.info("=== done ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
