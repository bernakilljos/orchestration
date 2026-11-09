"""한글이 든 PowerShell 스크립트에 UTF-8 BOM 자동 부착 (비차단 · exit 0).

이유: Windows PowerShell 5.1 은 BOM 없는 .ps1 을 시스템 코드페이지(cp949)로 읽어 한글이 한자처럼 깨진다
      (2026-11-09 Stage 1 관리자 창 안내문 · 그룹 확인 정규식 실패).
시점: PostToolUse Edit|Write — 방금 저장한 .ps1/.psm1/.psd1 에 BOM 부착 (저장 단계 정규화)
      PreToolUse Bash|PowerShell — 실행하려는 .ps1 은 고치지 않고 알리기만 한다 (2026-11-09: 실행 직전 수정은
      승인 때 해시와 실제 실행 파일을 다르게 만든다 · 승인 게이트가 그 차이를 '스크립트 변경' 으로 막는다)
처리: 비ASCII 바이트가 있고 BOM 이 없으면 BOM 만 앞에 붙인다 (내용 불변 · 순수 ASCII 는 손대지 않음).
      쓰기 실패는 조용히 넘기지 않고 메시지로 남긴다.
"""
from __future__ import annotations

import os
import re

from _common import Result, tool_input, tool_name

BOM = b"\xef\xbb\xbf"
_EXT = (".ps1", ".psm1", ".psd1")
_RX_PATH = re.compile(r"""(?:"([^"]+\.ps[dm]?1)"|'([^']+\.ps[dm]?1)'|([^\s"'`;|&<>()]+\.ps[dm]?1))""", re.I)


def _needs_bom(path: str):
    """BOM 이 필요하면 파일 내용(bytes), 아니면 None. UTF-8 이 아니면 (이미 cp949 등) BOM 을 붙이면 더 깨진다 → None."""
    if not os.path.isfile(path) or not path.lower().endswith(_EXT):
        return None
    with open(path, "rb") as f:
        data = f.read()
    if data.startswith(BOM) or not any(b > 127 for b in data):
        return None
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return data


def _fix(path: str):
    """True = 붙임 · False = 필요 없음 · str = 실패 사유 (조용히 넘기지 않는다)."""
    try:
        data = _needs_bom(path)
        if data is None:
            return False
        with open(path, "wb") as f:
            f.write(BOM + data)
        return True
    except OSError as e:
        return "%s: %s" % (type(e).__name__, e)


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
    if tn in ("Edit", "Write", "MultiEdit"):
        fp = ti.get("file_path") or ""
        r = _fix(fp) if fp else False
        if r is True:
            return Result(0, "", "[한글 보호] PowerShell 5.1 한자 깨짐 방지 — UTF-8 BOM 부착: %s\n" % fp)
        if isinstance(r, str):
            return Result(0, "", "[한글 보호] BOM 부착 실패 (한글이 깨질 수 있음): %s — %s\n" % (fp, r))
        return None
    if tn in ("Bash", "PowerShell"):
        cmd = ti.get("command") or ""
        if ".ps" not in cmd.lower():
            return None
        cwd = ctx.payload.get("cwd") or os.getcwd()
        need, seen = [], set()
        for m in _RX_PATH.finditer(cmd):
            p = _norm(next(g for g in m.groups() if g), cwd)
            if p in seen:
                continue
            seen.add(p)
            try:
                if _needs_bom(p) is not None:
                    need.append(p)
            except OSError:
                pass
        if need:
            return Result(0, "", "[한글 보호] BOM 없는 한글 .ps1 — 실행 직전에는 고치지 않음 (승인 해시 보존) · "
                                 "PowerShell 5.1 에서 한글이 깨질 수 있으니 Write/Edit 로 다시 저장하면 BOM 이 붙는다: %s\n"
                          % ", ".join(need))
    return None
