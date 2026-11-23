"""block_dangerous_bash.py 이식 — 파괴적 Bash 명령 deny (permissionDecision: deny JSON · exit 0).

stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - _common.py 의 PY_STDIN_FIX 설명 참고.
원본은 deny JSON 을 stdout(시스템 기본 인코딩 · strict) 으로 쓰다가 명령에 깨진 글자가 섞이면 UnicodeEncodeError 로
죽는다 (exit 1 · deny 미전달). 같은 결과를 재현한다.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import sys

from _common import Result, py_child_encoding, py_stdin_text

UNIVERSAL = [r"\bdd\s+if=", r"\bshutdown\b", r"\breboot\b", r"\bpoweroff\b"]
UNIX_LIKE = [r"\brm\s+-rf\b", r"\brm\s+-fr\b", r"\brm\s+-r\s+-f\b", r"\bmkfs\."]
WINDOWS = [r"\bdel\s+/s\s+/q\b", r"\brmdir\s+/s\s+/q\b", r"\bformat\s+[a-zA-Z]:\b",
           r"\bRemove-Item\b.*\s-Recurse\b.*\s-Force\b"]

# 2026-11-05 PowerShell 어휘 — Remove-Item 별칭 6종·-Recurse 축약·파이프 삭제 (Microsoft Remove-Item 문서)
_RM = r"(?:Remove-Item|ri|rm|rmdir|rd|del|erase)"
_CMD_POS = r"(?:^|[;|&({\n'\"]\s*)(?:&\s*)?"
POWERSHELL = [
    _CMD_POS + _RM + r"\b[^;|\n]*\s-r[a-z]*\b",
    r"\s-r[a-z]*\b[^;\n]*\|\s*(?:(?:%|ForEach-Object)\s*\{\s*)?" + _RM + r"\b",
    r"\[(?:System\.)?IO\.Directory\]::Delete\(",
    r"\brd\s+/s\b",
    r"\b(?:Format-Volume|Clear-Disk|Remove-Partition|Initialize-Disk|Stop-Computer|Restart-Computer)\b",
]
_PS_HOST = re.compile(r"\b(?:powershell|pwsh)(?:\.exe)?\b", re.I)
# -ExecutionPolicy(-ex·-ep) 와 구분 · 값은 UTF-16LE Base64 (about_Pwsh · about_PowerShell_exe)
_PS_ENCODED = re.compile(r"\b(?:powershell|pwsh)(?:\.exe)?\b[^;|\n]*?\s[-/]e(?:c|n[a-z]*)?\s+['\"]?([^\s'\"]+)", re.I)
# 문자열을 코드로 실행하는 경로 — 이때는 따옴표 안도 검사한다
_INDIRECT = re.compile(r"\b(?:iex|Invoke-Expression|Invoke-Command|icm|Start-Process|saps|powershell|pwsh|cmd|bash|sh)\b"
                       r"|\[scriptblock\]::Create", re.I)

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


def _ps_danger(cmd: str, depth: int = 0) -> bool:
    """PowerShell 명령 판정 — 별칭·축약·백틱·인코딩·간접 실행까지. 문자열 조립 등 정적 분석 밖은 잡지 못한다."""
    text = re.sub(r"`(?=[A-Za-z-])", "", cmd)
    patterns = _patterns() + POWERSHELL
    targets = [_strip_quoted(text)] + ([text] if _INDIRECT.search(text) else [])
    if any(re.search(p, t, re.I) for p in patterns for t in targets):
        return True
    if depth < 3:
        for m in _PS_ENCODED.finditer(text):
            try:
                decoded = base64.b64decode(m.group(1), validate=True).decode("utf-16-le")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                return True     # 해독 불가 인코딩 명령 = 내용 확인 불가 → 차단
            if _ps_danger(decoded, depth + 1):
                return True
    return False


# R370 (2026-11-23): C:\Windows\System32\powershell (확장자 없는 0바이트 · 2026-04-08 생성 · 생성 주체 UNKNOWN) 같은
#   «시스템 폴더에 생긴 잔여 파일» 재발 방지 — 작업 폴더가 Windows 폴더이거나 대상이 Windows 폴더인 출력 리디렉션·파일 쓰기를
#   실행 전에 막는다. 읽기·실행·버림(>nul·$null·/dev/null·&1)은 그대로 통과 (정상 시스템 명령 차단 X).
_SYSROOT = (__import__("os").environ.get("SystemRoot") or r"C:\Windows").replace("/", "\\").rstrip("\\").lower()
_CD = re.compile(r"(?:^|[;&|]\s*)(?:cd|chdir|Set-Location|sl|pushd)\s+(?:/d\s+)?['\"]?([^'\";&|\s]+)", re.I)
_REDIR = re.compile(r"(?<![<>&\w-])(?:[12*]?>>?)\s*['\"]?([^\s'\";|&)]+)")
_WRITE_CMD = re.compile(r"\b(?:Out-File|Set-Content|Add-Content|New-Item|Tee-Object)\b[^;|\n]*?(?:-(?:FilePath|Path|LiteralPath)\s+)?['\"]?([A-Za-z]:\\[^\s'\";|]+|[^\s'\";|-][^\s'\";|]*)", re.I)
_DISCARD = {"nul", "$null", "/dev/null", "null", "&1", "&2"}


def _norm_win(p: str) -> str:
    p = p.strip().strip("'\"")
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)               # Git Bash /c/Windows → C:\Windows
    if m:
        p = m.group(1) + ":\\" + m.group(2)
    p = re.sub(r"(?i)%SystemRoot%|%windir%|\$env:SystemRoot|\$env:windir|\$SYSTEMROOT|\$WINDIR", lambda _m: _SYSROOT, p)   # 치환 문자열의 \ 를 정규식 이스케이프로 읽지 않게
    return p.replace("/", "\\").lower()


def _in_sysroot(p: str) -> bool:
    p = _norm_win(p)
    return p == _SYSROOT or p.startswith(_SYSROOT + "\\")


def _system_dir_write(cmd: str, cwd: str) -> str | None:
    """작업 폴더(또는 명령 안 cd 대상)가 Windows 폴더인데 상대 경로로 쓰거나, 쓰기 대상이 Windows 폴더면 그 대상."""
    if sys.platform != "win32":
        return None
    eff = cwd or ""
    for m in _CD.finditer(cmd):
        eff = m.group(1)
    in_sys = bool(eff) and _in_sysroot(eff)
    targets = [m.group(1) for m in _REDIR.finditer(_strip_quoted(cmd))]   # 따옴표 안의 > (비교 연산자·문자열)는 리디렉션 아님
    targets += [m.group(1) for m in _WRITE_CMD.finditer(cmd)]
    for t in targets:
        tl = t.strip("'\"").lower()
        if not tl or tl in _DISCARD or tl.startswith("&"):
            continue
        absolute = bool(re.match(r"^(?:[a-z]:[\\/]|/[a-z]/|\\\\|%systemroot%|%windir%|\$env:)", tl))
        if absolute and _in_sysroot(t):
            return t
        if not absolute and in_sys:
            return t
    return None


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
    sysw = _system_dir_write(cmd, str(payload.get("cwd") or ""))
    if sysw:
        out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": "[BLOCK] Windows 시스템 폴더에 파일을 만드는 쓰기/리디렉션 차단 (R370 · 대상: %s) — "
                                                                  "작업 폴더를 프로젝트·임시 폴더로 바꾸거나 출력 경로를 절대 경로로 지정" % sysw[:120]}}
        return Result(0, json.dumps(out, ensure_ascii=False), "")
    target = _strip_quoted(cmd)
    is_ps = payload.get("tool_name") == "PowerShell" or _PS_HOST.search(cmd)
    for pat in _patterns():
        if (is_ps and _ps_danger(cmd)) or re.search(pat, target, re.IGNORECASE):
            out = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                          "permissionDecisionReason": "[BLOCK] 위험 명령 차단: %s" % cmd[:200]}}
            text = json.dumps(out, ensure_ascii=False)
            try:
                text.encode(py_child_encoding())     # 원본 sys.stdout.write 의 인코딩 실패 재현
            except UnicodeEncodeError as e:
                return Result(1, "", "UnicodeEncodeError: %s\n" % e)
            return Result(0, text, "")
    return None
