#!/usr/bin/env python
"""docx 吏꾩쭨 ?섏씠吏 寃利???Word COM ?쇰줈 ?ㅼ젣 ?뚮뜑留??섏씠吏 遺꾩꽍.

verify-docx-structure.py ??paragraph 留?蹂닿퀬 鍮??섏씠吏 紐?李얠쓬.
???ㅽ겕由쏀듃??Word COM ?쇰줈 ?ㅼ젣 ?섏씠吏 遺꾪븷 + ?섏씠吏蹂?湲????痢≪젙.

鍮??섏씠吏 (0?? ?먮뒗 ?먰닾由?(<100?? 寃異???FAIL.
"""
import sys
import os
from pathlib import Path

# pywin32 path 蹂닿컯 (Python 3.14 + post-install 誘몄떎??耳?댁뒪)
_site = Path(sys.executable).parent / "Lib" / "site-packages"
for sub in ("win32", "win32/lib", "Pythonwin"):
    p = _site / sub
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import win32com.client
except ImportError:
    print("[SKIP] pywin32 not available ??verify-docx-pages 嫄대꼫?")
    sys.exit(0)


SHORT_THRESHOLD = 100  # 100??誘몃쭔 = ?먰닾由??섏떖
EMPTY_THRESHOLD = 5    # 5??誘몃쭔 = 鍮??섏씠吏


def verify(docx_path: Path, retry: int = 1) -> int:
    if not docx_path.exists():
        print(f"[ERR] {docx_path} ?놁쓬")
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

        print(f"[INFO] {docx_path.name} ??珥?{total} ?섏씠吏")
        if empty_pages:
            print(f"[FAIL] 鍮??섏씠吏 {len(empty_pages)} 媛?")
            for pg, n, preview in empty_pages:
                print(f"  page {pg}: {n}????{preview!r}")
        if short_pages:
            print(f"[WARN] ?먰닾由??섏씠吏 {len(short_pages)} 媛?(<100??:")
            for pg, n, preview in short_pages:
                print(f"  page {pg}: {n}????{preview!r}")
        if not empty_pages and not short_pages:
            print(f"[PASS] 鍮??먰닾由??섏씠吏 ?놁쓬")
            return 0
        return 1 if empty_pages else 0  # 鍮??섏씠吏留?FAIL, ?먰닾由щ뒗 WARN
    finally:
        if word is not None:
            try:
                word.Quit()
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify-docx-pages.py <path-to-docx>")
        sys.exit(2)
    rc = verify(Path(sys.argv[1]))
    sys.exit(rc)

