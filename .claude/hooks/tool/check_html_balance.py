"""check-html-balance.sh 이식 - html/htm 편집 후 <script> 중괄호·괄호 균형 + HTML 태그 균형 검사 (systemMessage · 비차단).

원본은 awk · grep · tr · wc 파이프를 태그 17개 x 2 만큼 돌려 (프로세스 100개 이상) 이 PC 에서 단독 101초가 걸렸다.
settings timeout 5초에 늘 끊겨 한 번도 결과를 내지 못했다. 순수 문자열 처리라 같은 판정 로직을 그대로 in-process 로 옮겼다
(지금까지 타임아웃으로 안 나오던 경고가 실제로 나온다 - 비차단 안내일 뿐이다).
"""
from __future__ import annotations

import os
import re

from _common import Result, Spawn, bash_basename, bash_cat, glob_any, grep_key_value_a, has_jq

REL = ".claude/hooks/check-html-balance.sh"
_START = re.compile(r"<script[^>]*>")
_END = re.compile(r"</script>")
_TAGS = ("div", "span", "p", "ul", "ol", "li", "table", "tr", "td", "th", "tbody", "thead", "nav", "header",
         "footer", "section", "article", "main", "aside", "form")


def run(ctx):
    if has_jq():
        return Spawn(REL)
    fp = grep_key_value_a(bash_cat(ctx.raw), "file_path")
    if not os.path.isfile(fp):
        return None
    if not glob_any(fp, "*.html", "*.htm"):
        return None
    try:
        with open(fp, "rb") as f:
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    # awk '/<script[^>]*>/,/<\/script>/' | grep -v '<script\|</script>'
    script_lines = []
    in_range = False
    for line in lines:
        emit = False
        if not in_range:
            if _START.search(line):
                in_range = True
                emit = True
                if _END.search(line):
                    in_range = False
        else:
            emit = True
            if _END.search(line):
                in_range = False
        if emit and "<script" not in line and "</script>" not in line:
            script_lines.append(line)
    script = "\n".join(script_lines)

    ob, cb = script.count("{"), script.count("}")
    op, cp = script.count("("), script.count(")")
    warn = ""
    if ob != cb:
        warn += "\\n  - <script> brace 불균형: { %d / } %d" % (ob, cb)
    if op != cp:
        warn += "\\n  - <script> paren 불균형: ( %d / ) %d" % (op, cp)

    # grep -v '<script\|</script>\|<style\|</style>'
    body = "\n".join(ln for ln in lines
                     if "<script" not in ln and "</script>" not in ln and "<style" not in ln and "</style>" not in ln)
    for tag in _TAGS:
        opened = len(re.findall("<%s[ >/]" % tag, body))
        closed = len(re.findall("</%s>" % tag, body))
        diff = opened - closed
        if diff > 2 or diff < -2:
            warn += "\\n  - <%s> 불균형: 열린 %d / 닫은 %d" % (tag, opened, closed)
    if warn:
        base = bash_basename(fp)
        return Result(0, '{"systemMessage": "[html-balance] %s — tag/brace 불균형 의심:%s\\n수동 검토 권장."}\n' % (base, warn), "")
    return None
