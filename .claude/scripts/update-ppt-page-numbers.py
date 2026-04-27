"""
update-ppt-page-numbers.py — PPT 슬라이드 페이지번호 일괄 갱신

새 슬라이드 추가/삭제 후 모든 HTML 의 NN/총수 표기를 일괄 갱신.
정렬 순서대로 1, 2, 3... 부여하고, Cover 의 SLIDES 메트릭과 Learn More 의 "N slides" 도 함께 갱신.

사용:
  python .claude/scripts/update-ppt-page-numbers.py
  python .claude/scripts/update-ppt-page-numbers.py --dir outputs/ppt/html-source/slides
  python .claude/scripts/update-ppt-page-numbers.py --dry-run

함정 회피:
  - Cover 슬라이드 (slide-01.html) 는 NN/총수 형식 X — SLIDES 메트릭만 갱신
  - Learn More (slide-25.html 등) 는 "N slides" 형식 — 별도 패턴 처리
  - 알파벳 정렬: slide-04 < slide-04a < slide-04b < slide-05
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_slide_files(slides_dir: Path) -> list[Path]:
    """slide-*.html 파일을 알파벳 순으로 반환."""
    files = sorted(slides_dir.glob("slide-*.html"))
    return files


def detect_slide_kind(content: str, filename: str) -> str:
    """슬라이드 종류 탐지: cover / learn-more / standard."""
    # Cover: SLIDES 메트릭 박스 (stat-item .label 'Slides')
    if re.search(r'class="label">\s*Slides\s*</div>', content):
        return "cover"
    # Learn More: "Opus ... · N slides" 표기
    if re.search(r"Opus\s+[\d.]+\s+Baseline\s*·\s*\d+\s+slides", content):
        return "learn-more"
    # Standard: NN / 총수 caption
    if re.search(r'class="mono caption">\s*\d+\s*/\s*\d+\s*</span>', content):
        return "standard"
    # Divider 슬라이드는 별도 패턴 (`.pageno`)
    if re.search(r'class="pageno">\s*\d+\s*/\s*\d+\s*</span>', content):
        return "divider"
    return "unknown"


def update_standard(content: str, page_no: int, total: int) -> str:
    """표준 슬라이드: <span class="mono caption">XX / YY</span> 갱신."""
    pattern = re.compile(r'(class="mono caption">\s*)(\d+)(\s*/\s*)(\d+)(\s*</span>)')
    return pattern.sub(rf'\g<1>{page_no:02d}\g<3>{total}\g<5>', content)


def update_divider(content: str, page_no: int, total: int) -> str:
    """Divider 슬라이드: <span class="pageno">XX / YY</span> 갱신."""
    pattern = re.compile(r'(class="pageno">\s*)(\d+)(\s*/\s*)(\d+)(\s*</span>)')
    return pattern.sub(rf'\g<1>{page_no:02d}\g<3>{total}\g<5>', content)


def update_cover(content: str, total: int) -> str:
    """Cover: <div class="value">N</div> (SLIDES 메트릭) 갱신.

    'Slides' 라벨 다음에 오는 value 만 정확히 교체."""
    pattern = re.compile(
        r'(class="label">\s*Slides\s*</div>\s*<div class="value">)(\d+)(</div>)',
        re.MULTILINE,
    )
    return pattern.sub(rf'\g<1>{total}\g<3>', content)


def update_learn_more(content: str, total: int) -> str:
    """Learn More: 'Opus 4.7 Baseline · N slides' 갱신."""
    pattern = re.compile(r'(Opus\s+[\d.]+\s+Baseline\s*·\s*)(\d+)(\s+slides)')
    return pattern.sub(rf'\g<1>{total}\g<3>', content)


def main():
    parser = argparse.ArgumentParser(description="Update PPT slide page numbers")
    parser.add_argument(
        "--dir",
        default="outputs/ppt/html-source/slides",
        help="Slides directory (default: outputs/ppt/html-source/slides)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing",
    )
    args = parser.parse_args()

    slides_dir = Path(args.dir)
    if not slides_dir.exists():
        print(f"[ERROR] Slides directory not found: {slides_dir}")
        sys.exit(1)

    files = find_slide_files(slides_dir)
    total = len(files)

    if total == 0:
        print(f"[ERROR] No slide-*.html files in {slides_dir}")
        sys.exit(1)

    print(f"[INFO] Found {total} slide files in {slides_dir}")
    print(f"[INFO] Page number scheme: NN / {total}")
    print()

    changed = 0
    for idx, fp in enumerate(files, start=1):
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        kind = detect_slide_kind(content, fp.name)
        original = content

        if kind == "standard":
            content = update_standard(content, idx, total)
        elif kind == "divider":
            content = update_divider(content, idx, total)
        elif kind == "cover":
            content = update_cover(content, total)
        elif kind == "learn-more":
            content = update_learn_more(content, total)

        if content != original:
            mark = "DRY" if args.dry_run else "OK "
            print(f"[{mark}] {fp.name:30s} → page {idx:02d}/{total} ({kind})")
            if not args.dry_run:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(content)
            changed += 1
        else:
            print(f"[--] {fp.name:30s} → page {idx:02d}/{total} ({kind}, no change)")

    print()
    if args.dry_run:
        print(f"[DRY RUN] Would update {changed}/{total} files")
    else:
        print(f"[DONE] Updated {changed}/{total} files")


if __name__ == "__main__":
    main()
