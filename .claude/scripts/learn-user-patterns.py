#!/usr/bin/env python
"""
learn-user-patterns.py ???ъ슜??諛섎났 吏???⑦꽩 ?먮룞 ?숈뒿

orca.db conversations + problem_solutions 遺꾩꽍 ??諛섎났 ?몃━嫄??ㅼ썙??top N 異붿텧
??.claude/state/learned-user-patterns.json ?????SessionStart hook 媛 systemMessage 濡??덈궡

二?1???먮룞 (?쇱슂??04:30 쨌 learn-style.py ? 媛숈씠) + ?ъ슜??紐낆떆 ??(/recall-patterns)
"""
from __future__ import annotations
import json, os, sqlite3, re, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
OUT = ROOT / ".claude" / "state" / "learned-user-patterns.json"
RULES = ROOT / ".claude" / "rules" / "user-emotion.md"

# ?대? 留ㅽ븨???몃━嫄?(user-emotion.md ?먯꽌 異붿텧)
EXISTING_TRIGGERS = set()
if RULES.exists():
    txt = RULES.read_text(encoding="utf-8", errors="ignore")
    # | **"X"쨌"Y"쨌"Z"** | ... | ?⑦꽩?먯꽌 X쨌Y쨌Z 異붿텧
    for m in re.finditer(r'\*\*["\']([^"\'\*]+)["\']', txt):
        for tok in re.split(r'[쨌,??]', m.group(1)):
            tok = tok.strip().strip('"\'')
            if 1 < len(tok) < 20:
                EXISTING_TRIGGERS.add(tok.lower())

# ?ъ슜???먯＜ ?곕뒗 ?댄쐶 異붿텧 (紐낆궗쨌?숈궗 ?대? 쨌 2~15 chars)
TOKEN_RE = re.compile(r'[媛-?즑-zA-Z]{2,15}')
# 遺덉슜??(?쇰컲???쒖쇅)
STOPWORDS = {
    "洹몃━怨?,"洹몃옒??,"?닿굅","?嫄?,"?곕━","吏湲?,"?꾨땲","?ㅻ뒛","?닿?","?덇?","洹몃깷","醫",
    "媛숈씠","紐⑤몢","?꾨?","?닿쾶","洹멸쾶","?寃?,"?대윴","洹몃윴","???,"?섎뒗","?덈뒗","?녿뒗","?덉뼱","?놁뼱",
    "?섎뒗","?덈릺","?섏뼱","?덉뼱??,"?덉옄??,"?먮굹","?댁빞","媛숈븘","媛숇떎","?띠뼱","?띕떎","?섏옄","?섏?",
    "the","and","for","with","this","that","what","how","why","when","where","your","from","have","has",
}

def extract_tokens(text: str) -> list[str]:
    toks = []
    for m in TOKEN_RE.findall(text or ""):
        t = m.lower()
        if t in STOPWORDS or t in EXISTING_TRIGGERS: continue
        if len(t) < 2: continue
        toks.append(t)
    return toks

def main():
    if not DB.exists():
        print("[WARN] orca.db ?놁쓬 쨌 skip"); return
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    counter = Counter()
    phrase_examples: dict[str, str] = {}
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content FROM conversations WHERE role='user' AND ts >= ? LIMIT 2000",
            (cutoff,)
        ).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[WARN] conversations 議고쉶 ?ㅽ뙣: {e}"); return

    for (content,) in rows:
        if not content: continue
        snippet = content[:200]
        for tok in extract_tokens(snippet):
            counter[tok] += 1
            # ?덉떆 臾몄옣 ???(泥섏쓬 1媛?
            if tok not in phrase_examples and len(snippet) < 100:
                phrase_examples[tok] = snippet.strip()

    # top 30 (3?? 諛섎났留?
    top = [(k, v) for k, v in counter.most_common(100) if v >= 3][:30]
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "orca.db.conversations 쨌 理쒓렐 30??쨌 role=user",
        "existing_triggers_count": len(EXISTING_TRIGGERS),
        "total_user_turns": len(rows),
        "top_patterns": [
            {"trigger": k, "count": v, "example": phrase_examples.get(k, "")}
            for k, v in top
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {OUT.name} 쨌 top {len(top)} ?⑦꽩 쨌 total user turns {len(rows)}")
    print(f"  top 5: {[t['trigger'] for t in result['top_patterns'][:5]]}")

if __name__ == "__main__":
    try:
        main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)

