"""secret-scan.sh 이식 — git commit/push 직전 staged 파일 시크릿 스캔 (deny JSON).

git commit/push 로 시작하는 명령이 아니면 즉시 통과 (대부분의 Bash 호출). 해당될 때만 원본 스크립트에 위임한다.
"""
from __future__ import annotations

from _common import Spawn, bash_field, bash_read


def run(ctx):
    inp = bash_read(ctx.raw)
    if "git commit" not in inp and "git push" not in inp:
        return None
    cmd = bash_field(inp, "command")
    if cmd.startswith("git commit") or cmd.startswith("git push"):
        return Spawn(".claude/hooks/secret-scan.sh")
    return None
