"""verify-teaching-doc-sections.py 이식 — Edit/Write 후 교재·강의 문서 8섹션 확인 (비차단 안내).

R375 (2026-11-28 · Hook 경량화 기준선): 종전 settings 비동기 훅은 인자 없이 실행돼 사용법만 출력하고 exit 2 로 끝났다
(문서를 한 번도 검사하지 않음 · Edit 마다 python 프로세스 1개). 여기서는 tool_input.file_path 로 원본 판정
(교재 경로 휴리스틱 · extract_text · SECTION_PATTERNS)을 그대로 재사용한다. 누락 = exit 1 의미(비차단 · stderr 안내).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from _common import Result, load_script, tool_input

_SUFFIX = (".md", ".txt", ".docx", ".pdf")
_TEACHING = ("teaching", "교재", "강의", "guide", "가이드", "튜토리얼", "tutorial", "docs/", "docs\\")


def run(ctx):
    fp = tool_input(ctx).get("file_path") or ""
    if not isinstance(fp, str) or not fp.lower().endswith(_SUFFIX):
        return None
    if not any(k in fp.lower() for k in _TEACHING):     # 원본과 같은 교재 판정 (비교재 = 건너뜀)
        return None
    path = Path(fp)
    if not path.is_file():
        return None
    mod = load_script("verify-teaching-doc-sections")
    if mod is None:
        return None
    try:
        text = mod.extract_text(path)
    except Exception:  # noqa: BLE001
        return None
    if not text:
        return None
    missing = [k for k, pat in mod.SECTION_PATTERNS.items() if not re.search(pat, text, re.IGNORECASE | re.MULTILINE)]
    if not missing:
        return None
    msg = (f"[VIOLATION] teaching-doc 8섹션 누락 ({len(missing)}/8): {missing}\n"
           f"[FILE] {os.path.normpath(fp)}\n[RULE] .claude/rules/teaching-doc.md § 각 챕터 필수 8 섹션")
    return Result(1, "", msg)
