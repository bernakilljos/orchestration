#!/usr/bin/env python
"""docx 진짜 페이지 검증 — Word COM 으로 실제 렌더링 페이지 분석.

verify-docx-structure.py 는 paragraph 만 보고 빈 페이지 못 찾음.
이 스크립트는 Word COM 으로 실제 페이지 분할 + 페이지별 글자 수 측정.

빈 페이지 (0자) 또는 자투리 (<100자) 검출 시 FAIL.
"""
import sys
import os
from pathlib import Path

# pywin32 path 보강 (Python 3.14 + post-install 미실행 케이스)
_site = Path(sys.executable).parent / "Lib" / "site-packages"
for sub in ("win32", "win32/lib", "Pythonwin"):
    p = _site / sub
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import win32com.client
except ImportError:
    print("[SKIP] pywin32 not available — verify-docx-pages 건너뜀")
    sys.exit(0)


SHORT_THRESHOLD = 100  # 100자 미만 = 자투리 의심
EMPTY_THRESHOLD = 5    # 5자 미만 = 빈 페이지


def verify(docx_path: Path, retry: int = 1) -> int:
    if not docx_path.exists():
        print(f"[ERR] {docx_path} 없음")
        return 2

    abspath = str(docx_path.resolve())
    word = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(abspath, ReadOnly=True)
        total = doc.ComputeStatistics(2)  # wdStatisticPages

        empty_pages = []
        short_pages = []
        for pg in range(1, total + 1):
            start = doc.GoTo(What=1, Which=1, Count=pg).Start
            if pg < total:
                end = doc.GoTo(What=1, Which=1, Count=pg + 1).Start
            else:
                end = doc.Content.End
            rng = doc.Range(start, end)
            txt = rng.Text.strip()
            n = len(txt)
            if n < EMPTY_THRESHOLD:
                empty_pages.append((pg, n, txt[:50]))
            elif n < SHORT_THRESHOLD:
                short_pages.append((pg, n, txt[:50]))
        doc.Close(SaveChanges=False)

        print(f"[INFO] {docx_path.name} — 총 {total} 페이지")
        if empty_pages:
            print(f"[FAIL] 빈 페이지 {len(empty_pages)} 개:")
            for pg, n, preview in empty_pages:
                print(f"  page {pg}: {n}자 — {preview!r}")
        if short_pages:
            print(f"[WARN] 자투리 페이지 {len(short_pages)} 개 (<100자):")
            for pg, n, preview in short_pages:
                print(f"  page {pg}: {n}자 — {preview!r}")
        if not empty_pages and not short_pages:
            print(f"[PASS] 빈/자투리 페이지 없음")
            return 0
        return 1 if empty_pages else 0  # 빈 페이지만 FAIL, 자투리는 WARN
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify-docx-pages.py <path-to-docx>")
        sys.exit(2)
    rc = verify(Path(sys.argv[1]))
    sys.exit(rc)
