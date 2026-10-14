"""check-hardcoded-paths.sh 이식 — 코드/설정 파일 편집에 하드 경로(사용자명·Python 버전·호스트명) 감지 시 systemMessage (비차단)."""
from __future__ import annotations

import re

from _common import Result, Spawn, bash_basename, bash_cat, glob_any, grep_key_value_a, has_jq

REL = ".claude/hooks/check-hardcoded-paths.sh"

_P1 = re.compile(r"C:[\\/]+[Uu]sers[\\/]+[a-z][a-z0-9_]+")
_P2 = re.compile(r"/home/[a-z][a-z0-9_]+")
_P3 = re.compile(r"Python3[0-9]{2}")
_P4 = re.compile(r"DESKTOP-[A-Z0-9]{5,}")


def _first(rx, text):
    for line in text.split("\n"):
        m = rx.search(line)
        if m:
            return m.group(0)
    return None


def _has(rx, text):
    return any(rx.search(line) for line in text.split("\n"))


def run(ctx):
    if has_jq():
        return Spawn(REL)
    inp = bash_cat(ctx.raw)
    fp = grep_key_value_a(inp, "file_path")
    if not glob_any(fp, "*.py", "*.sh", "*.bat", "*.ps1", "*.js", "*.ts", "*.json", "*.toml", "*.yaml",
                    "*.yml", "*.ini", "*.cfg", "*.conf"):
        return None
    if glob_any(fp, "*.claude/rules/*", "*docs/*", "*examples/*", "*.example*", "*setup/templates/*"):
        return None
    content = inp
    if not content or content == "null":
        return None
    # 원본 viol 문자열은 "\n" 두 글자(역슬래시 + n) 를 그대로 JSON 에 싣는다
    viol = ""
    if _has(_P1, content):
        viol += "\\n  - 사용자명: %s -> %%USERPROFILE%% / Path.home()" % _first(_P1, content)
    if _has(_P2, content):
        viol += "\\n  - Linux 사용자: %s -> $HOME / Path.home()" % _first(_P2, content)
    if _has(_P3, content):
        viol += "\\n  - Python 버전: %s -> where python / shutil.which('python')" % _first(_P3, content)
    if _has(_P4, content):
        viol += "\\n  - 호스트명: %s -> %%COMPUTERNAME%% / socket.gethostname()" % _first(_P4, content)
    if viol:
        base = bash_basename(fp)
        out = ('{"systemMessage": "[hardcoded-path] %s — best-practices §하드 경로 금지 위반 후보:%s\\n'
               '동적 검색으로 교체 권장."}\n') % (base, viol)
        return Result(0, out, "")
    return None
