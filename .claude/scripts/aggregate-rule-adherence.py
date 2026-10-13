#!/usr/bin/env python
"""
aggregate-rule-adherence.py ??猷??꾨컲 吏??吏묎퀎 (?붿옄?맞룰컻諛?

orca.db conversations ?ㅼ틪 ???ъ슜???ъ????⑦꽩 count ??.claude/state/rule-adherence.json ??? statusline ????JSON ?쎌쓬.

cache TTL 10遺?(留????ш퀎??X).
"""
from __future__ import annotations
import json, sqlite3, re, sys, os, time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

# Windows cp949 ?섍꼍?먯꽌 stdout쨌stderr UTF-8 媛뺤젣 (??cp949 ???諛⑹?)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
SESSIONS_DB = ROOT / ".claude" / "state" / "sessions.db"
OUT = ROOT / ".claude" / "state" / "rule-adherence.json"
TTL = 600  # 10遺?
# ?붿옄??猷??꾨컲 吏??(?ъ슜???ъ????댄쐶)
DESIGN_PATTERNS = {
    "?대え吏":          r'?대え吏|?대え?곗퐯|emoji',
    "?щ갚":            r'?щ갚|鍮?怨듦컙|鍮꾩뼱|諛뗫컠|諛뗫컠??,
    "踰꾩쟾愿由?:        r'-v2|-v3|_v2|_v3|final_final|踰꾩쟾\s*?묐?|v2\s*(留뚮뱾|?뚯씪)',
    "?곗텧臾쇨린??:      r'OVERDUE|?곗텧臾?*湲고븳|freshness|?ㅻ옒\s*???≪?',
}
# 媛쒕컻 猷??꾨컲 吏??DEV_PATTERNS = {
    "利앸챸吏??:        r'利앸챸???뺤씤??遊?寃利앺빐',
    "誘몃컲??:          r'??s*?섏뿀|??s*????s*?섏뼱???곸슜\s*???④낵\s*???묐룞\s*??諛섏쁺\s*??,
    "?꾩닔議곗궗skip":    r'?띾븸???異??λ궃|?쒕?濡?*???꾩닔議곗궗|??s*(蹂댁?|蹂댁떆)',
}

def count_in_window(rows, patterns, days):
    cutoff = datetime.now() - timedelta(days=days)
    cnt = Counter()
    for (ts, txt) in rows:
        if not txt: continue
        try:
            tsd = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if tsd.tzinfo:  # sessions.db ??UTC(Z) 쨌 濡쒖뺄 naive 濡?留욎떠 鍮꾧탳
                tsd = tsd.astimezone().replace(tzinfo=None)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            continue
        if tsd < cutoff: continue
        for k, pat in patterns.items():
            if re.search(pat, txt):
                cnt[k] += 1
    return dict(cnt)

def main():
    # TTL 泥댄겕
    if OUT.exists():
        age = time.time() - OUT.stat().st_mtime
        if age < TTL and os.environ.get("FORCE") != "1":
            return  # cache valid
    # ?뺣낯 = sessions.db prompts(source='typed') ??jsonl 利앸텇 ?곸옱?????몄뀡???덈떎.
    # orca.db.conversations ??save-user-prompt ?낆씠 ?볦튇 寃?留롮븘 (2026-10-02 ?ㅼ륫 12嫄?vs typed 133嫄?
    # ?꾨컲 0 ?쇰줈 蹂댁뿬 ?곹깭以?以꾩씠 ?듭㎏濡??⑥뿀?? ?놁쓣 ?뚮쭔 ?대갚.
    cutoff90 = (datetime.now() - timedelta(days=90)).isoformat()
    rows, source = [], ""
    try:
        if SESSIONS_DB.exists():
            c = sqlite3.connect(SESSIONS_DB)
            rows = c.execute(
                "SELECT ts, text FROM prompts WHERE source='typed' "
                "AND ts >= ? ORDER BY ts DESC LIMIT 5000", (cutoff90[:10],)
            ).fetchall()
            source = "sessions.db:prompts(typed)"
        if not rows and DB.exists():
            c = sqlite3.connect(DB)
            rows = c.execute(
                "SELECT ts, content FROM conversations WHERE role='user' "
                "AND ts >= ? ORDER BY ts DESC LIMIT 5000", (cutoff90,)
            ).fetchall()
            source = "orca.db:conversations"
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[ERR] {e}", file=sys.stderr); return
    if not source:
        return

    design_90 = count_in_window(rows, DESIGN_PATTERNS, 90)
    design_30 = count_in_window(rows, DESIGN_PATTERNS, 30)
    design_7  = count_in_window(rows, DESIGN_PATTERNS, 7)
    dev_90    = count_in_window(rows, DEV_PATTERNS, 90)
    dev_30    = count_in_window(rows, DEV_PATTERNS, 30)
    # 2026-10-06 ?ъ슜??吏?????대씪?꾠???0嫄???ぉ???곹깭以꾩뿉 蹂댁씠?꾨줉 ??移댄뀒怨좊━ ???좎?
    design_30 = {k: design_30.get(k, 0) for k in DESIGN_PATTERNS}
    dev_30    = {k: dev_30.get(k, 0) for k in DEV_PATTERNS}
    dev_7     = count_in_window(rows, DEV_PATTERNS, 7)

    def recur_rate(c7, c30):
        total_30 = sum(c30.values())
        total_7  = sum(c7.values())
        return round(total_7 / total_30 * 100) if total_30 else 0

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "user_turns_90d": len(rows),
        "design": {
            "counts_90d": design_90,
            "counts_30d": design_30,
            "counts_7d":  design_7,
            "recur_rate_pct": recur_rate(design_7, design_30),
        },
        "dev": {
            "counts_90d": dev_90,
            "counts_30d": dev_30,
            "counts_7d":  dev_7,
            "recur_rate_pct": recur_rate(dev_7, dev_30),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # ensure_ascii=True ???쒓뎅????\uXXXX escape 濡????(Windows cp949 ?섍꼍 ?명솚)
    OUT.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")

if __name__ == "__main__":
    try: main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)

