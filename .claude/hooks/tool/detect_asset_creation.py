"""detect-asset-creation.sh 이식 — Write 로 새 rule/hook/skill/command/agent/memory 를 만들 때 유사 파일 경고.

Write 가 아니거나 자산 경로 패턴이 아니면 즉시 통과. 해당될 때만 (드묾) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import re

from _common import Spawn, bash_cat, glob_any, grep_o_first, has_jq

REL = ".claude/hooks/detect-asset-creation.sh"
_SED = re.compile(r'.*: *"(.*)"$')


def _val(inp: str, key: str) -> str:
    m = grep_o_first(inp, r'"%s"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]*"' % key)
    if m is None:
        return ""
    mm = _SED.match(m)
    return mm.group(1) if mm else m


_KIND = (
    "*/.claude/rules/*.md", "*/rules/*.md", "*/.claude/hooks/*.sh", "*/hooks/*.sh", "*/.claude/hooks/*.ps1",
    "*/hooks/*.ps1", "*/.claude/hooks/*.py", "*/hooks/*.py", "*/.claude/hooks/*.md", "*/hooks/*.md",
    "*/.claude/skills/*.md", "*/skills/*.md", "*/.claude/commands/*.md", "*/commands/*.md",
    "*/.claude/agents/*.md", "*/agents/*.md", "*memory/feedback_*.md", "*memory/reference_*.md",
)


def run(ctx):
    if has_jq():
        return Spawn(REL)
    inp = bash_cat(ctx.raw)
    if _val(inp, "tool_name") != "Write":
        return None
    p = _val(inp, "file_path")
    if not p:
        return None
    if not glob_any(p, *_KIND):
        return None
    return Spawn(REL)
