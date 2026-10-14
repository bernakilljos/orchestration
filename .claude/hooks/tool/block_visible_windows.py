"""block-visible-windows.sh 이식 (e39d316 판) - 세션이 보이는 창(CMD·PowerShell·서버 콘솔)을 띄우기 전에 차단 (exit 2).

판정: (1) 명령 자체가 창을 연다 (start /b·/min 없이 · cmd /k · Start-Process -WindowStyle Hidden·-NoNewWindow 없이)
      (2) 명령이 실행하는 .bat/.cmd/.ps1 파일 안에 (1) 이 있다 (cd "DIR" 의 DIR 기준으로 상대 경로 해석)
우회: 명령에 ALLOW_VISIBLE_WINDOW=1.
원본의 bash [[ =~ ]] 는 nocasematch + POSIX ERE ([[:space:]]) 이다 - 같은 의미의 python 정규식으로 옮겼다.
POSIX 절대경로(/tmp/x.bat 등 드라이브 표기가 아닌 것) 는 python 이 msys 경로를 못 풀어 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import os
import re

from _common import Result, Spawn, bash_read

REL = ".claude/hooks/block-visible-windows.sh"
_S = r"[ \t\n\r\f\v]"
_I = re.I
_RE_COMMENT = re.compile(r"^" + _S + r"*(rem" + _S + r"|::|#)", _I)
_RE_START = re.compile(r"(^|[ \t\n\r\f\v&|(])start" + _S, _I)
_RE_HIDDEN_START = re.compile(_S + r"/(b|min)(" + _S + r"|\Z)", _I)
_RE_PROG = re.compile(r'(cmd|powershell|pwsh|python|py' + _S + r'|\.exe|\.bat|\.cmd|%PY%|"%)', _I)
_RE_CMDK = re.compile(r"cmd(\.exe)?" + _S + r"+//?k(" + _S + r"|\Z)", _I)
_RE_SP = re.compile(r"Start-Process", _I)
_RE_SP_HIDDEN = re.compile(r"(-WindowStyle" + _S + r"+Hidden|-NoNewWindow)", _I)
_RE_CDQ = re.compile(r'cd' + _S + r'+"([^"]+)"', _I)
_RE_CD = re.compile(r"cd" + _S + r"+([^ \t\n\r\f\v&;]+)", _I)
_RE_FILE = re.compile(r"([A-Za-z]:[\\/][^\"' \t\n\r\f\v]*|[^\"' \t\n\r\f\v]*)\.(bat|cmd|ps1)", _I)

_GATE = ("start", "START", "Start", "cmd /k", "cmd //k", ".bat", ".BAT", ".cmd", ".ps1")

MSG_1 = "BLOCKED(창 예방): %s\n"
MSG_2 = ("  → 테스트·검증은 창 없이: run_in_background 로 직접 실행 (예: python run.py …) · 프로젝트에 숨김 모드가 있으면 그것 "
         "· start 를 쓰면 /b\n")
MSG_3 = "  → 테스트로 띄운 프로세스는 끝나면 닫는다 (원래 떠 있던 서버는 원래 방식으로 되돌린다).\n"
MSG_4 = "  → 사용자가 창을 원하면 명령 앞에 ALLOW_VISIBLE_WINDOW=1\n"


def _opens_window(line: str) -> bool:
    if _RE_COMMENT.search(line):
        return False
    if _RE_START.search(line) and not _RE_HIDDEN_START.search(line) and _RE_PROG.search(line):
        return True
    if _RE_CMDK.search(line):
        return True
    if _RE_SP.search(line) and not _RE_SP_HIDDEN.search(line):
        return True
    return False


def _extract_cmd(inp: str) -> str:
    tag = '"command":'
    i = inp.find(tag)
    cmd = inp[i + len(tag):] if i >= 0 else inp
    if cmd.startswith('"'):
        cmd = cmd[1:]
    if cmd.startswith(' "'):
        cmd = cmd[2:]
    for sep in ('", "', '","', '"}'):
        j = cmd.find(sep)
        if j >= 0:
            cmd = cmd[:j]
    cmd = cmd.replace("\\\\", "\\")   # JSON 의 \\ -> \
    cmd = cmd.replace('\\"', '"')    # JSON 의 \" -> "
    return cmd


def _is_posix_abs(p: str) -> bool:
    return p.startswith("/")


def run(ctx):
    inp = bash_read(ctx.raw)
    if not any(g in inp for g in _GATE):
        return None
    if "ALLOW_VISIBLE_WINDOW=1" in inp:
        return None
    cmd = _extract_cmd(inp)
    reason = ""
    if _opens_window(cmd):
        reason = "명령이 보이는 창을 연다: " + cmd[:120]
    if not reason:
        base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        m = _RE_CDQ.search(cmd)
        if m:
            base = m.group(1)
        else:
            m = _RE_CD.search(cmd)
            if m:
                base = m.group(1)
        rest = cmd
        while True:
            m = _RE_FILE.search(rest)
            if not m:
                break
            f = m.group(0)
            k = rest.find(f)
            rest = rest[k + len(f):] if k >= 0 else ""
            f = f.replace("\\", "/")
            if re.match(r"[A-Za-z]:/", f):
                p = f
            elif f.startswith("/"):
                return Spawn(REL)            # msys 절대경로 - 원본에 위임
            else:
                if _is_posix_abs(base):
                    return Spawn(REL)        # cd /c/... 형태 - 원본에 위임
                p = base + "/" + f
            if not os.path.isfile(p):
                continue
            try:
                with open(p, "rb") as fh:
                    data = fh.read().decode("utf-8", "surrogateescape")
            except OSError:
                continue
            lines = data.split("\n")
            if lines and lines[-1] == "":
                lines.pop()
            for n, line in enumerate(lines, 1):
                if line.endswith("\r"):
                    line = line[:-1]
                if _opens_window(line):
                    reason = "%s:%d 이 보이는 창을 연다 → %s" % (f[f.rfind("/") + 1:], n, line[:100])
                    break
            if reason:
                break
    if reason:
        return Result(2, "", MSG_1 % reason + MSG_2 + MSG_3 + MSG_4)
    return None
