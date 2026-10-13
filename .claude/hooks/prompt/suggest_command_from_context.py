"""suggest-command-from-context.sh ?댁떇 ??理쒓렐 10 turn ?⑦꽩쨌?꾧퀎 珥덇낵쨌?ъ궗???닿껐梨끒룹쇅遺 ?좏샇 湲곕컲 command 異붿쿇.

濡쒖쭅? .claude/scripts/suggest-command-from-context.py (5遺?TTL 罹먯떆) 瑜?in-process 濡??몄텧?쒕떎.
洹??ㅽ겕由쏀듃媛 print ?섎뜕 JSON 留?媛濡쒖콈 additionalContext 瑜?爰쇰궦??(紐⑤뱢 ?꾩뿭 print 援먯껜 ???꾩뿭 stdout ? 嫄대뱶由ъ? ?딆쓬).
罹먯떆 留뚮즺 ???ㅽ겕由쏀듃 ?대??먯꽌 git status 瑜?1??遺瑜몃떎 (5遺꾩뿉 理쒕? 1??쨌 ?먮낯 ?숈씪).
"""
from __future__ import annotations

import json

from _common import load_script


def run(ctx):
    if not ctx.has_plugins():
        return None
    mod = load_script("suggest-command-from-context")
    if mod is None:
        return None
    buf: list[str] = []
    mod.print = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    try:
        mod.main()
    finally:
        del mod.print
    if not buf:
        return None
    text = "\n".join(buf)
    try:
        return json.loads(text)["hookSpecificOutput"]["additionalContext"]
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return text + "\n"

