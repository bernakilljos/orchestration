#!/usr/bin/env python
"""
diagnose-failure.py · 07-repair.yaml step `diagnose` stub

근거:
- environment-dependent-bug.md · measurement-two-deaths.md · investigation-discipline.md
- 2026-10-27 workflow-run.log ERROR fix

로직 (minimal):
- failure_report (string) 입력
- 패턴 매칭으로 root_cause 분류 (hardcoded path · timeout · permission · syntax)
- 다음 세션 실 분석 로직 추가 (LLM 호출 · stack trace parse)

CLI:
  python diagnose-failure.py --report "<text>"
  python diagnose-failure.py --file <log_path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PATTERNS = [
    (r"ModuleNotFoundError|ImportError", "missing_dependency"),
    (r"Permission denied|PermissionError", "permission"),
    (r"not found|No such file", "missing_file"),
    (r"timeout|TimeoutExpired", "timeout"),
    (r"SyntaxError|IndentationError", "syntax"),
    (r"ConnectionError|unreachable|refused", "network"),
    (r"0x80070002", "file_not_found_s4u"),
    (r"UnicodeDecodeError|UnicodeEncodeError|cp949", "encoding"),
    (r"out of memory|MemoryError|OOM", "memory"),
    (r"deadlock|lock timeout", "lock"),
]


def diagnose(report: str) -> dict:
    causes = []
    for pat, label in PATTERNS:
        if re.search(pat, report, re.IGNORECASE):
            causes.append(label)
    return {
        "report_len": len(report),
        "root_cause_candidates": causes or ["unknown"],
        "note": "stub · 매칭 기반 · 실 LLM 분석은 다음 세션",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()
    text = args.report
    if args.file:
        p = Path(args.file)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
    if not text:
        print(json.dumps({"error": "--report or --file required"}, ensure_ascii=False))
        return 2
    print(json.dumps(diagnose(text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
