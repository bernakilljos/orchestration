"""pre-commit-full-check.sh 이식 — git commit 시 문서/설정 동반 갱신 누락 검사 (exit 2).

git commit 명령이 아니면 즉시 통과. 해당될 때만 (git 조회 포함) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import re

from _common import Result, Spawn, bash_cat, grep_o_first, project_guard

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
    if is_git_commit_invocation(cmd):
        return Spawn(".claude/hooks/pre-commit-full-check.sh")
    if is_svn_commit_invocation(cmd):
        return _svn_syntax_gate(ctx)
    return None


# 2026-11-15 (R256): 커밋 훅이 git commit 에만 반응해 실제 개발 프로젝트(IFRS = SVN)의 svn commit 은 변경 소스 문법 검사를
#   한 번도 거치지 않았다. git 과 같은 방식 — 무거운 검사는 `independent_verifier.py syntax-gate` 가 하고 수정 파일 내용 해시와
#   함께 기록 · 이 훅(5초 제한)은 지금 수정 파일 해시가 기록과 같고 상태가 pass/skip 인지만 본다. 다르면·없으면 차단.
#   커밋 대상 경로를 지정해도 작업본 전체 수정 파일을 본다 (보수적).
_RX_SVN_COMMIT_AT_CMD = re.compile(
    r"(?:^|[;&|(\n{]|\$\()\s*(?:\w+=\S*\s+)*(?:command\s+|exec\s+|&\s*)?svn(?:\.exe)?"
    r"(?:\s+-[^\s;&|]+(?:\s+[^\s;&|-][^\s;&|]*)?)*\s+(?:commit|ci)(?![\w.-])",
    re.I,
)


def is_svn_commit_invocation(cmd: str) -> bool:
    if not cmd or not re.search(r"svn", cmd, re.I):
        return False
    cmd = cmd.replace("\\n", "\n").replace('\\"', '"')
    cmd = _RX_HEREDOC.sub("<<DOC", cmd)
    cmd = _RX_QUOTED.sub("''", cmd)
    return bool(_RX_SVN_COMMIT_AT_CMD.search(cmd))


def _svn_syntax_gate(ctx):
    import importlib.util
    import json
    import os
    from pathlib import Path
    root = Path(ctx.project_dir)
    if not (root / ".svn").is_dir():
        return None   # SVN 작업본이 아닌 프로젝트 — 해당 없음
    run_cmd = "python -X utf8 .claude/scripts/lib/independent_verifier.py syntax-gate"

    def _block(msg):
        return Result(2, "", "\n[X] [BLOCK] svn commit 전 변경 소스 문법 게이트\n  - %s\n  - 실행: %s (수정 파일이 바뀌면 다시)\n"
                      % (msg, run_cmd))
    try:
        spec = importlib.util.spec_from_file_location(
            "_iv_svn_gate", os.path.join(str(root), ".claude", "scripts", "lib", "independent_verifier.py"))
        iv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(iv)
        changed = iv._svn_changed(root, timeout=4)
        if changed is None:
            return _block("svn status 로 수정 파일을 확인하지 못함 — 검사 여부를 확정할 수 없어 차단")
        code = [p for p in changed if p.lower().endswith(iv._CODE_EXT)]
        if not code:
            return None
        stamp = json.loads((root / iv.SYNTAX_STAMP).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _block("문법 게이트 기록 없음")
    except Exception as e:  # noqa: BLE001 — 확인 실패 = 차단 (fail-closed)
        return _block("문법 게이트 확인 실패 (%s)" % type(e).__name__)
    if stamp.get("files") != iv.file_hashes(root, code):
        return _block("문법 게이트 기록이 지금 수정 파일과 다름 (검사 뒤 파일이 바뀌었거나 새 파일)")
    st = stamp.get("status")
    if st in ("pass", "skip"):
        return None
    if st == "syntax_error":
        return _block("변경 소스 문법 오류: " + (stamp.get("reason") or "") + " — 고친 뒤 다시")
    if st == "unverified":
        return _block("문법 검사기가 없어 확인 못 한 변경 파일 — 검증 완료로 보지 않아 자동 커밋하지 않음: "
                      + ", ".join(stamp.get("syntax_unchecked") or []))
    return _block("문법 게이트 상태 %s: %s" % (st, stamp.get("reason") or ""))


# 2026-11-09: 명령 본문(echo·grep 검색어·커밋 메시지·heredoc)에 'git commit' 글자만 있어도
# 커밋으로 오인해 회귀 게이트가 막던 결함. 실행 위치(명령 시작)에 있는 git commit 만 인정한다.
_RX_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?=\s*(?:\n|$))", re.S)
_RX_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
_RX_COMMIT_AT_CMD = re.compile(
    r"(?:^|[;&|(\n{]|\$\()\s*(?:\w+=\S*\s+)*(?:command\s+|exec\s+)?git(?:\.exe)?"
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
