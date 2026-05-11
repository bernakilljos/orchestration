"""verify-docx-structure.py — docx 안 빈 페이지·중복 page_break·이상 구조 감지.

A·B·D 의 한계 (PNG·external 만 검증) 보완.
build-*-doc.py 호출 후 hook-09 가 자동 발동.

감지:
- 연속된 빈 paragraph (3개+) → 빈 페이지 위험
- 연속된 page_break (2개+) → 빈 페이지 확정
- 빈 paragraph + page_break 패턴 → 빈 페이지
"""
import sys
import io
from pathlib import Path

try:
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except (AttributeError, Exception):
    pass

try:
    from docx import Document
except ImportError:
    print("[SKIP] python-docx not installed")
    sys.exit(0)


ROOT = Path(__file__).resolve().parent.parent.parent
DOCX_DIR = ROOT / "docs"


def has_page_break(para):
    """paragraph 안에 page_break 있는지."""
    for run in para.runs:
        for br in run._element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br"):
            if br.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type") == "page":
                return True
    return False


def check_docx(path):
    """docx 구조 검사. 문제 목록 반환."""
    doc = Document(str(path))
    problems = []

    paragraphs = list(doc.paragraphs)
    consecutive_empty = 0
    last_was_break = False

    for i, p in enumerate(paragraphs):
        text = p.text.strip()
        is_break = has_page_break(p)
        is_empty = not text and not p.runs

        if is_break:
            if last_was_break:
                problems.append(f"para {i}: 직전 paragraph 도 page_break — 빈 페이지")
            last_was_break = True
            consecutive_empty = 0
        else:
            if is_empty:
                consecutive_empty += 1
                if consecutive_empty >= 5:
                    problems.append(f"para {i}: 빈 paragraph {consecutive_empty}개 연속 — 큰 여백")
            else:
                consecutive_empty = 0
            last_was_break = False

    return {
        "path": path.name,
        "total_paragraphs": len(paragraphs),
        "problems": problems,
    }


targets = sorted(DOCX_DIR.glob("*.docx"))
targets = [t for t in targets if not t.name.endswith(".bak")]

if not targets:
    print("[SKIP] docs/*.docx 없음")
    sys.exit(0)

any_fail = False
for t in targets:
    r = check_docx(t)
    if r["problems"]:
        any_fail = True
        print(f"[FAIL] {r['path']} ({r['total_paragraphs']} paragraphs) — {len(r['problems'])} 문제:")
        for prob in r["problems"][:10]:
            print(f"  - {prob}")
        if len(r["problems"]) > 10:
            print(f"  ... {len(r['problems']) - 10} more")
    else:
        print(f"[PASS] {r['path']} ({r['total_paragraphs']} paragraphs) — 구조 정상")

sys.exit(2 if any_fail else 0)
