"""block_dangerous_bash.py 이식 — 파괴적 Bash 명령 deny (permissionDecision: deny JSON · exit 0).

stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - _common.py 의 PY_STDIN_FIX 설명 참고.
원본은 deny JSON 을 stdout(시스템 기본 인코딩 · strict) 으로 쓰다가 명령에 깨진 글자가 섞이면 UnicodeEncodeError 로
죽는다 (exit 1 · deny 미전달). 같은 결과를 재현한다.
"""
from __future__ import annotations

import json
import re
import sys

from _common import Result, py_child_encoding, py_stdin_text

UNIVERSAL = [r"\bdd\s+if=", r"\bshutdown\b", r"\breboot\b", r"\bpoweroff\b"]
UNIX_LIKE = [r"\brm\s+-rf\b", r"\brm\s+-fr\b", r"\brm\s+-r\s+-f\b", r"\bmkfs\."]
WINDOWS = [r"\bdel\s+/s\s+/q\b", r"\brmdir\s+/s\s+/q\b", r"\bformat\s+[a-zA-Z]:\b",
           r"\bRemove-Item\b.*\s-Recurse\b.*\s-Force\b"]

_HEREDOC = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?[^\n]*\n.*?\n[ \t]*\1\b", re.DOTALL)
_DQ = re.compile(r'"(?:[^"\\]|\\.)*"')
_SQ = re.compile(r"'[^']*'")


def _patterns():
    if sys.platform == "win32":  # platform.system() 은 이 PC 에서 첫 호출이 느리다 (uname 조회) - 같은 판정
        return UNIVERSAL + WINDOWS + UNIX_LIKE
    return UNIVERSAL + UNIX_LIKE


def _strip_quoted(cmd: str) -> str:
    cmd = _HEREDOC.sub(r"<<\1>>", cmd)
    cmd = _DQ.sub('""', cmd)
    cmd = _SQ.sub("''", cmd)
    return cmd


def run(ctx):
    try:
        payload = json.loads(py_stdin_text(ctx))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    ti = payload.get("tool_input", {}) or {}
    cmd = ti.get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return None
    target = _strip_quoted(cmd)
    for pat in _patterns():
        if re.search(pat, target, re.IGNORECASE):
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                          "permissionDecisionReason": "[BLOCK] 위험 명령 차단: %s" % cmd[:200]}}
            text = json.dumps(out, ensure_ascii=False)
            try:
                text.encode(py_child_encoding())     # 원본 sys.stdout.write 의 인코딩 실패 재현
            except UnicodeEncodeError as e:
                return Result(1, "", "UnicodeEncodeError: %s\n" % e)
            return Result(0, text, "")
    return None
