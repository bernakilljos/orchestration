"""block-tricks.sh/.py 이식 — Edit 의 꼼수 패턴 (한글 삭제 · 시크릿→placeholder · U+FFFD 우회 · 자동응답 회귀) 차단 (exit 2)."""
from __future__ import annotations

import json
import os
import re

from _common import Result

KR = re.compile(r"[" + chr(0xAC00) + "-" + chr(0xD7A3) + "]")
SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{30,})")
PLACEHOLDER_HINTS = ["YOUR_TOKEN_HERE", "YOUR_API_KEY", "REPLACE_WITH", "YOUR_GOOGLE_API_KEY"]


def run(ctx):
    if os.environ.get("ALLOW_TRICKS") == "1":
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
    violations = []

    # T1. 한글 삭제
    old_kr = len(KR.findall(old))
    new_kr = len(KR.findall(new))
    if old_kr > 0 and new_kr < old_kr:
        violations.append("T1 KOREAN_REMOVAL: " + str(old_kr) + " to " + str(new_kr))

    # T2. 시크릿 -> placeholder
    old_has_secret = bool(SECRET_RE.search(old))
    new_has_secret = bool(SECRET_RE.search(new))
    new_has_placeholder = any(h in new for h in PLACEHOLDER_HINTS)
    if old_has_secret and not new_has_secret and new_has_placeholder:
        violations.append("T2 SECRET_TO_PLACEHOLDER: real secret -> placeholder")

    # T3. GITHUB_PAT 전용
    old_pat_m = re.search(r"GITHUB_PAT=([^\s\r\n]+)", old)
    new_pat_m = re.search(r"GITHUB_PAT=([^\s\r\n]+)", new)
    if old_pat_m and new_pat_m:
        if "YOUR_TOKEN" not in old_pat_m.group(1) and "YOUR_TOKEN" in new_pat_m.group(1):
            violations.append("T3 PAT_TO_PLACEHOLDER")

    # T4. 깨짐 우회 (소스에 U+FFFD 를 직접 쓰지 않고 런타임 조립)
    ffffd_seq = chr(0xFFFD)
    ffffd_escape = "\\" + "u" + "fffd"
    if ffffd_seq in new and ffffd_seq not in old:
        violations.append("T4 MOJIBAKE_LITERAL_ADDED")
    if ffffd_escape in new and ffffd_escape not in old:
        violations.append("T4 MOJIBAKE_ESCAPE_ADDED")
    if "chr(0xFFFD)" in new and "chr(0xFFFD)" not in old:
        violations.append("T4 CHR_BYPASS_ADDED")

    # T5. 자동응답 회귀
    old_choice = len(re.findall(r"\bchoice\s+/c", old))
    new_choice = len(re.findall(r"\bchoice\s+/c", new))
    old_setp = len(re.findall(r"\bset\s+/p\b", old))
    new_setp = len(re.findall(r"\bset\s+/p\b", new))
    old_timeout = len(re.findall(r"\btimeout\s+/t", old))
    new_timeout = len(re.findall(r"\btimeout\s+/t", new))
    old_pause = len(re.findall(r"\bpause\s*(>nul)?\s*$", old, re.MULTILINE))
    new_pause = len(re.findall(r"\bpause\s*(>nul)?\s*$", new, re.MULTILINE))
    if old_choice > new_choice and new_setp > old_setp:
        violations.append("T5 CHOICE_TO_SETP_REGRESSION")
    if old_timeout > new_timeout and new_pause > old_pause:
        violations.append("T5 TIMEOUT_TO_PAUSE_REGRESSION")

    if violations:
        err = "[BLOCK] Trick patterns detected (Edit refused):\n"
        for v in violations:
            err += "  - " + v + "\n"
        err += "\nIf user explicitly authorized this change:\n"
        err += "  Bypass: set environment variable ALLOW_TRICKS=1\n"
        return Result(2, "", err)
    return None
