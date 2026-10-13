#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sync-assistant-from-jsonl - Claude Code jsonl ?먯꽌 assistant ?묐떟 ??orca.db.conversations.

諛곌꼍: Claude Code ??assistant ?묐떟??hook ???놁쓬. Stop hook ??jsonl ?뚯떛??sync.
洹쇨굅: ?ъ슜??吏??(2026-09-03) - assistant ?대젰 ?좎떎.
"""
from __future__ import annotations
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass


def main() -> int:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    home = os.path.expanduser("~")
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    proj_dir = os.path.join(home, ".claude", "projects", safe)
    if not os.path.isdir(proj_dir):
        print(f"[skip] proj_dir not found: {proj_dir}")
        return 0
    db = os.path.join(cwd, ".claude", "state", "orca.db")
    if not os.path.exists(db):
        print(f"[skip] db not found: {db}")
        return 0
    c = sqlite3.connect(db)
    # ?대? ??λ맂 content_hash (以묐났 諛⑹?)
    existing = set(
        r[0] for r in c.execute(
            "SELECT content_hash FROM conversations WHERE role IN ('assistant','user') "
            "AND content_hash IS NOT NULL"
        ).fetchall()
    )
    added = 0
    # 理쒓렐 5 jsonl 留?sync (遺???덇컧)
    # ??stdin ??以 ?대쾲 ?몄뀡 transcript 留?sync. ?놁쓣 ?뚮쭔 理쒓렐 5 jsonl (2026-09-19: 306MB ???뚯씪??留?Stop 留덈떎 ?쎌뿀??
    own = os.environ.get("CLAUDE_TRANSCRIPT_PATH", "")
    if own and os.path.isfile(own):
        files = [own]
    else:
        files = sorted(
            glob.glob(os.path.join(proj_dir, "*.jsonl")),
            key=os.path.getmtime, reverse=True
        )[:5]
    for jp in files:
        sid = os.path.splitext(os.path.basename(jp))[0]
        try:
            with open(jp, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                        continue
                    rtype = rec.get("type")
                    if rtype not in ("assistant", "user"):
                        continue
                    msg = rec.get("message") or {}
                    cp = msg.get("content") or []
                    if isinstance(cp, list):
                        parts = []
                        for p in cp:
                            if isinstance(p, dict):
                                t = p.get("text") or ""
                                if t:
                                    parts.append(t)
                            elif isinstance(p, str):
                                parts.append(p)
                        text = " ".join(parts)
                    elif isinstance(cp, str):
                        text = cp
                    else:
                        text = ""
                    text = (text or "").strip()[:8000]
                    if not text:
                        continue
                    ch = hashlib.sha256(
                        text.encode("utf-8", errors="replace")
                    ).hexdigest()[:16]
                    if ch in existing:
                        continue
                    existing.add(ch)
                    turn = c.execute(
                        "SELECT COALESCE(MAX(turn),0)+1 FROM conversations WHERE session_id=?",
                        (sid,)
                    ).fetchone()[0] or 1
                    # ?끸쁾??002 ??`ts` 瑜?**jsonl ???ㅼ젣 ????쒓컖**?쇰줈 ?ｋ뒗??
                    #   醫낆쟾??`ts` 瑜???二쇱뼱 `DEFAULT CURRENT_TIMESTAMP`(=?곸옱 ?쒓컖)媛
                    #   ?ㅼ뼱媛붾떎. 洹몃옒??**怨쇨굅 ?몄뀡 ?꾨?媛 ?뚯삤?섅띾줈 李랁삍??* ??                    #   ?ㅼ륫 1002: ?몄뀡 5媛쒓? ?꾨? `07:55:47` ???쒓컖?댁뿀怨?9/30 ?몄뀡 ?ы븿),
                    #   7?셋?0?셋?0??李쎌씠 **媛숈? 404嫄?*???먮떎.
                    #   ?끸쁾洹?寃곌낵 statusline ??**?щ컻瑜좎씠 援ъ“?곸쑝濡?100%** ???                    #     (?곗떇 = 7??첨 30??. ?뚰빆???щ컻?쒕떎?띻? ?꾨땲??                    #     **?뚮퉬援먰븷 怨쇨굅媛 ?녿떎??*?????遺꾨え媛 遺꾩옄? 媛숈? 吏묓빀?대떎.
                    #   ?꾿10: ??李쎌씠 媛숈? ?먮줈 ??媛믪씠硫?鍮꾧탳媛 ?듭씠 ?꾨땲???뚯쓬?대떎.
                    _ts = (rec.get("timestamp") or "").strip()
                    if _ts:
                        # "2026-09-30T00:22:04.982Z" ??"2026-09-30 00:22:04"
                        _ts = _ts.replace("T", " ").replace("Z", "").split(".")[0]
                    if _ts:
                        c.execute(
                            "INSERT INTO conversations"
                            "(session_id,turn,role,content,content_hash,tokens,ts) "
                            "VALUES(?,?,?,?,?,?,?)",
                            (sid, turn, rtype, text, ch, len(text) // 4, _ts)
                        )
                    else:
                        # ?낆떆媛곸씠 ?놁쑝硫?**吏?대궡吏 ?딅뒗??* ??湲곕낯媛??곸옱 ?쒓컖)??留↔린怨?                        #   洹??ъ떎??吏묎퀎?먯꽌 짬?ㅻ뒛쨩濡?蹂댁씠??寃껋? 媛먯닔?쒕떎(A8).
                        c.execute(
                            "INSERT INTO conversations"
                            "(session_id,turn,role,content,content_hash,tokens) "
                            "VALUES(?,?,?,?,?,?)",
                            (sid, turn, rtype, text, ch, len(text) // 4)
                        )
                    added += 1
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[skip jsonl] {jp}: {e}", file=sys.stderr)
    c.commit()
    print(f"[ok] jsonl sync - added {added}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[err] {e}", file=sys.stderr)
        sys.exit(0)

