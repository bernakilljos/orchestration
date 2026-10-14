"""pre-commit-full-check.sh 이식 — git commit 시 문서/설정 동반 갱신 누락 검사 (exit 2).

git commit 명령이 아니면 즉시 통과. 해당될 때만 (git 조회 포함) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import re

from _common import Spawn, bash_cat, grep_o_first, project_guard

_SED_A = re.compile(r'"command"[ \t\r\f\v]*:[ \t\r\f\v]*"')


def run(ctx):
    if not project_guard(ctx):
        return None
    m = grep_o_first(bash_cat(ctx.raw), r'"command"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]*"')
    cmd = ""
    if m is not None:
        cmd = _SED_A.sub("", m, count=1)
        if cmd.endswith('"'):
            cmd = cmd[:-1]
    if re.search(r"git\s+commit", cmd):
        return Spawn(".claude/hooks/pre-commit-full-check.sh")
    return None
