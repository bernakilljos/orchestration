#!/usr/bin/env bash
# design_pdf plugin — PDF 생성 wrapper (PyMuPDF / reportlab)
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PYTHONIOENCODING=utf-8 python -c "
import sys
try:
    import fitz  # PyMuPDF
    print(f'[design_pdf] PyMuPDF {fitz.__version__} 사용 가능')
except ImportError:
    print('[design_pdf] PyMuPDF 없음 — pip install PyMuPDF')
    sys.exit(1)
print('use: PyMuPDF (fitz) for PDF generation. See SPEC.md')
"
