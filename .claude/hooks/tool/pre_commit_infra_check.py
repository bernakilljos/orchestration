"""pre-commit-infra-check.sh 이식 — git commit 시 인프라 변경인데 문서 미변경이면 차단 (exit 2).

git commit 명령이 아니면 즉시 통과. 해당될 때만 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import re

from _common import Spawn, bash_cat, grep_o_first

_SED_A = re.compile(r'"command"[ \t\r\f\v]*:[ \t\r\f\v]*"')


def run(ctx):
    m = grep_o_first(bash_cat(ctx.raw), r'"command"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]*"')
    cmd = ""
    if m is not None:
        cmd = _SED_A.sub("", m, count=1)
        if cmd.endswith('"'):
            cmd = cmd[:-1]
    if re.search(r"git\s+commit", cmd):
        return Spawn(".claude/hooks/pre-commit-infra-check.sh")
    return None
