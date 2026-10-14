"""block-file-deletion.sh 이식 — plugins/ · .claude/scripts/ 파일 삭제 명령 차단 (exit 2 · 메시지는 stdout)."""
from __future__ import annotations

import re

from _common import Result, bash_cat, sed_json_value

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


def run(ctx):
    cmd = sed_json_value(bash_cat(ctx.raw), "command")
    if not cmd:
        return None
    has_force = "--force-delete" in cmd
    if _RM_PLUGINS.search(cmd) and not has_force:
        return Result(2, MSG_PLUGINS, "")
    if _RM_SCRIPTS.search(cmd) and not has_force:
        return Result(2, MSG_SCRIPTS, "")
    return None
