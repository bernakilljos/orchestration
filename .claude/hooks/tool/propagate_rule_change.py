"""propagate-rule-change.sh 이식 - 룰/CLAUDE.md/guide.txt 편집 시 확산 후보 알림 (additionalContext).

대상 파일이 아니면 즉시 통과. 해당될 때만 (grep 다수) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import os
import re

from _common import Spawn, bash_cat, glob_any, project_guard

_RX = re.compile(r'"file_path"\s*:\s*"([^"]+)')


def run(ctx):
    if not project_guard(ctx):
        return None
    tool_input = os.environ.get("TOOL_INPUT", "")
    if not tool_input:
        tool_input = bash_cat(ctx.raw)
    f = ""
    for line in tool_input.split("\n"):
        m = _RX.search(line)
        if m:
            f = m.group(1)
            break
    if glob_any(f, "*.claude/rules/*.md", "*CLAUDE.md", "*guide.txt"):
        return Spawn(".claude/hooks/propagate-rule-change.sh")
    return None
