"""block-korean-removal.sh/.py 이식 — Edit 가 한글 글자 수를 줄이면 차단 (exit 2)."""
from __future__ import annotations

import json
import os
import re

from _common import Result

KR = re.compile(r"[가-힣]")


def run(ctx):
    if os.environ.get("ALLOW_KOREAN_REMOVAL") == "1":
        return None
    raw = ctx.raw
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("tool_name", "") != "Edit":
        return None
    ti = data.get("tool_input", {}) or {}
    old = ti.get("old_string", "") or ""
    new = ti.get("new_string", "") or ""
    old_kr = len(KR.findall(old))
    new_kr = len(KR.findall(new))
    if old_kr > 0 and new_kr < old_kr:
        err = ("[BLOCK] korean removal detected: old=%d chars -> new=%d chars\n" % (old_kr, new_kr)
               + "        Edit refused: explicit user consent required to remove korean.\n"
               + "        Bypass: set environment variable ALLOW_KOREAN_REMOVAL=1\n")
        return Result(2, "", err)
    return None
