#!/usr/bin/env python3
"""verify-fresh-clone ??"git pull 留?諛쏆? ??PC ?먯꽌???숈옉?섎굹" ?뺤쟻 寃??

2026-10-02 ?ш퀬: ?곕뒗 肄붾뱶留??덇퀬 洹몃쫯(DDL쨌?곹깭?뚯씪 ?앹꽦湲????놁뼱?? ?섎룞?쇰줈 ?볦씤
?ㅻⅨ PC ?먯꽌留??숈옉?덈떎. ?꾨옒 2媛吏瑜?kit ?꾩껜?먯꽌 ?꾩닔 寃?ы븳??

  1. INSERT/UPDATE ?섎뒗 紐⑤뱺 ?뚯씠釉붿뿉 CREATE TABLE IF NOT EXISTS 媛 kit ?덉뿉 ?덈뒗媛
  2. .claude/state/*.json ???쎈뒗 ?뚯씪留덈떎, 洹??뚯씪???곕뒗 ?앹꽦湲곌? hook(settings.json)
     ?먯꽌 (吏곸젒 ?먮뒗 1?④퀎 ?몄텧濡? ?ㅽ뻾?섎뒗媛

寃곌낵: ?꾨컲 0 = exit 0 쨌 ?꾨컲 ?덉쓬 = exit 1 + 紐⑸줉. 遺꾨え(寃???????瑜???긽 異쒕젰.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [ROOT / ".claude" / "scripts", ROOT / ".claude" / "hooks", ROOT / "plugins"]
EXTS = {".py", ".sh"}

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass


def files():
    for d in SCAN_DIRS:
        for p in d.rglob("*"):
            if p.suffix in EXTS and "__pycache__" not in p.parts and p.name != Path(__file__).name:
                yield p


def main() -> int:
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in files()}
    all_text = "\n".join(texts.values())

    # 1) ?뚯씠釉?DDL
    created = set(re.findall(r"CREATE (?:VIRTUAL )?TABLE IF NOT EXISTS\s+(\w+)", all_text))  # FTS5 ??VIRTUAL ?ы븿
    written: dict[str, set[str]] = {}
    for p, t in texts.items():
        for tbl in re.findall(r"(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE)\s+(\w+)\s*(?:\(|SET)", t):
            written.setdefault(tbl, set()).add(str(p.relative_to(ROOT)))
    no_ddl = {t: w for t, w in written.items() if t not in created}

    # 1-b) ?곕뒗 而щ읆??DDL(?먮뒗 ALTER ADD COLUMN)???덈뒗媛 ??2026-10-02 session_summary.updated_at ?꾨씫 ?ш퀬
    ddl_cols: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*;", all_text, re.S):
        body = re.sub(r"--[^\n]*", "", m.group(2))   # SQL 二쇱꽍 ?쒓굅 (?ㅽ깘 諛⑹?)
        cols = {c.strip().split()[0] for c in body.split(",") if c.strip()}
        ddl_cols.setdefault(m.group(1), set()).update(cols)
    alter_cols = set(re.findall(r"ADD COLUMN\s+(\w+)", all_text)) | set(re.findall(r"""\("(\w+)",\s*"(?:TIMESTAMP|INTEGER|TEXT)""", all_text))
    # (?뚯씠釉? 而щ읆, ??? 3-?쒗뵆 ?뺤떇 ALTER 紐⑸줉???몄떇 (session-history-db.py ?ㅼ륫 쨌 2026-10-12)
    alter_cols |= set(re.findall(r"""\("\w+",\s*"(\w+)",\s*"(?:TIMESTAMP|INTEGER|TEXT|REAL)"\)""", all_text))
    bad_cols: list[str] = []
    for p, t in texts.items():
        for m in re.finditer(r"INSERT(?:\s+OR\s+\w+)?\s+INTO\s+(\w+)\s*\(([^)]*)\)(.{0,800}?)(?:\"\"\"|\"\s*,|\)\s*$)", t, re.S):
            tbl = m.group(1)
            if tbl not in ddl_cols:
                continue
            # ?뚯씠??臾몄옄???댁뼱遺숈씠湲?"a, " "b") ???곗샂?쑣룰났諛??쒓굅
            cols = {re.sub(r"[\s\"']", "", c) for c in m.group(2).split(",")} - {""}
            tail = m.group(3)
            if "DO UPDATE SET" in tail:
                cols |= set(re.findall(r"(\w+)\s*=", tail.split("DO UPDATE SET", 1)[1]))
            for c in sorted(cols - ddl_cols[tbl] - alter_cols - {"excluded"}):
                bad_cols.append(f"{tbl}.{c} ({p.relative_to(ROOT)})")

    # 2) state ?뚯씪 ?앹꽦湲???hook ?곌껐
    # hooks ?뱀뀡??command 留?(statusLine ? ?앹꽦湲곌? ?꾨땲???뚮퉬?먮씪 ?쒖쇅)
    sj = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
    cmds = [h.get("command", "") for evs in (sj.get("hooks") or {}).values()
            for m in evs or [] for h in m.get("hooks", [])]
    hooked = {Path(m).name for c in cmds for m in re.findall(r"[\w./-]+\.(?:sh|py)", c)}
    # hook ?ㅽ겕由쏀듃媛 **?ㅽ뻾?섎뒗** ?ㅽ겕由쏀듃源뚯? 1?④퀎 ?뺤옣 (二쇱꽍 ?멸툒? ?쒖쇅)
    run_re = re.compile(r"^(?!\s*#).*?(?:bash|python3?|sh|\$PY)\b[^\n]*?([\w.-]+\.(?:sh|py))", re.M)
    reach = set(hooked)
    for p, t in texts.items():
        if p.name in hooked:
            reach |= {m for m in run_re.findall(t)}
    # 2026-10-12 ??prompt-dispatch.py 泥섎읆 hook ??紐⑤뱢??import ??in-process 濡??뚮━硫??ㅽ뻾 以꾩씠 ?녿떎.
    #   hook ??.py ?덉뿉 ?대쫫(stem)???섏삤??媛숈? ?몃━??.py 紐⑤뱢???ㅽ뻾 寃쎈줈濡?蹂몃떎 (1?④퀎 + 洹?紐⑤뱢???ㅽ뻾 以?.
    mods = set()
    for p, t in texts.items():
        if p.name in hooked and p.suffix == ".py":
            for q in texts:
                if q.suffix == ".py" and q != p and q.parent.parent == p.parent and any(s in t for s in (q.stem, q.stem.replace("_", "-"))):
                    mods.add(q)
    for q in mods:
        reach.add(q.name)
        reach |= {m for m in run_re.findall(texts[q])}
        # load_script("?대쫫") ???뺤옣???놁씠 ?ㅽ겕由쏀듃瑜?in-process 濡?遺덈윭?ㅻ뒗 ?뺤떇 (prompt/_common.py)
        reach |= {m + ".py" for m in re.findall(r"""load_script\(\s*["']([\w.-]+)["']""", texts[q])}
    # statusLine 紐낅졊??留??뚮뜑 ?ㅽ뻾?섎뒗 ?앹꽦湲?(?먭린 罹먯떆瑜??ㅼ뒪濡??) ???뺤옣? ????    sl = (sj.get("statusLine") or {}).get("command", "")
    reach |= {Path(m).name for m in re.findall(r"[\w./-]+\.(?:sh|py)", sl)}
    state_reads: dict[str, set[str]] = {}
    for p, t in texts.items():
        for f in re.findall(r"""["']\.claude["'],\s*["']state["'],\s*["']([\w.-]+\.json)["']""", t):
            state_reads.setdefault(f, set()).add(p.name)
    orphan_state = {}
    for f, readers in state_reads.items():
        # ?앹꽦湲?= 洹??뚯씪紐낆쓣 ?ㅻ（??'?쎈뒗 履쎌씠 ?꾨땶' ?뚯씪. ?쎈뒗 履쎈쭔 ?덉쑝硫??먭린 罹먯떆
        # (statusline ???곌퀬 ?쎈뒗 rate-limits ?? ???쎈뒗 履쎌씠 ?ㅽ뻾 寃쎈줈???덉쑝硫??뺤긽.
        producers = {p.name for p, t in texts.items() if f in t and p.name not in readers}
        if not producers:
            producers = set(readers)
        if not (producers & reach):
            orphan_state[f] = (sorted(readers), sorted(producers))

    print(f"[verify-fresh-clone] 寃???뚯씪 {len(texts)} 쨌 ?곕뒗 ?뚯씠釉?{len(written)} 쨌 state ?쎄린 {len(state_reads)}")
    bad = 0
    for t, w in sorted(no_ddl.items()):
        bad += 1
        print(f"  [FAIL] ?뚯씠釉?{t}: DDL ?놁쓬 (?곕뒗 怨?{', '.join(sorted(w))[:160]})")
    for bc in sorted(set(bad_cols)):
        bad += 1
        print(f"  [FAIL] 而щ읆 {bc}: DDL쨌ALTER ???놁쓬")
    for f, (r, pr) in sorted(orphan_state.items()):
        bad += 1
        print(f"  [FAIL] state/{f}: ?쎈뒗 怨?{r} 쨌 ?앹꽦湲?{pr or '?놁쓬'} ??hook 誘몄뿰寃?)
    print(f"[verify-fresh-clone] {'PASS' if bad == 0 else 'FAIL'} ?꾨컲 {bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

