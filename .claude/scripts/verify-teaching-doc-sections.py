#!/usr/bin/env python3
"""verify-teaching-doc-sections.py ??援먯옱/媛뺤쓽 doc 8?뱀뀡 寃利?

猷? .claude/rules/teaching-doc.md
8?뱀뀡: ?듭떖 ??以????먮쫫-媛뺤젏-?쎌젏-媛뺤텛-?곕━ ?쒖뒪??留ㅽ븨-?먭?

?몄텧:
  python verify-teaching-doc-sections.py <docx_or_md_path>

醫낅즺 肄붾뱶:
  0 = ?듦낵
  1 = ?꾨씫 ?뱀뀡 ?덉쓬
  2 = ?뚯씪 紐??쎌쓬
"""
import re
import sys
from pathlib import Path

SECTION_PATTERNS = {
    "1.?듭떖": r"|?듭떖.{0,4}???以??듭떖\s",
    "2.??:   r"[STAT]|^\s*\|.*\|.*\||\<table\>|<tr>",
    "3.?먮쫫": r"|?먮쫫|flow|?④퀎|->",
    "4.媛뺤젏": r"|媛뺤젏|?μ젏",
    "5.?쎌젏": r"[WARN]|?쎌젏|二쇱쓽|?⑥젙|?⑥젏",
    "6.媛뺤텛": r"|媛뺤텛|異붿쿇|?몄젣\s.*?ъ슜",
    "7.留ㅽ븨": r"[TGT]|?곕━\s??쒖뒪???곕━\s?留ㅽ븨|orchestration_v1",
    "8.?먭?": r"|?먭?|check|?뺤씤|泥댄겕",
}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
            return "\n".join(parts)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[ERROR] docx ?쎄린 ?ㅽ뙣: {e}", file=sys.stderr)
            return ""
    elif suffix in (".md", ".txt"):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[ERROR] {suffix} ?쎄린 ?ㅽ뙣: {e}", file=sys.stderr)
            return ""
    elif suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            return ""
    return ""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"[ERROR] ?뚯씪 ?놁쓬: {path}", file=sys.stderr)
        sys.exit(2)

    # 援먯옱/媛뺤쓽/媛?대뱶 doc 留?寃利????뚯씪紐?寃쎈줈 ?대━?ㅽ떛
    name_lower = str(path).lower()
    is_teaching = any(k in name_lower for k in [
        "teaching", "援먯옱", "媛뺤쓽", "guide", "媛?대뱶", "?쒗넗由ъ뼹", "tutorial",
        "docs/", "docs\\",
    ])
    if not is_teaching:
        # 鍮?援먯옱 doc ? skip
        sys.exit(0)

    text = extract_text(path)
    if not text:
        sys.exit(2)

    missing = []
    found = []
    for label, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            found.append(label)
        else:
            missing.append(label)

    if missing:
        # systemMessage 濡?Claude ?먭쾶 ?뚮┝ (PostToolUse 李⑤떒 X)
        print(f"[VIOLATION] teaching-doc 8?뱀뀡 ?꾨씫 ({len(missing)}/8): {missing}",
              file=sys.stderr)
        print(f"[OK] 諛쒓껄: {found}", file=sys.stderr)
        print(f"[FILE] {path}", file=sys.stderr)
        print("[RULE] .claude/rules/teaching-doc.md 짠 媛?梨뺥꽣 ?꾩닔 8 ?뱀뀡",
              file=sys.stderr)
        sys.exit(1)

    print(f"[PASS] {path}: 8?뱀뀡 紐⑤몢 諛쒓껄")
    sys.exit(0)


if __name__ == "__main__":
    main()

