"""docx -> PDF -> PNG 변환 후 페이지별 시각 검증.

Word COM 으로 docx -> PDF, PyMuPDF 로 PDF -> 페이지별 PNG.
Read tool 로 확인 가능한 PNG 산출.
"""
import sys
import os
from pathlib import Path

_site = Path(sys.executable).parent / "Lib" / "site-packages"
for sub in ("win32", "win32/lib", "Pythonwin"):
    p = _site / sub
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import win32com.client
import fitz


def docx_to_pdf(docx: Path, pdf: Path):
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(docx.resolve()), ReadOnly=True)
        # wdFormatPDF = 17, wdExportFormatPDF = 17
        doc.ExportAsFixedFormat(str(pdf.resolve()), 17)
        doc.Close(SaveChanges=False)
    finally:
        word.Quit()


def pdf_to_pngs(pdf: Path, out_dir: Path, pages: list = None, dpi: int = 100):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with fitz.open(str(pdf)) as d:
        total = len(d)
        target = pages or list(range(1, total + 1))
        for pno in target:
            if pno < 1 or pno > total:
                continue
            page = d[pno - 1]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            out = out_dir / f"page-{pno:03d}.png"
            pix.save(str(out))
            paths.append(out)
    return paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: verify-docx-visual.py <docx> [page1,page2,...]")
        sys.exit(2)
    docx = Path(sys.argv[1])
    pages = None
    if len(sys.argv) >= 3:
        pages = [int(p) for p in sys.argv[2].split(",")]
    pdf = docx.with_suffix(".pdf")
    out_dir = docx.parent / "_visual"
    print(f"[1/3] docx -> pdf ...")
    docx_to_pdf(docx, pdf)
    print(f"  {pdf}")
    print(f"[2/3] pdf -> png (pages={pages or 'all'}) ...")
    pngs = pdf_to_pngs(pdf, out_dir, pages=pages)
    print(f"[3/3] {len(pngs)} PNGs:")
    for p in pngs:
        print(f"  {p}")
