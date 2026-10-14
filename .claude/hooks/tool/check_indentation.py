"""check-indentation.sh 이식 - md/json/yaml/sh 편집 후 탭/스페이스 혼용 경고 (systemMessage · 비차단).

원본의 fallback sed 는 콜론 바로 뒤 따옴표(공백 없는 JSON) 일 때만 값을 뽑는다 - 그대로 재현한다.
원본의 grep -c ... || echo 0 은 매치 0건일 때 두 줄(0 과 0) 이 되어 [ ] 정수 비교 오류(stderr) 를 낸다 - 이것도 재현한다.
"""
from __future__ import annotations

import os
import re

from _common import Result, Spawn, bash_basename, bash_cat, glob_any, grep_o_first, has_jq

REL = ".claude/hooks/check-indentation.sh"
_SED = re.compile(r'.*:"(.*)"')
_IF_LINE = 28  # check-indentation.sh 의 `if [ "$TAB_LINES" -ge 1 ] && ...` 줄 번호


def run(ctx):
    if has_jq():
        return Spawn(REL)
    m = grep_o_first(bash_cat(ctx.raw), r'"file_path"\s*:\s*"[^"]*"')
    fp = ""
    if m is not None:
        mm = _SED.match(m)
        fp = mm.group(1) if mm else m
    if not os.path.isfile(fp):
        return None
    if not glob_any(fp, "*.md", "*.json", "*.yaml", "*.yml", "*.sh"):
        return None
    try:
        with open(fp, "rb") as f:
            data = f.read()
    except OSError:
        return None
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    tab = sum(1 for ln in lines if ln.startswith(b"\t"))
    sp = sum(1 for ln in lines if ln.startswith(b"  "))
    script = ctx.project_dir + "/.claude/hooks/check-indentation.sh"

    def _bad(val):
        return f"{script}: line {_IF_LINE}: [: {val}: integer expression expected\n"

    # grep -c 가 0 이면 "0"(grep) + "0"(echo) 두 줄이 된다
    if tab == 0:
        return Result(0, "", _bad("0\n0"))
    if sp == 0:
        return Result(0, "", _bad("0\n0"))
    base = bash_basename(fp)
    out = ('{"systemMessage": "[indent-check] %s — 탭 %d줄 + 스페이스 %d줄 혼용 (indentation rule 위반). '
           '`sed -i \'s/\\\\t/  /g\'` 권장."}\n') % (base, tab, sp)
    return Result(0, out, "")
