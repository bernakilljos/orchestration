#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit-hardcoded ??CLAUDE.md 짠 7-A1 (?섎뱶 寃쎈줈쨌?쒗겕由온텾ython 踰꾩쟾 湲덉?) ?먮룞 媛먯궗.
寃곌낵: .claude/state/hardcoded-audit.json
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / ".claude" / "state" / "hardcoded-audit.json"

PATTERNS = [
    ("users_path_win", re.compile(r"C:\\Users\\[a-z0-9_]+", re.IGNORECASE), "Windows ?ъ슜??寃쎈줈"),
    ("users_path_unix", re.compile(r"/home/[a-z0-9_]+"), "Linux ?ъ슜??寃쎈줈"),
    ("python_version", re.compile(r"Python3(10|11|12|13|14|15)\\python\.exe"), "Python 踰꾩쟾 諛뺤쓬"),
    ("desktop_hostname", re.compile(r"DESKTOP-[A-Z0-9]+"), "?뱀젙 ?몄뒪?몃챸"),
    ("ip_192", re.compile(r"192\.168\.\d+\.\d+"), "怨좎젙 ?ъ꽕 IP"),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    ("openai_key", re.compile(r"sk-[a-zA-Z0-9]{40,}"), "OpenAI/Anthropic API key"),
    ("github_pat", re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub PAT"),
]

# ?끸쁾??002 ??臾몄꽌(.md)?먯꽌 **寃쎈줈쨌踰꾩쟾쨌?몄뒪?맞텶P 留?* 硫댁젣?쒕떎.
#   ?? ?ㅼ륫 1002 ???⑥? 22嫄댁씠 ?꾨? **猷걔룰??대뱶媛 ?뚯씠?뉕쾶 ?곗? 留덈씪?띻퀬 ?몄슜??#   湲덉? ?덉떆**???`best-practices.md` ???ъ슜??寃쎈줈 ?덉떆 4嫄???. 洹쒖튃 臾몄꽌媛
#   ?먭린媛 湲덉??섎뒗 ?⑦꽩???곸뿀?ㅺ퀬 ?꾨컲?쇰줈 ?몃㈃, 怨좎튂??湲몄? **?덉떆瑜?吏?곕뒗
#   寃?*肉먯씠怨?洹몃윭硫?猷곗씠 ?살쓣 ?껊뒗??
#   ?끸쁾?? **?쒗겕由?3醫?aws_key쨌openai_key쨌github_pat)? 臾몄꽌?먯꽌??怨꾩냽 ?〓뒗??* ??#     ??md ???꾨? 硫댁젣?띾줈 ?볧엳硫?臾몄꽌??諛뺥엺 吏꾩쭨 ?ㅻ? ?곸썝??紐?蹂몃떎.
#     硫댁젣??짬?ㅽ깘??援ъ“?곸씤 ?⑦꽩쨩?먮쭔 嫄멸퀬, 짬?섎㈃ ?ш퀬???⑦꽩쨩?먮뒗 ??嫄대떎.
#   ?낆씠寃껋? ?뚭퇋移숈씠 ??몄쑝硫?洹쒖튃??怨좎튇?ㅳ?媛덈옒??肄붾뱶瑜?鍮꾪?吏 ?딅뒗??.
DOC_EXEMPT_KEYS = {"users_path_win", "users_path_unix",
                   "python_version", "desktop_hostname", "ip_192"}

# ?끸쁾??002 ????媛덈옒濡??섎댋?? 醫낆쟾????吏묓빀???욎뿬 ?덉뿀怨? 洹몃옒??#   짬.claude/state쨩 瑜?**寃쎈줈??3媛쒓? ??踰덈룄 嫄몃윭吏??곸씠 ?놁뿀??*:
#   鍮꾧탳媛 `any(p in SKIP_DIRS for p in rel.split("/"))` ????移?.claude ?먮뒗
#   state)?섍퀬留?留욎떠 蹂대뒗?? 吏묓빀?먮뒗 ??移몄쭨由?臾몄옄?댁씠 ?ㅼ뼱 ?덉뿀??
#   ?낃렇 寃곌낵 媛먯궗湲곌? **?먭린 寃곌낵 ?뚯씪(.claude/state/hardcoded-audit.json)??#     ?ㅼ떆 ?ㅼ틪**?덈떎 ??寃異쒗븳 ?꾨컲??罹먯떆???곹엳怨? ?ㅼ쓬 ?ㅽ뻾??洹멸구 ???쇰떎.
#     ?ㅼ륫 1002: ?꾩껜 115嫄?以?**38嫄댁씠 ???먭린李몄“**???異쒖쿂 1??.
#     ?レ옄媛 ?ㅽ뻾留덈떎 異쒕쟻?대뜕 寃껊룄, 怨좎튂吏 ?딆븘???섎뜕 寃껊룄 ???뚮Ц?대떎.
#   ?끹뚮갑?닿? ?덈떎怨?誘용뒗 寃껋씠 ?녿뒗 寃껊낫???꾪뿕?섎떎??A4)쨌?뚯륫???꾧뎄???먭린瑜?#     ?몄? ?딅뒗?ㅳ?A12)媛 ???먮━?먯꽌 媛숈씠 ?щ떎.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             # ??archive` 留??곹? ?덉뼱 ????μ냼???ㅼ젣 ?대쫫 `_archive` 媛 ??嫄몃졇??             #   (怨쇨굅 ?ㅻ깄??= ?묒뾽 ????꾨떂 쨌 猷⑦듃 CLAUDE.md 짠 3 ??洹몃젃寃?留먰븳??.
             "archive", "_archive", "outputs", "local_data",
             # ?낅윴???濡쒓렇 ???ъ꽕 IP 媛 李랁엳??嫄?洹??쒕쾭媛 ?ㅼ젣濡?洹?二쇱냼??ㅻ뒗
             #   **湲곕줉**?댁? ?뚯뒪???섎뱶肄붾뵫???꾨땲?? 吏?곕㈃ 湲곕줉???щ씪吏꾨떎(A15).
             "logs",
             # ?꿘PA ?섏쭛 ?곗텧臾???怨좉컼 ?ъ씠?몄뿉??湲곸뼱??**?곗씠??*?댁? ?곕━ ?뚯뒪媛
             #   ?꾨땲?? ?섏쭛???뚮쭏???섏뼱???レ옄媛 ?묒뾽怨?臾닿??섍쾶 ?붾뱾由ш퀬,
             #   諛쏆븘???띿뒪?몄뿉 ?좏겙 鍮꾩듂??臾몄옄?댁씠 ?덉쑝硫?CRITICAL ?ㅽ깘???쒕떎.
             "download", "evidence", "highlight",
             # ?낅깽?붽? 諛고룷???고????ㅼ씠踰?WASM 諛붿씤???? ??怨좎튌 ???녿뒗 肄붾뱶.
             "rpa_profiles"}

# 寃쎈줈???쒖쇅(??移??댁긽) ????吏묓빀怨?鍮꾧탳 諛⑹떇???ㅻⅤ誘濡??곕줈 ?붾떎.
SKIP_PREFIXES = (".claude/state", ".claude/logs", ".claude/context-cache")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".docx", ".pptx",
            ".xlsx", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav", ".sqlite",
            ".db", ".bak", ".pyc", ".pyo", ".ico",
            # ?낅줈洹몃뒗 짬?쇱뼱???셋살쓽 湲곕줉?대떎 ??`logs/` 諛뽰뿉 ?⑥뼱吏?寃껊룄 ?덉뼱
            #   ?뺤옣?먮줈??留됰뒗???ㅼ륫 1002: 猷⑦듃 `test_mock_err.log`).
            ".log", ".err"}


def scan():
    hits = {k: [] for k, _, _ in PATTERNS}
    scanned = 0
    for base, dirs, files in os.walk(ROOT):
        rel = Path(base).relative_to(ROOT).as_posix()
        # skip
        parts = rel.split("/")
        if any(p in SKIP_DIRS for p in parts) or \
                any(rel == p or rel.startswith(p + "/") for p in SKIP_PREFIXES):
            dirs[:] = []
            continue
        for name in files:
            ext = Path(name).suffix.lower()
            if ext in SKIP_EXT:
                continue
            fp = Path(base) / name
            try:
                if fp.stat().st_size > 500_000:
                    continue
                txt = fp.read_text(encoding="utf-8", errors="replace")
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                continue
            scanned += 1
            _is_doc = (ext == ".md")
            for key, pat, _ in PATTERNS:
                # ?낅Ц?쒖쓽 湲덉? ?덉떆 硫댁젣 ?????쒗겕由?3醫낆? 硫댁젣?섏? ?딅뒗????二쇱꽍).
                if _is_doc and key in DOC_EXEMPT_KEYS:
                    continue
                for m in pat.finditer(txt):
                    lineno = txt.count("\n", 0, m.start()) + 1
                    hits[key].append({
                        "file": fp.relative_to(ROOT).as_posix(),
                        "line": lineno,
                        "match": m.group(0)[:80],
                    })
                    if len(hits[key]) >= 100:
                        break
    return hits, scanned


def main():
    hits, scanned = scan()
    counts = {k: len(v) for k, v in hits.items()}
    total = sum(counts.values())
    critical = counts.get("aws_key", 0) + counts.get("openai_key", 0) + counts.get("github_pat", 0)
    status = "PASS" if total == 0 else ("CRITICAL" if critical else "WARN")
    result = {
        "ts": datetime.now().isoformat(),
        "scanned_files": scanned,
        "status": status,
        "total_hits": total,
        "counts": counts,
        "hits": {k: v[:20] for k, v in hits.items()},  # top 20 per pattern
        "patterns": {k: desc for k, _, desc in PATTERNS},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[audit-hardcoded] {status} - scanned {scanned} - total {total} - critical {critical}")
    print(f"  cache: {OUT.relative_to(ROOT)}")
    for k, n in counts.items():
        if n:
            print(f"  {k}: {n}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"[audit-hardcoded] err: {e}", file=sys.stderr)
        sys.exit(1)

