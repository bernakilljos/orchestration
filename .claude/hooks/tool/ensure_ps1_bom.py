"""한글이 든 PowerShell 스크립트에 UTF-8 BOM 자동 부착 (비차단 · exit 0).

이유: Windows PowerShell 5.1 은 BOM 없는 .ps1 을 시스템 코드페이지(cp949)로 읽어 한글이 한자처럼 깨진다
      (2026-11-09 Stage 1 관리자 창 안내문 · 그룹 확인 정규식 실패).
시점: PostToolUse Edit|Write — 방금 저장한 .ps1/.psm1/.psd1
      PreToolUse Bash|PowerShell — 명령이 실행하려는 .ps1 (Bash heredoc 등으로 만든 파일 포함)
처리: 비ASCII 바이트가 있고 BOM 이 없으면 BOM 만 앞에 붙인다 (내용 불변 · 순수 ASCII 는 손대지 않음).
"""
from __future__ import annotations

import os
import re

from _common import Result, tool_input, tool_name

BOM = b"\xef\xbb\xbf"
_EXT = (".ps1", ".psm1", ".psd1")
_RX_PATH = re.compile(r"""(?:"([^"]+\.ps[dm]?1)"|'([^']+\.ps[dm]?1)'|([^\s"'`;|&<>()]+\.ps[dm]?1))""", re.I)


def _fix(path: str) -> bool:
    try:
        if not os.path.isfile(path) or not path.lower().endswith(_EXT):
            return False
        with open(path, "rb") as f:
            data = f.read()
        if data.startswith(BOM) or not any(b > 127 for b in data):
            return False
        data.decode("utf-8")  # UTF-8 이 아니면 (이미 cp949 등) BOM 을 붙이면 더 깨진다 → 건드리지 않음
        with open(path, "wb") as f:
            f.write(BOM + data)
        return True
    except (OSError, UnicodeDecodeError):
        return False


def _norm(p: str, cwd: str) -> str:
    p = p.strip()
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)  # Git Bash /c/... → C:/...
    if m:
        p = "%s:/%s" % (m.group(1).upper(), m.group(2))
    p = os.path.expandvars(os.path.expanduser(p))
    if not os.path.isabs(p):
        p = os.path.join(cwd, p)
    return p


def run(ctx):
    tn = tool_name(ctx)
    ti = tool_input(ctx)
    fixed = []
    if tn in ("Edit", "Write", "MultiEdit"):
        fp = ti.get("file_path") or ""
        if fp and _fix(fp):
            fixed.append(fp)
    elif tn in ("Bash", "PowerShell"):
        cmd = ti.get("command") or ""
        if ".ps" not in cmd.lower():
            return None
        cwd = ctx.payload.get("cwd") or os.getcwd()
        seen = set()
        for m in _RX_PATH.finditer(cmd):
            p = _norm(next(g for g in m.groups() if g), cwd)
            if p not in seen:
                seen.add(p)
                if _fix(p):
                    fixed.append(p)
    if not fixed:
        return None
    return Result(0, "", "[한글 보호] PowerShell 5.1 한자 깨짐 방지 — UTF-8 BOM 부착: %s\n" % ", ".join(fixed))
