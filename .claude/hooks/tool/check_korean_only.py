"""check-korean-only.sh 이식 — templates/*.html 의 영어 UI 텍스트 경고 (stderr · 비차단 · exit 0)."""
from __future__ import annotations

import os
import re

from _common import Result, bash_field, bash_read, glob_any

_RX = re.compile(r">(Dashboard|Total Assets|Invested|Settings|Loading|No data|Submit|Cancel|Save|Delete|Search|"
                 r"Filter|Community|Bookmark|Wishlist|Hot Deals|Coupons|Compare|Alerts|Goal|Trend)<")


def run(ctx):
    inp = bash_read(ctx.raw)
    if "templates" not in inp:
        return None
    fp = bash_field(inp, "file_path")
    if not glob_any(fp, "*templates*.html"):
        return None
    if not os.path.isfile(fp):
        return None
    try:
        with open(fp, "rb") as f:
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    found = []
    for line in data.split("\n"):
        found.extend(m.group(0) for m in _RX.finditer(line))
        if len(found) >= 5:
            break
    found = found[:5]
    if not found:
        return None
    joined = "\n".join(found)
    err = ("WARNING: 영어 UI 텍스트 발견 — 한국어로 변경 필요: %s\n" % joined
           + "한국어 전용 플랫폼입니다. 영어 UI 텍스트를 한국어로 바꿔주세요.\n")
    return Result(0, "", err)
