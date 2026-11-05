"""block-file-deletion.sh 이식 — plugins/ · .claude/scripts/ 파일 삭제 명령 차단 (exit 2 · 메시지는 stdout)."""
from __future__ import annotations

import re

from _common import Result, bash_cat, sed_json_value, tool_name

MSG_PLUGINS = """
[X] [BLOCK] plugins/ 파일 삭제 명령 감지!

  규칙: "명분 없이는 지우지 마" (feedback_no_delete_without_justification.md)

  orchestration_v1 은 template kit. 기존 파일은 명분 없이 삭제 금지.

  허용하는 명분 (3가지 중 하나):
  1. 사용자 명시:        "X 파일 지워줘"
  2. 분석-검증:         md5sum-diff-grep 결과로 확정
  3. git deprecated:    commit message + replacement merged

  우회 방법: rm --force-delete ...

  상세: feedback_no_delete_without_justification.md

"""

MSG_SCRIPTS = """
[X] [BLOCK] .claude/scripts/ 파일 삭제 명령 감지!

  규칙: .claude 체계 파일은 명분 없이 삭제 금지

  허용하는 명분 (3가지 중 하나):
  1. 사용자 명시
  2. 분석-검증 (md5sum-diff)
  3. git deprecated + replacement merged

  우회 방법: rm --force-delete ...

  상세: .claude/rules/cleanup-policy.md

"""

_RM_PLUGINS = re.compile(r"rm\s+.*(-r|-f|--recursive|--force).*plugins/|rm\s+.*plugins/.*(-r|-f|--recursive|--force)")
_RM_SCRIPTS = re.compile(
    r"rm\s+.*(-r|-f|--recursive|--force).*\.claude/scripts/|rm\s+.*\.claude/scripts/.*(-r|-f|--recursive|--force)")

# 2026-11-05 PowerShell: Remove-Item 별칭은 -r/-f 없이도 삭제한다 · 경로 구분자 \ 포함
_PS_RM = r"(?:^|[;|&({]\s*)(?:Remove-Item|ri|rm|rmdir|rd|del|erase)\s[^;|]*"
_RM_PS_PLUGINS = re.compile(_PS_RM + r"plugins[\\/]", re.I)
_RM_PS_SCRIPTS = re.compile(_PS_RM + r"\.claude[\\/]+scripts[\\/]", re.I)


def run(ctx):
    cmd = sed_json_value(bash_cat(ctx.raw), "command")
    if not cmd:
        return None
    has_force = "--force-delete" in cmd
    if tool_name(ctx) == "PowerShell" and not has_force:
        if _RM_PS_PLUGINS.search(cmd):
            return Result(2, MSG_PLUGINS, "")
        if _RM_PS_SCRIPTS.search(cmd):
            return Result(2, MSG_SCRIPTS, "")
    if _RM_PLUGINS.search(cmd) and not has_force:
        return Result(2, MSG_PLUGINS, "")
    if _RM_SCRIPTS.search(cmd) and not has_force:
        return Result(2, MSG_SCRIPTS, "")
    return None
