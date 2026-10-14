"""block-version-suffix.sh 이식 — 산출물 파일명 -v2/_v2 접미사 차단 (exit 2 · 메시지는 stdout)."""
from __future__ import annotations

import re

from _common import Result, bash_basename, bash_cat, sed_json_value

MSG = """
[X] [BLOCK] 산출물 버전 접미사 감지!

  규칙: 빌드 결과물 (.docx/.pptx/.pdf 등) 에 -v2, -v3, _v2 자동 추가 금지

  금지:   report-v2.docx, slides_v3.pptx
  허용:   report.docx (원본 덮어쓰기), report.docx.bak (백업)

  방법:
  1. 파일 잠겨있으면 -> 사용자에게 알림 ("원본 닫아주세요")
  2. 파일 접근 가능하면 -> .bak 백업 후 원본 자리에 덮어쓰기
  3. 버전은 사용자 명시 요청 시만

  상세: .claude/rules/teaching-doc.md § 산출물 명명
         feedback_no_version_suffix.md

"""

_VER = re.compile(r"-v[0-9]|_v[0-9]", re.I)
_EXT = re.compile(r"\.(docx|pptx|pdf|xlsx|doc|ppt|md|txt|html|rst|adoc|ipynb)$", re.I)


def run(ctx):
    inp = bash_cat(ctx.raw)
    fp = sed_json_value(inp, "file_path")
    if not fp:
        return None
    base = bash_basename(fp)
    if not base:
        return None
    if _VER.search(base) and _EXT.search(base):
        return Result(2, MSG, "")
    return None
