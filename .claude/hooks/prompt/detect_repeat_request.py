"""detect-repeat-request.sh ?댁떇 ??理쒓렐 ?꾨＼?꾪듃? ?ㅼ썙??3+ 寃뱀튂硫?/explainlikeim5 ?먮룞 ?몃━嫄?

?곹깭: .claude/state/prompt-history (理쒓렐 10以?쨌 300??以?
"""
from __future__ import annotations

import os
import re

from _common import append_text, bash_strip, head_bytes, is_loop_prompt, read_lines, write_text

MESSAGE = (
    "[以묐났 ?붿껌 媛먯? ???좎궗??@SCORE@ ?ㅼ썙??쨌 3?? 諛섎났]\n"
    "???먮룞 諛쒕룞: /explainlikeim5 (5???ㅒ룹씪??鍮꾩쑀쨌吏㏐쾶 ?ъ꽕紐?. ?ъ슜?먭? 紐??뚯븘?ㅼ뼱??諛섎났 以?= ?ㅻ챸 諛⑹떇 寃고븿.\n"
    "\n"
    "?????\n"
    "  1) 吏湲덇퉴吏 ??묒씠 遺議깊뻽?붿? ?몄젙\n"
    "  2) /explainlikeim5 ?ㅼ쑝濡??ъ꽕紐?(怨좉툒 ?⑹뼱 湲덉? 쨌 鍮꾩쑀 ?곗꽑)\n"
    "  3) /loop ?먮룞 諛쒕룞 寃??(諛섎났 ?묒뾽 ?먮룞??\n"
    "  4) 媛먯?-媛뺤젣 ?쒖뒪??(hook-rule-memory) ???볦튇 遺遺??ㅼ륫 ???깆옱\n"
    "  5) 留ㅻ쾲 媛숈? 吏??= ?쒖뒪??寃고븿 ?좏샇 (?ъ슜???몄? 遺??X)\n"
    "\n"
    "愿??猷? .claude/rules/user-emotion.md (3?? ??explainlikeim5)\n"
    "         .claude/rules/consistency.md 짠 湲곗? ?쇨???
)

_KW = re.compile(r"[媛-?즑-zA-Z][媛-?즑-zA-Z0-9_-]+")


def _kw(t: str) -> set:
    return set(_KW.findall(t))


def run(ctx):
    prompt = bash_strip(head_bytes(ctx.prompt_jq(), 500))
    if not prompt:
        return None
    if is_loop_prompt(prompt):  # /loop쨌諛곌꼍 ?뚮┝? 諛섎났 ?붿껌 ?ㅽ깘 諛⑹?
        return None

    hist = os.path.join(ctx.project_dir, ".claude", "state", "prompt-history")
    os.makedirs(os.path.dirname(hist), exist_ok=True)

    # 以꾨컮轅?-> 怨듬갚 쨌 ?곗냽 怨듬갚 1媛?쨌 300??    current = re.sub(" +", " ", prompt.replace("\n", " "))[:300]

    # ?좎궗?????ㅼ썙???곸쐞 10媛?vs 理쒓렐 5以?以?泥섏쓬 3媛? 寃뱀튇 以꾩쓽 寃뱀묠 ??    score = 0
    if os.path.isfile(hist):
        cur = set(sorted(_kw(current))[:10])
        try:
            with open(hist, encoding="utf-8", errors="replace") as f:
                past = f.read().splitlines()[-5:]
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            past = []
        for ln in past:
            n = len(cur & _kw(ln))
            if n >= 3:
                score = n
                break

    # ?덉뒪?좊━ 異붽? 쨌 理쒓렐 10以꾨쭔 ?좎?
    append_text(hist, current + "\n")
    lines = read_lines(hist)
    if len(lines) > 10:
        write_text(hist, "\n".join(lines[-10:]) + "\n")

    if score >= 3:
        return MESSAGE.replace("@SCORE@", str(score))
    return None

