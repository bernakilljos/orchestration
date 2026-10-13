"""save-user-prompt.sh ?댁떇 ???ъ슜???꾨＼?꾪듃瑜?orca.db.conversations ?????(異쒕젰 ?놁쓬).

?먮낯???먮윭 異쒕젰(stderr)? .claude/logs/conversation-save.log 濡?媛붾떎 ??洹몃?濡??좎?.
"""
from __future__ import annotations

import os

from _common import append_text, load_script


def run(ctx):
    root = ctx.root
    log = root / ".claude" / "logs" / "conversation-save.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():  # ?먮낯??`>>"$LOG"` ??異쒕젰???놁뼱???뚯씪??留뚮뱺??        log.touch()

    if ctx.parse_error:
        append_text(log, "[parse error] %s\n" % ctx.parse_error)
        return None
    # 2026-09-19: ?몄뀡 id ????stdin ??session_id 媛 ?뺣낯 ???? 媛숈? ?꾨줈?몄뒪???ㅻⅨ ?낆뿉 ?덉? ?딄쾶 ????숈븞留??ㅼ젙
    sid = ctx.payload.get("session_id")
    prev = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        os.environ["CLAUDE_CODE_SESSION_ID"] = sid
    try:
        p = ctx.field("user_prompt", "prompt")
        if not p:
            return None
        CL = load_script("lib/conversation_logger")
        CL.save_turn("user", p)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        append_text(log, "[save error] %s\n" % e)
    finally:
        if sid:
            if prev is None:
                os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            else:
                os.environ["CLAUDE_CODE_SESSION_ID"] = prev
    return None

