"""block-visible-windows.sh 이식 (e39d316 판) - 세션이 보이는 창(CMD·PowerShell·서버 콘솔)을 띄우기 전에 차단 (exit 2).

판정: (1) 명령 자체가 창을 연다 (start /b·/min 없이 · cmd /k · Start-Process -WindowStyle Hidden·-NoNewWindow 없이)
      (2) 명령이 실행하는 .bat/.cmd/.ps1 파일 안에 (1) 이 있다 (cd "DIR" 의 DIR 기준으로 상대 경로 해석)
우회: 명령에 ALLOW_VISIBLE_WINDOW=1.
원본의 bash [[ =~ ]] 는 nocasematch + POSIX ERE ([[:space:]]) 이다 - 같은 의미의 python 정규식으로 옮겼다.
판정의 정본은 이 파일 하나다 — .sh 는 이것을 부르는 껍데기(2026-10-25 사이클 881: 두 벌이 어긋나 637 처럼 한쪽만 고쳐지던 것).
  /c/... 는 직접 C:/... 로, /tmp 같은 다른 POSIX 경로는 cygpath 로 푼다.
읽기만 하는 명령(grep·sed·cat·git …)으로 시작하는 조각은 판정에서 뺀다 — 인자·heredoc 글은 실행되지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import subprocess

from _common import Result, bash_read
_S = r"[ \t\n\r\f\v]"
_I = re.I
_RE_COMMENT = re.compile(r"^" + _S + r"*(rem" + _S + r"|::|#)", _I)
_RE_START = re.compile(r"(^|[ \t\n\r\f\v&|(])start" + _S, _I)
# `npm run start`·`next start`·`yarn start` 는 cmd 의 start 가 아니라 하위 명령이다
#   (2026-10-17: start-3000.bat:63 의 Hidden 줄을 이것 때문에 막아 3000 재기동이 막혔다)
_RE_SUBCMD_START = re.compile(r"\b(run|next|npm|yarn|pnpm)" + _S + r"+start\b", _I)
_RE_HIDDEN_START = re.compile(_S + r"/(b|min)(" + _S + r"|\Z)", _I)
_RE_PROG = re.compile(r'(cmd|powershell|pwsh|python|py' + _S + r'|\.exe|\.bat|\.cmd|%PY%|"%)', _I)
_RE_CMDK = re.compile(r"cmd(\.exe)?" + _S + r"+//?k(" + _S + r"|\Z)", _I)
# 2026-10-26 외부 AI 지적: cmd //c "start ..." Git Bash 패턴 추가 감지
_RE_CMDC_START = re.compile(r"cmd(\.exe)?" + _S + r"+//?c" + _S + r"+[\"']?start" + _S, _I)
_RE_SP = re.compile(r"Start-Process", _I)
_RE_SP_HIDDEN = re.compile(r"(-WindowStyle" + _S + r"+Hidden|-NoNewWindow)", _I)
_RE_CDQ = re.compile(r'cd' + _S + r'+"([^"]+)"', _I)
_RE_CD = re.compile(r"cd" + _S + r"+([^ \t\n\r\f\v&;]+)", _I)
_RE_FILE = re.compile(r"([A-Za-z]:[\\/][^\"' \t\n\r\f\v]*|[^\"' \t\n\r\f\v]*)\.(bat|cmd|ps1)", _I)

_GATE = ("start", "START", "Start", "cmd /k", "cmd //k", "cmd /c", "cmd //c", ".bat", ".BAT", ".cmd", ".ps1")

# 읽기만 하는 명령 — 인자는 글·파일 경로일 뿐 실행되지 않는다. 이 명령으로 시작하는 조각은 판정에서 뺀다.
#   (2026-10-25 사이클 881: `grep -n taskkill memcheck.ps1` · `grep "Start-Process\|start " x.ps1` ·
#    `git commit -F - <<EOF … start cmd …` 처럼 인자·heredoc 글에 든 낱말·파일까지 '실행' 으로 보고 막았다)
#   find(-exec)·xargs·bash·python 은 남을 실행하므로 넣지 않는다.
_READERS = frozenset((
    "grep", "egrep", "fgrep", "rg", "sed", "awk", "gawk", "cat", "head", "tail", "less", "more", "wc",
    "diff", "cmp", "md5sum", "sha1sum", "sha256sum", "file", "ls", "stat", "echo", "printf", "git",
    "sort", "uniq", "cut", "tr", "iconv", "od", "xxd", "strings", "basename", "dirname", "realpath",
    "readlink", "test", "[", "cygpath",
))
_PREFIX_WORDS = frozenset(("env", "time", "nohup", "command", "builtin", "exec"))
_RE_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_RE_HEREDOC = re.compile(r"(?<!<)<<(?!<)-?[ \t]*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
_RE_MSYS_DRIVE = re.compile(r"^/([A-Za-z])(/|$)")


def _segments(cmd: str) -> list:
    """명령을 실행 단위 조각으로 — 따옴표 밖의 && || ; | & 줄바꿈에서 자른다. heredoc 본문은 그 조각에 붙인다."""
    segs, cur, q, i, n = [], [], None, 0, len(cmd)
    line_start = 0   # cur 안에서 지금 줄이 시작된 위치

    def flush():
        s = "".join(cur)
        if s.strip():
            segs.append(s)
        cur.clear()

    while i < n:
        c = cmd[i]
        if q:
            cur.append(c)
            if c == q:
                q = None
            elif c == "\\" and q == '"' and i + 1 < n:
                cur.append(cmd[i + 1])
                i += 1
            i += 1
            continue
        if c in "'\"":
            q = c
            cur.append(c)
            i += 1
            continue
        if c == "\\" and i + 1 < n:
            cur.append(c)
            cur.append(cmd[i + 1])
            i += 2
            continue
        if c == "\n":
            m = _RE_HEREDOC.search("".join(cur[line_start:]))
            if m:
                delim = m.group(1)
                j = i + 1
                while j <= n:
                    k = cmd.find("\n", j)
                    k = n if k < 0 else k
                    body_line = cmd[j:k]
                    cur.append("\n" + body_line)
                    j = k + 1
                    if body_line.strip() == delim:
                        break
                i = j
                flush()
                line_start = 0
                continue
            flush()
            line_start = 0
            i += 1
            continue
        if c in ";|&":
            flush()
            line_start = 0
            i += 2 if (c in "|&" and i + 1 < n and cmd[i + 1] == c) else 1
            continue
        cur.append(c)
        i += 1
    flush()
    return segs


def _is_reader(seg: str) -> bool:
    for w in seg.split():
        w = w.lstrip("({!")
        if not w or _RE_ASSIGN.match(w) or w in _PREFIX_WORDS:
            continue
        w = w.strip("'\"").replace("\\", "/").rsplit("/", 1)[-1].lower()
        if w.endswith(".exe"):
            w = w[:-4]
        return w in _READERS
    return True   # 빈 조각


def _msys_to_win(p: str) -> str:
    """/c/work/x → C:/work/x (Git Bash 드라이브 표기). 다른 POSIX 경로는 그대로."""
    m = _RE_MSYS_DRIVE.match(p)
    return (m.group(1).upper() + ":/" + p[m.end():]) if m else p

MSG_1 = "BLOCKED(창 예방): %s\n"
MSG_2 = ("  → 테스트·검증은 창 없이: run_in_background 로 직접 실행 (예: python run.py …) · 프로젝트에 숨김 모드가 있으면 그것 "
         "· start 를 쓰면 /b\n")
MSG_3 = "  → 테스트로 띄운 프로세스는 끝나면 닫는다 (원래 떠 있던 서버는 원래 방식으로 되돌린다).\n"
MSG_4 = "  → 사용자가 창을 원하면 명령 앞에 ALLOW_VISIBLE_WINDOW=1\n"


def _opens_window(line: str) -> bool:
    if _RE_COMMENT.search(line):
        return False
    bare = _RE_SUBCMD_START.sub(" ", line)
    if _RE_START.search(bare) and not _RE_HIDDEN_START.search(bare) and _RE_PROG.search(bare):
        return True
    if _RE_CMDK.search(line):
        return True
    # 2026-10-26: cmd //c "start ..." Git Bash 패턴 (/b·/min 없이)
    if _RE_CMDC_START.search(line) and not _RE_HIDDEN_START.search(line):
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


def _posix_to_win(p: str) -> str:
    """/tmp/x 같은 Git Bash 경로 → Windows 경로 (cygpath · 드물다). 못 풀면 빈 문자열."""
    try:
        r = subprocess.run(["cygpath", "-m", p], capture_output=True, timeout=5)
        return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _run_inner(ctx):
    inp = bash_read(ctx.raw)
    if not any(g in inp for g in _GATE):
        return None
    if "ALLOW_VISIBLE_WINDOW=1" in inp:
        return None
    try:   # 줄바꿈(\n)·따옴표가 제대로 풀려야 조각을 나눌 수 있다 — 옛 글자 치환은 실패할 때만
        cmd = json.loads(ctx.raw)["tool_input"]["command"]
        if not isinstance(cmd, str):
            raise TypeError
    except Exception:
        cmd = _extract_cmd(inp)
    run_segs = [s for s in _segments(cmd) if not _is_reader(s)]
    if not run_segs:
        return None
    reason = ""
    for s in run_segs:
        if _opens_window(s):
            reason = "명령이 보이는 창을 연다: " + s.strip()[:120]
            break
    if not reason:
        base = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        m = _RE_CDQ.search(cmd)
        if m:
            base = m.group(1)
        else:
            m = _RE_CD.search(cmd)
            if m:
                base = m.group(1)
        base = _msys_to_win(base.replace("\\", "/"))
        rest = "\n".join(run_segs)
        while True:
            m = _RE_FILE.search(rest)
            if not m:
                break
            f = m.group(0)
            k = rest.find(f)
            rest = rest[k + len(f):] if k >= 0 else ""
            f = _msys_to_win(f.replace("\\", "/"))
            if re.match(r"[A-Za-z]:/", f):
                p = f
            elif f.startswith("/"):
                p = _posix_to_win(f)
            else:
                p = (_posix_to_win(base) if _is_posix_abs(base) else base) + "/" + f
            if not p:
                continue
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
            # 줄 잇기(ps1 끝 ` · bat 끝 ^)는 한 명령으로 붙여 본다 — memcheck.ps1:31 의 Start-Process 는
            #   -WindowStyle Hidden 이 33줄에 있는데 31줄만 보고 막았다 (사이클 881)
            cont = "`" if f.lower().endswith(".ps1") else "^"
            logical, buf, buf_n = [], "", 0
            for n, line in enumerate(lines, 1):
                if line.endswith("\r"):
                    line = line[:-1]
                if not buf:
                    buf_n = n
                if line.rstrip().endswith(cont):
                    buf += line.rstrip()[:-1] + " "
                    continue
                logical.append((buf_n, buf + line))
                buf = ""
            if buf:
                logical.append((buf_n, buf))
            for n, line in logical:
                if _opens_window(line):
                    reason = "%s:%d 이 보이는 창을 연다 → %s" % (f[f.rfind("/") + 1:], n, line[:100])
                    break
            if reason:
                break
    if reason:
        return Result(2, "", MSG_1 % reason + MSG_2 + MSG_3 + MSG_4)
    return None


def run(ctx):
    """2026-10-26 외부 AI 지적: fail-closed 정책 적용.
    hook 자체 exception 시 → GATE 매치한 명령만 BLOCK (안전 쪽 default)."""
    try:
        return _run_inner(ctx)
    except Exception as e:  # noqa: BLE001
        # fail-closed: GATE 매치 명령에서 hook 오류 발생 시 BLOCK (위험 쪽 default)
        try:
            inp = bash_read(ctx.raw)
            if any(g in inp for g in _GATE) and "ALLOW_VISIBLE_WINDOW=1" not in inp:
                return Result(2, "",
                    "BLOCKED(창 예방 · fail-closed): hook 검사 중 오류 발생 — 안전상 차단\n"
                    f"  → err: {type(e).__name__}: {str(e)[:120]}\n"
                    "  → 확실히 안전하면 ALLOW_VISIBLE_WINDOW=1 로 bypass\n")
        except Exception:
            pass
        return None  # non-GATE 명령은 통과 (평상 동작 유지)

if __name__ == "__main__":   # block-visible-windows.sh 껍데기가 부른다 (stdin = 훅 페이로드)
    import sys
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    class _Ctx:
        def __init__(self, raw):
            self.raw = raw

    res = run(_Ctx(sys.stdin.read()))
    if res is not None:
        sys.stderr.write(res.err)
        sys.exit(res.rc)
    sys.exit(0)
