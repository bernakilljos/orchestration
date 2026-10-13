#!/usr/bin/env python
"""
suggest-learned-patterns.py ???숈뒿??諛섎났 ?⑦꽩 以?**?꾩쭅 留ㅽ븨 ????* 寃껋쓣 ?쒖븞
(?먮룞 patch X 쨌 dry-run ?꾩슜 쨌 ?ъ슜???뱀씤 ?꾨쭔 諛섏쁺)

?먮쫫:
1. .claude/state/learned-user-patterns.json ?쎄린
2. user-emotion.md ?꾩옱 留ㅽ븨???몃━嫄곗? ?議?3. 誘몃ℓ??+ count?? ?⑦꽩留?"?쒖븞" ?쇰줈 ???4. SessionStart hook 媛 systemMessage 濡?"N 媛??좉퇋 ?⑦꽩 諛쒓껄 쨌 /apply-learned 濡?諛섏쁺" ?덈궡
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
LEARNED = ROOT / ".claude" / "state" / "learned-user-patterns.json"
RULES = ROOT / ".claude" / "rules" / "user-emotion.md"
SUGGESTIONS = ROOT / ".claude" / "state" / "learned-pattern-suggestions.json"

MIN_COUNT = 5  # ?덉쟾 threshold
NOISE = {"id","task","on","reset","mcp","command","pm","local","pjt","claude","?몃옓",
         "ago","src","dst","usr","etc","tmp","log","dir","env","key","val"}  # ?몄씠利?(紐낅갚???ㅼ젙 ?댄쐶)

def extract_existing_triggers(txt: str) -> set[str]:
    out = set()
    # | **"X"쨌"Y"쨌"Z"** | ?⑦꽩
    for m in re.finditer(r'\*\*["\']([^"\'\*]+)["\']\*\*', txt):
        for tok in re.split(r'[쨌,??]', m.group(1)):
            t = tok.strip().strip('"\'').lower()
            if t: out.add(t)
    return out

def main():
    if not LEARNED.exists():
        print(f"[WARN] {LEARNED.name} ?놁쓬 쨌 learn-user-patterns.py 癒쇱?")
        return
    data = json.loads(LEARNED.read_text(encoding="utf-8"))
    patterns = data.get("top_patterns", [])
    existing = extract_existing_triggers(RULES.read_text(encoding="utf-8", errors="ignore")) if RULES.exists() else set()

    suggestions = []
    for p in patterns:
        tok = p["trigger"].lower()
        if tok in NOISE: continue
        if tok in existing: continue
        if any(tok in e or e in tok for e in existing if len(e) > 2): continue  # 遺遺?留ㅼ묶??skip
        if p["count"] < MIN_COUNT: continue
        suggestions.append({
            "trigger": p["trigger"],
            "count": p["count"],
            "example": p["example"],
            "proposed_action": "留ㅽ븨 誘몄젙 쨌 ?ъ슜??吏???꾩슂"
        })

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "safe_threshold": MIN_COUNT,
        "existing_mappings": len(existing),
        "learned_total": len(patterns),
        "suggestions_count": len(suggestions),
        "note": "?먮룞 patch X 쨌 ?ъ슜?먭? /apply-learned ?먮뒗 吏곸젒 user-emotion.md ?섏젙",
        "suggestions": suggestions,
    }
    SUGGESTIONS.parent.mkdir(parents=True, exist_ok=True)
    SUGGESTIONS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {SUGGESTIONS.name} 쨌 ?좉퇋 ?쒖븞 {len(suggestions)} 媛?(count>={MIN_COUNT})")
    for s in suggestions[:5]:
        print(f"  [{s['count']}x] {s['trigger']}  ?? {s['example'][:60]}")

if __name__ == "__main__":
    try: main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)

