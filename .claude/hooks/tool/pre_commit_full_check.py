"""pre-commit-full-check.sh 이식 — git commit 시 문서/설정 동반 갱신 누락 검사 (exit 2).

git commit 명령이 아니면 즉시 통과. 해당될 때만 (git 조회 포함) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import re

from _common import Spawn, bash_cat, grep_o_first, project_guard, tool_command



def run(ctx):
    if not project_guard(ctx):
        return None
    cmd = tool_command(ctx)
    if is_git_commit_invocation(cmd):
        return Spawn(".claude/hooks/pre-commit-full-check.sh")
    return None


# 2026-11-09: 명령 본문(echo·grep 검색어·커밋 메시지·heredoc)에 'git commit' 글자만 있어도
# 커밋으로 오인해 회귀 게이트가 막던 결함. 실행 위치(명령 시작)에 있는 git commit 만 인정한다.
_RX_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?=\s*(?:\n|$))", re.S)
_RX_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
# 11-15(사이클 1038): 'timeout 590 git commit' 처럼 감싸는 명령이 앞에 붙으면 못 봐 회귀 게이트를 건너뛰었다 → 흔한 감싸개 허용.
_WRAP = (r"(?:(?:timeout(?:\s+-{1,2}[\w-]+(?:[=\s]\S+)?)*\s+\d+\S*|time(?:\s+-p)?|nice(?:\s+-n\s*-?\d+)?"
         r"|nohup|env(?:\s+\w+=\S*)*|stdbuf(?:\s+-\S+)*|command|exec)\s+(?:\w+=\S*\s+)*)*")
_RX_COMMIT_AT_CMD = re.compile(
    r"(?:^|[;&|(\n{]|\$\()\s*(?:\w+=\S*\s+)*" + _WRAP + r"git(?:\.exe)?"
    r"(?:\s+(?:-[Cc]\s+\S+|--[\w-]+(?:=\S+)?))*\s+commit(?![\w-])",
    re.I,
)


def is_git_commit_invocation(cmd: str) -> bool:
    if not cmd or not re.search(r"git", cmd, re.I):
        return False
    cmd = cmd.replace("\\n", "\n").replace('\\"', '"')
    cmd = _RX_HEREDOC.sub("<<DOC", cmd)
    cmd = _RX_QUOTED.sub("''", cmd)
    return bool(_RX_COMMIT_AT_CMD.search(cmd))
