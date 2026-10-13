#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
statusline_context ??Claude Code ?좏겙 ?붾웾 ?쒖떆
?쒖? ?쇱씠釉뚮윭由щ쭔 ?ъ슜 - Windows ?⑥젙 4媛??뚰뵾.

寃쎈줈 ?? ~/.claude/statusline_context.py
"""
from __future__ import annotations
import json
import os
import re
import sys

# [?⑥젙 1] CP949 stdout ?뚰뵾
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, TypeError):
    pass

FILLED = "??  # ??EMPTY = "??   # ??WIDTH = 10

# ?곹븳 留ㅽ븨 - 湲?寃껊???LIMIT_PREFIXES = [
    # Opus 5.5 = 1M 湲곕낯 (?묐? ?좊Т 臾닿?) - "claude-opus-5" 蹂대떎 癒쇱? ?????    ("claude-opus-5-5", 1_000_000),
    # [1m] ?묐? - 湲?寃?癒쇱?
    ("claude-opus-5[1m]", 1_000_000),
    ("claude-sonnet-5[1m]", 1_000_000),
    ("claude-opus-4-8[1m]", 1_000_000),
    ("claude-opus-4-7[1m]", 1_000_000),
    ("claude-sonnet-4-6[1m]", 1_000_000),
    # ?쒖? 200K
    ("claude-opus-5", 200_000),
    ("claude-sonnet-5", 200_000),
    ("claude-opus-4-8", 200_000),
    ("claude-opus-4-7", 200_000),
    ("claude-sonnet-4-6", 200_000),
    ("claude-fable-5", 200_000),
    ("claude-haiku-4-5", 200_000),
]
DEFAULT_LIMIT = 200_000



def _project_root(start: str) -> str:
    """猷⑦듃 ?쒖떇(.git ?먮뒗 .claude+plugins)???덈뒗 議곗긽 ?붾젆?곕━瑜??뚮젮以??

    紐?李얠쑝硫?start 瑜?洹몃?濡?以???덉쟾痢????녿뜕 怨녹뿉 ?덈줈 留뚮뱾吏???딅뒗??.
    CLAUDE_PROJECT_DIR ???덉쑝硫?洹멸쾬???뺣낯?대떎.
    """
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isdir(env):
        return env
    cur = os.path.abspath(start or ".")
    for _ in range(12):
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        if os.path.isdir(os.path.join(cur, ".claude")) and os.path.isdir(os.path.join(cur, "plugins")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.abspath(start or ".")

def pick_limit(model_id: str) -> tuple[int, bool]:
    """(?곹븳, ?뺥솗?) 諛섑솚."""
    if not model_id:
        return DEFAULT_LIMIT, False
    # 2026-09-23: ?대쫫?쒕쭔 蹂대㈃ ??紐⑤뜽(claude-opus-5-5[1m])??claude-opus-5 ??嫄몃젮 200K 濡??ㅽ뙋?먮떎
    # (?ㅼ젣 26% ?몃뜲 "125% 利됱떆 compact"). [1m] ?묐?媛 怨?1M ?대떎 ???대쫫怨?臾닿??섍쾶 癒쇱? 蹂몃떎.
    if "[1m]" in model_id.lower():
        return 1_000_000, True
    for pref, lim in LIMIT_PREFIXES:
        if model_id.startswith(pref):
            return lim, True
    return DEFAULT_LIMIT, False


def cwd_to_proj_dir(cwd: str) -> str:
    """cwd -> ~/.claude/projects/<safe>/ ?대뜑紐?"""
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "projects", safe)


def last_assistant_usage(jsonl_path: str) -> dict | None:
    """jsonl 留덉?留?assistant ?덉퐫?쒖쓽 message.usage.

    2026-10-06 ???앹뿉?쒕???256KB ??嫄곌씀濡??쎄퀬 李얠쑝硫?硫덉텣??(127MB ?몄뀡 ?꾩껜 ?쎄린 ????珥??ㅼ륫)."""
    if not os.path.exists(jsonl_path):
        return None
    try:
        with open(jsonl_path, "rb") as f:
            f.seek(0, 2)
            pos, tail = f.tell(), b""
            while pos > 0:
                step = min(262144, pos)
                pos -= step
                f.seek(pos)
                lines = (f.read(step) + tail).split(b"\n")
                tail = lines[0] if pos > 0 else b""
                for raw in reversed(lines[1:] if pos > 0 else lines):
                    if b'"assistant"' not in raw:
                        continue
                    try:
                        rec = json.loads(raw.decode("utf-8", errors="replace"))
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if rec.get("type") == "assistant":
                        usage = ((rec.get("message") or {}).get("usage")) or None
                        if usage:
                            return usage
    except (OSError, IOError, json.JSONDecodeError):
        return None
    return None


# 紐⑤뜽蹂?rate - ?뺣낯? lib/pricing.py (?ш린 ?곕줈 ?먮㈃ 媛덈┛??쨌 ?뚯옣 E)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
try:
    from pricing import rates_for as _rates_for
except (ImportError, ModuleNotFoundError):
    _rates_for = None


def pick_rate(model_id: str) -> tuple[float, float, float, float]:
    """(input, output, cache_write, cache_read) USD/MTok. 紐⑤Ⅴ??紐⑤뜽? 0 (異붿젙 ????."""
    p = _rates_for(model_id) if _rates_for else None
    if not p:
        return (0.0, 0.0, 0.0, 0.0)
    return (p["input"] or 0.0, p["output"] or 0.0,
            p["cache_write"] or 0.0, p["cache_read"] or 0.0)


def cache_hit_rate(jsonl_path: str) -> float:
    """?몄뀡 prompt cache ?덊듃??= cache_read / (cache_read + input + cache_creation) * 100."""
    _c, tot_in, tot_cw, tot_cr = _scan_jsonl(jsonl_path, "")
    denom = tot_in + tot_cw + tot_cr
    if denom <= 0:
        return 0.0
    return tot_cr / denom * 100.0


def recent_error_count(cwd: str) -> int:
    """?섏쐞?명솚 ???ㅻ쪟 ?섎쭔."""
    return recent_log_issues(cwd)[0]


def recent_log_issues(cwd: str):
    """(?ㅻ쪟 ?? 寃쎄퀬 ?? ?ㅻ쪟 理쒕떎 濡쒓렇) ??以????쒓컖??理쒓렐 24h ??寃껊쭔 ?쇰떎.

    2026-10-06: ?덉쟾??짬24h ?덉뿉 媛깆떊??濡쒓렇??留덉?留?500以꽷살쓣 ?쒓컖 臾닿??섍쾶 ?뚭퀬 WARN쨌skip 源뚯?
    ?욎뼱 짬errors 121쨩 泥섎읆 遺??덈떎 (?ㅼ륫: kit 36嫄??꾨? ?쒓컖 ?녿뒗 以?쨌 24h ???ㅼ젣 ?ㅻ쪟 0).
    ?쒓컖 ?녿뒗 以꾩? ?몄젣 寃껋씤吏 紐⑤Ⅴ誘濡??몄? ?딅뒗??
    """
    import glob as _g
    import time as _t
    import re as _re
    import collections as _co
    log_dir = os.path.join(cwd, ".claude", "logs")
    if not os.path.isdir(log_dir):
        return 0, 0, ""
    cutoff = _t.time() - 86400
    ts_re = _re.compile(r"(20\d\d)-(\d\d)-(\d\d)[ T](\d\d):(\d\d):(\d\d)")
    err_re = _re.compile(r"\b(ERROR|FAIL|Traceback|\[err\]|\[!!\])", _re.I)
    warn_re = _re.compile(r"\b(WARN|\[skip\])", _re.I)
    errs, warns = _co.Counter(), 0
    # 2026-09-23: 紐낅졊쨌?꾨＼?꾪듃쨌議고쉶瑜?洹몃?濡??곷뒗 湲곕줉??濡쒓렇??類?? 紐낅졊 臾몄옄?댁뿉 "error" 媛 ?덉쑝硫?    # ?ㅻ쪟濡??몄뼱 90嫄?以?65嫄댁씠 bash_commands.log ????ㅼ젣 ?ㅻ쪟 ?꾨떂).
    skip = {"bash_commands.log", "lookup-history.log", "user-prompt-history.log",
            "conversation-save.log", "deflection-detect.log", "emotion-response.log",
            # 2026-10-12: mcp-health.log ??MCP ?뱀뀡?먯꽌 蹂꾨룄 吏묎퀎 (以묐났 諛⑹?)
            "mcp-health.log"}
    for lp in _g.glob(os.path.join(log_dir, "*.log")):
        if os.path.basename(lp) in skip:
            continue
        try:
            if os.path.getmtime(lp) < cutoff:
                continue
            with open(lp, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-500:]
            for ln in lines:
                e, w = err_re.search(ln), warn_re.search(ln)
                if not (e or w):
                    continue
                m = ts_re.search(ln)
                if not m:
                    continue
                if _t.mktime(tuple(map(int, m.groups())) + (0, 0, -1)) < cutoff:
                    continue
                if e:
                    errs[os.path.basename(lp)] += 1
                else:
                    warns += 1
        except (OSError, IOError, UnicodeDecodeError):
            continue
    top = errs.most_common(1)[0][0] if errs else ""
    return sum(errs.values()), warns, top


# 2026-10-06 ???뚮뜑留덈떎 紐⑤뱺 jsonl ??泥섏쓬遺???ㅼ떆 ?쎌뿀??(?붋룹뿰 ?⑷퀎濡?媛숈? ?뚯씪 2踰?쨌 127MB ?몄뀡 4珥??ㅼ륫).
#   ?뚯씪蹂?(?ш린쨌?쎌? ?꾩튂쨌message.id 蹂?吏묎퀎) 瑜?state ???먭퀬 **?섏뼱???룸?遺꾨쭔** ?쎈뒗??
#   ?ш린媛 以꾨㈃(??뼱?곌린) 泥섏쓬遺???ㅼ떆. 寃곌낵???꾩껜 ?ш퀎?곌낵 媛숇떎 (id 蹂?留덉?留?usage 洹쒖튃 ?숈씪).
_SCAN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state", "jsonl-scan-cache.json")
_SCAN: dict | None = None
_SCAN_DIRTY = False


def _scan_load() -> dict:
    global _SCAN
    if _SCAN is None:
        try:
            with open(_SCAN_PATH, encoding="utf-8") as f:
                _SCAN = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _SCAN = {}
    return _SCAN


def _scan_save() -> None:
    if not _SCAN_DIRTY or _SCAN is None:
        return
    try:
        os.makedirs(os.path.dirname(_SCAN_PATH), exist_ok=True)
        tmp = f"{_SCAN_PATH}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_SCAN, f, separators=(",", ":"))
        os.replace(tmp, _SCAN_PATH)
    except (OSError, IOError, TypeError):
        pass


import atexit as _atexit
_atexit.register(_scan_save)


def _scan_jsonl(jsonl_path: str, default_model: str = "", ts_prefix: str = "") -> tuple[float, int, int, int]:
    """(鍮꾩슜 USD, input, cache_write, cache_read) ??message.id 蹂?留덉?留?usage 留??쇰떎.

    ts_prefix ("2026-10"쨌"2026") 媛 ?덉쑝硫?洹?湲곌컙 timestamp ???묐떟留??⑹궛?쒕떎.
    2026-09-23: ?붋룸뀈 ?⑹궛???뚯씪 mtime ?쇰줈留?嫄몃윭 8??湲곕줉源뚯? 9?붿뿉 ?뷀뻽??$4,635 ???ㅼ젣 $2,924).
    """
    global _SCAN_DIRTY
    if not os.path.exists(jsonl_path):
        return (0.0, 0, 0, 0)
    cache = _scan_load()
    key = os.path.abspath(jsonl_path) + "|" + (default_model or "") + "|v2"  # v2: ??ぉ??timestamp 異붽?
    size = os.path.getsize(jsonl_path)
    ent = cache.get(key)
    if not ent or ent.get("size", 0) > size:
        ent = {"size": 0, "off": 0, "ids": {}}
    if ent["size"] != size:
        try:
            with open(jsonl_path, "rb") as f:
                f.seek(ent["off"])
                buf = f.read()
            end = buf.rfind(b"\n")
            if end >= 0:
                n0 = ent["off"]
                for i, raw in enumerate(buf[:end].split(b"\n")):
                    if b'"assistant"' not in raw:
                        continue
                    try:
                        rec = json.loads(raw.decode("utf-8", errors="replace"))
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if rec.get("type") != "assistant":
                        continue
                    msg = rec.get("message") or {}
                    u = msg.get("usage") or {}
                    in_r, out_r, cw_r, cr_r = pick_rate(msg.get("model") or default_model)
                    ti, tw, tr = (u.get("input_tokens", 0) or 0), (u.get("cache_creation_input_tokens", 0) or 0), (u.get("cache_read_input_tokens", 0) or 0)
                    cost = (ti * in_r + (u.get("output_tokens", 0) or 0) * out_r + tw * cw_r + tr * cr_r) / 1_000_000
                    ent["ids"][msg.get("id") or f"_off{n0}_{i}"] = [cost, ti, tw, tr, str(rec.get("timestamp") or "")[:10]]
                ent["off"] += end + 1
            ent["size"] = size
            cache[key] = ent
            _SCAN_DIRTY = True
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            return (0.0, 0, 0, 0)
    vals = [v for v in ent["ids"].values() if not ts_prefix or (len(v) > 4 and v[4].startswith(ts_prefix))]
    return (sum(v[0] for v in vals), sum(v[1] for v in vals), sum(v[2] for v in vals), sum(v[3] for v in vals))


def _jsonl_cost(jsonl_path: str, default_model: str = "", ts_prefix: str = "") -> float:
    """?⑥씪 jsonl - ?뚯씪 ??message.model 濡?rate 寃곗젙, ?놁쑝硫?default_model."""
    return _scan_jsonl(jsonl_path, default_model, ts_prefix)[0]


def session_cost(jsonl_path: str, model_id: str) -> float:
    return _jsonl_cost(jsonl_path, model_id)


def monthly_cost(cwd: str, model_id: str) -> float:
    """?대쾲 ??1??~ ?ㅻ뒛 쨌 ???꾨줈?앺듃??紐⑤뱺 jsonl ?몄뀡 鍮꾩슜 ?⑹궛."""
    import glob as _g
    import datetime as _d
    try:
        proj_dir = cwd_to_proj_dir(cwd)
        if not os.path.isdir(proj_dir):
            return 0.0
        # ?대쾲 ??1??00:00 timestamp
        now = _d.datetime.now()
        month_start = _d.datetime(now.year, now.month, 1).timestamp()
        total = 0.0
        for jp in _g.glob(os.path.join(proj_dir, "*.jsonl")):
            try:
                if os.path.getmtime(jp) < month_start:
                    continue
                total += _jsonl_cost(jp, model_id, now.strftime("%Y-%m"))
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                continue
        return total
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        return 0.0


def yearly_cost(cwd: str, model_id: str) -> float:
    """?ы빐 1??1??~ ?ㅻ뒛 쨌 ?꾨줈?앺듃??紐⑤뱺 jsonl ?몄뀡 鍮꾩슜 ?⑹궛."""
    import glob as _g
    import datetime as _d
    try:
        proj_dir = cwd_to_proj_dir(cwd)
        if not os.path.isdir(proj_dir):
            return 0.0
        now = _d.datetime.now()
        year_start = _d.datetime(now.year, 1, 1).timestamp()
        total = 0.0
        for jp in _g.glob(os.path.join(proj_dir, "*.jsonl")):
            try:
                if os.path.getmtime(jp) < year_start:
                    continue
                total += _jsonl_cost(jp, model_id, now.strftime("%Y"))
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                continue
        return total
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        return 0.0


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def render(tokens: int, limit: int, exact_model: bool, no_usage: bool) -> str:
    if no_usage:
        return f"{EMPTY * 8} 痢≪젙 ??
    ratio = 0.0 if limit <= 0 else min(tokens / limit, 1.0)
    W = 8
    filled = int(round(ratio * W))
    filled = min(W, max(0, filled))
    bar = FILLED * filled + EMPTY * (W - filled)
    pct = ratio * 100
    tok_s = fmt_tokens(tokens)
    lim_s = fmt_tokens(limit)
    q = "" if exact_model else "?"
    line = f"{bar} {pct:.0f}%{q} ({tok_s}/{lim_s}{q})"
    if pct >= 95:
        line += " 쨌 [!] ?먮룞 compact ?꾨컯 (?앸궗?쇰㈃ /clear)"
    elif pct >= 80:
        line += " 쨌 ?묒뾽 ?앸굹硫?/clear"
    elif pct >= 70:
        line += " 쨌 二쇱쓽"
    return line


def mini_bar(cur, total, w=6):
    """吏㏃? bar (multi-gauge ??."""
    if total <= 0:
        return "?" * w
    r = min(cur / total, 1.0)
    filled = int(round(r * w))
    filled = min(w, max(0, filled))
    return "?? * filled + "?? * (w - filled)


def gauge(label, cur, total, cur_s="", tot_s="", w=6):
    """짠 ?댿뻽?믠뼊?믠뼊 32% (cur/tot) ?ㅽ???"""
    if total <= 0:
        return f"{label} {'?' * w} (??"
    r = min(cur / total, 1.0)
    pct = r * 100
    cs = cur_s or fmt_tokens(int(cur))
    ts = tot_s or fmt_tokens(int(total))
    return f"{label} {mini_bar(cur, total, w)} {pct:.0f}% ({cs}/{ts})"


SEP = "?" * 50  # 援щ텇??_SESSION_COST = 0.0  # ?몄뀡 ?꾩쟻 異붿젙 鍮꾩슜 (jsonl 怨꾩궛 ????
_MONTHLY_COST = 0.0  # ?대쾲 ???꾩껜 鍮꾩슜 (紐⑤뱺 jsonl ?⑹궛)
_YEARLY_COST = 0.0   # ?ы빐 1??1?쇰????ㅻ뒛源뚯? ?⑹궛
_CACHE_HIT_RATE = 0.0  # ?몄뀡 prompt cache ?덊듃??%
_ERROR_COUNT = 0     # 理쒓렐 24h .claude/logs ??error쨌warn 移댁슫??

# 2026-09-05: plan_usage() 瑜?嫄룹뼱?덈떎. ~/.claude/statsig/ ?뚯씪???뺢퇋?앹쑝濡??묒뼱
#   session_limit쨌week_limit ??戮묒쑝???덈뒗??洹??대뜑?먮뒗 ?뚯씪??0媛쒖?怨??ㅼ륫),
#   ?몄텧?섎뒗 怨노룄 ?놁뿀?? Anthropic ?ㅼ젣 ?쒕룄?????ㅽ겕由쏀듃媛 ?쎌쓣 ???녿떎 ??#   紐??쎈뒗 媛믪쓣 吏?대궡?먮땲 ???꾩슫??(?뚯옣 A2).

def extra_gauges(cwd, data=None):
    """??以??뺤텞 - [?좏겙][?ъ궗??[?쇨컙][二쇨컙][?몄뀡?쒕룄][二쇨컙?쒕룄][MCP][git]."""
    # ?끸쁾??006 ??**?뺢퇋?붾뒗 ?ш린???쒕떎(?뺣낯 1怨?쨌 ??.**
    #   泥섏쓬??main() 履쎌뿉留??ｌ뿀?붾뜲 ???⑥닔 ?덉쓽 8媛?寃쎈줈媛 洹몃?濡??섏쐞 ?대뜑瑜?    #   蹂닿퀬 ?덉뼱 MCP쨌鍮꾩슜??怨꾩냽 鍮꾩뿀?????뚰븳 怨녹뵫 怨좎튂硫???鍮좎쭊?ㅳ띾? ?닿? ?덈떎.
    #   ?낇뙋?뺤? 짬.claude ?대뜑媛 ?덈뒗媛쨩???꾨줈?앺듃 援ъ“瑜?吏?대궡吏 ?딅뒗??.
    if cwd:
        _p0 = os.path.abspath(cwd)
        for _ in range(5):
            if os.path.isdir(os.path.join(_p0, "plugins")) and os.path.isdir(os.path.join(_p0, ".claude")):  # kit ?ㅼ튂 猷⑦듃 (?섏쐞 ?대뜑??濡쒖뺄 .claude ?먯꽌 硫덉텛吏 ?딄쾶 쨌 hook guard ? 媛숈? 湲곗?)
                cwd = _p0
                break
            _u0 = os.path.dirname(_p0)
            if _u0 == _p0:
                break
            _p0 = _u0
    budget_str = ""
    solutions_str = ""
    sessions_str = ""
    files_str = ""
    tasks_str = ""
    try:
        import sqlite3
        db = os.path.join(cwd, ".claude", "state", "orca.db")
        if os.path.exists(db):
            with sqlite3.connect(db) as c:
                # ?덉궛 (?쇨컙-二쇨컙-?붽컙)
                try:
                    b = c.execute(
                        "SELECT COALESCE(today_spent_usd,0), COALESCE(daily_limit_usd,0), "
                        "COALESCE(weekly_spent_usd,0), COALESCE(weekly_limit_usd,0), "
                        "COALESCE(monthly_spent_usd,0), COALESCE(monthly_limit_usd,0) "
                        "FROM budget LIMIT 1"
                    ).fetchone()
                    if b:
                        ds, dl, ws, wl, ms, ml = b
                        d_lim = f"${dl:.0f}" if dl else "??
                        w_lim = f"${wl:.0f}" if wl else "??
                        m_lim = f"${ml:.0f}" if ml else "??
                        db_bar = mini_bar(ds*100, (dl or 1)*100, 4) if dl else "????"
                        wb_bar = mini_bar(ws*100, (wl or 1)*100, 4) if wl else "????"
                        mb_bar = mini_bar(ms*100, (ml or 1)*100, 4) if ml else "????"
                        budget_str = (
                            f"?쇨컙 {db_bar} ${ds:.2f}/{d_lim}\n"
                            f"二쇨컙 {wb_bar} ${ws:.2f}/{w_lim}\n"
                            f"?붽컙 {mb_bar} ${ms:.2f}/{m_lim}"
                        )
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
                # ?ъ궗??solutions
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(AVG(reusable_score),0) FROM problem_solutions"
                    ).fetchone()
                    if r and r[0]:
                        solutions_str = f"?ъ궗??{r[0]}嫄?- ?됯퇏 {r[1]:.1f}"
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
                # ?몄뀡
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(SUM(turns),0), COALESCE(SUM(tokens_total),0) "
                        "FROM session_summary"
                    ).fetchone()
                    if r:
                        sessions_str = f"?몄뀡 {r[0]} - ??{r[1]}"
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
                # ?ㅻ뒛 ?뚯씪 蹂寃?                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM file_audit "
                        "WHERE ts >= datetime('now','-1 day')"
                    ).fetchone()
                    if r and r[0]:
                        files_str = f"?ㅻ뒛 ?뚯씪 {r[0]}嫄?
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
                # 吏꾪뻾 以?task
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"
                    ).fetchone()
                    if r and r[0]:
                        tasks_str = f"task {r[0]}"
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass
    # MCP - Headroom proxy ?ъ뒪泥댄겕
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=0.3)
        mcp = "MCP on"
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        mcp = "MCP off"
    # git branch + uncommitted
    git_str = ""
    try:
        import subprocess
        b = subprocess.run(
            ["git", "--no-optional-locks", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1
        )
        branch = b.stdout.strip() if b.returncode == 0 else ""
        s = subprocess.run(
            ["git", "--no-optional-locks", "-C", cwd, "status", "--porcelain"],
            capture_output=True, text=True, timeout=1
        )
        dirty = len([x for x in s.stdout.splitlines() if x.strip()]) if s.returncode == 0 else 0
        if branch:
            git_str = f"git {branch}" + (f" ({dirty} 蹂寃?" if dirty else " clean")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # Agent 吏꾪뻾瑜??뱀뀡 異붽? (2026-10-12)
    agent_str = ""
    try:
        active_agents_file = os.path.join(cwd, ".claude", "state", "active-agents.json")
        if os.path.exists(active_agents_file):
            with open(active_agents_file, "r", encoding="utf-8") as f:
                agents = json.load(f) if isinstance(json.load(open(active_agents_file)), list) else []
            # ?쒖꽦 agent (end_ts ?녿뒗 寃껊뱾) 吏묎퀎
            active = [a for a in agents if not a.get("end_ts")]
            if active:
                import collections as _col
                agent_counts = _col.Counter(a["id"].split("-")[0].lower() for a in active)
                agent_list = " 쨌 ".join(f"{name} 횞{cnt}" if cnt > 1 else name
                                       for name, cnt in sorted(agent_counts.items()))
                # 理쒕? duration (吏꾪뻾 以묒씤 寃?以? - ?됯퉼 湲곗?
                max_dur = max((a.get("duration_s", 0) for a in active), default=0)
                if max_dur > 180:  # 3遺?
                    color = "\033[1;31m"  # 鍮④컯
                    severity = "?뵶"
                elif max_dur > 60:  # 1~3遺?                    color = "\033[1;35m"  # 二쇳솴/留덉젨?
                    severity = "?윝"
                elif max_dur > 30:  # 30s~1遺?                    color = "\033[1;33m"  # ?몃옉
                    severity = "?윞"
                else:  # <30s
                    color = "\033[1;32m"  # ?뱀깋
                    severity = "?윟"
                agent_str = (f"{color}{severity} {agent_list} "
                            f"({max_dur}s)\033[0m")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # ??以?援ъ“ - line 1: ?몄뀡(?좏겙怨??⑹퀜吏?in main) 쨌 line 2: 二쇨컙 + MCP + ?ъ궗??+ agent
    import datetime as _dt
    import glob as _glob
    session_gauge = ""
    week_gauge = ""

    def _bar(pct, w=8):
        pct = max(0.0, min(100.0, pct))
        filled = int(round(pct / 100.0 * w))
        return "?? * filled + "?? * (w - filled)

    # 2026-09-07: ?몄뀡쨌二쇨컙 ?먯껜 異붿젙(5h李?寃쎄낵 쨌 ?꾨줈?앺듃 jsonl ?묐떟 ????嫄룹뼱?덈떎.
    #   ?꾨옒 rate_limits 釉붾줉????긽 ??뼱?⑥꽌 二쎌? 肄붾뱶?怨? 留??뚮뜑留덈떎 7?쇱튂 jsonl ??    #   ?꾨? ?쎈뒓???곹깭諛붾쭔 ?먮젮議뚮떎. ?ㅺ컪? stdin rate_limits + 罹먯떆濡?異⑸텇?섎떎.

    # 3) 吏㏃? ?몃뵒耳?댄꽣 (MCP - ?ъ궗??
    tail = []
    # MCP 移댁슫????.claude/state/mcp-status.json (?뺤떇: "MCP 14 on 13 off")
    mcp_shown = False
    try:
        mcp_cache = os.path.join(cwd, ".claude", "state", "mcp-status.json")
        # ?뚯씪???꾩삁 ?놁쓣 ?뚮룄 諛깃렇?쇱슫??痢≪젙 ?쒖옉 (?덈줈 蹂묓빀???대뜑?먯꽌 'MCP off' 濡쒕쭔 ?⑤뜕 寃?쨌 1006 A1 ?ㅼ륫)
        if not os.path.exists(mcp_cache):
            try:
                import time as _time0
                mk0 = os.path.join(cwd, ".claude", "state", "mcp-refresh.started")
                scr0 = os.path.join(cwd, ".claude", "scripts", "refresh-mcp-status.sh")
                if os.path.exists(scr0) and (not os.path.exists(mk0) or _time0.time() - os.path.getmtime(mk0) > 600):
                    os.makedirs(os.path.dirname(mk0), exist_ok=True)
                    open(mk0, "w").close()
                    import subprocess as _sp0
                    _sp0.Popen(["bash", scr0], stdout=_sp0.DEVNULL, stderr=_sp0.DEVNULL, stdin=_sp0.DEVNULL,
                               creationflags=(0x08000000 | 0x00000008) if os.name == "nt" else 0)
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                pass
        if os.path.exists(mcp_cache):
            import time as _time
            age = _time.time() - os.path.getmtime(mcp_cache)
            with open(mcp_cache, "r", encoding="utf-8") as f:
                ms = json.load(f)
            ok = int(ms.get("connected", 0))
            fail = int(ms.get("failed", 0))
            # 1h ?섏쑝硫?諛깃렇?쇱슫???ъ륫??(SessionStart ?먯꽌留?媛깆떊??硫곗튌 ?몄뀡??91h ??媛믪씠 ?대떎)
            #   李??놁쓬 쨌 10遺????ъ떎??諛⑹? 留덉빱 쨌 ?뚮뜑??湲곕떎由ъ? ?딆쓬 (claude mcp list ~30s)
            if age > 3600:
                try:
                    mk = os.path.join(cwd, ".claude", "state", "mcp-refresh.started")
                    if not os.path.exists(mk) or _time.time() - os.path.getmtime(mk) > 600:
                        open(mk, "w").close()
                        import subprocess as _sp
                        _sp.Popen(["bash", os.path.join(cwd, ".claude", "scripts", "refresh-mcp-status.sh")],
                                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, stdin=_sp.DEVNULL,
                                  creationflags=(0x08000000 | 0x00000008) if os.name == "nt" else 0)
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
            # 4h ?섏쑝硫?紐??쒓컙 ??媛믪씤吏 ?곷뒗??(?덉쟾 "?" ???살씠 ??蹂댁???
            stale = f" ({int(age // 3600)}h ??" if age > 14400 else ""
            tot = ok + fail
            tail.append((f"MCP {ok}/{tot}" if not fail else f"[!] MCP {ok}/{tot} ({fail} ?ㅽ뙣)") + stale)
            mcp_shown = True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass
    if not mcp_shown:
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=0.3)
            tail.append("MCP on")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            tail.append("MCP off")
    # git ?쒖떆 ?쒓굅 (?ъ슜???붿껌 2026-09-03)
    try:
        import sqlite3
        db = os.path.join(cwd, ".claude", "state", "orca.db")
        if os.path.exists(db):
            with sqlite3.connect(db) as c:
                r = c.execute(
                    "SELECT COUNT(*), COALESCE(AVG(reusable_score),0) FROM problem_solutions"
                ).fetchone()
                if r and r[0]:
                    cnt = int(r[0])
                    avg = float(r[1] or 0)
                    rate = min(max(avg / 10.0 * 100.0, 0.0), 100.0)
                    tail.append(f"?ъ궗??{cnt} ({rate:.0f}%)")
                # orca hit 移댁슫??(activations 쨌 tasks)
                try:
                    a = c.execute("SELECT COUNT(*) FROM activations").fetchone()
                    t = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN "
                        "('locked','pending','in_progress','waiting_approval')"
                    ).fetchone()
                    ac = int(a[0]) if a else 0
                    tk = int(t[0]) if t else 0
                    # 移??덉뿉 '쨌' 瑜????곕㈃ 移?援щ텇怨??욎씤??쨌 task 0 ? ?쒖떆 ????                    if ac:
                        tail.append(f"orca {ac}")
                    if tk:
                        tail.append(f"task {tk}")
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
                    pass
                # AI 鍮꾩슜? 蹂꾨룄 line3 濡?遺꾨━ (?ш린?쒕뒗 append X)
                pass
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass
    # 2026-10-02: ?꾨옒 3媛쒕뒗 orca.db ? 臾닿? ??DB ?녿뒗 PC ?먯꽌???쒖떆 (?꾩뿏 db 釉붾줉 ?덉뿉 媛뉙? ?щ씪吏?
    # 2026-10-12: Agent 吏꾪뻾瑜?異붽?
    if agent_str:
        tail.insert(0, agent_str)
    try:
        # Cache hit rate (prompt cache ?덇컧)
        # stdin prompt_cache.hit_ratio (Claude Code ?ㅼ륫) ?곗꽑, ?놁쑝硫?jsonl 怨꾩궛
        _pc = (data or {}).get("prompt_cache") or {}
        _hr = _pc.get("hit_ratio")
        _cr = float(_hr) * 100 if isinstance(_hr, (int, float)) else _CACHE_HIT_RATE
        if _cr > 0:
            tail.append(f"cache {_cr:.0f}%")
        # 理쒓렐 24h error쨌warn 移댁슫??        _e, _w, _top = recent_log_issues(cwd)
        if _e:
            tail.append(("[!] " if _e > 20 else "") + f"?ㅻ쪟 {_e}" + (f" ({_top})" if _top else ""))
        if _w:
            tail.append(f"寃쎄퀬 {_w}")
        # ?섎뱶肄붾뵫 媛먯궗 寃곌낵 (蹂꾨룄 罹먯떆)
        try:
            aud = os.path.join(cwd, ".claude", "state", "hardcoded-audit.json")
            if os.path.exists(aud):
                with open(aud, "r", encoding="utf-8") as f:
                    a = json.load(f)
                st = a.get("status", "?")
                tot = int(a.get("total_hits", 0))
                if st == "PASS":
                    tail.append("?섎뱶肄붾뵫 0")
                elif st == "CRITICAL":
                    tail.append(f"[!] ?섎뱶肄붾뵫 {tot}")
                else:
                    tail.append(f"?섎뱶肄붾뵫 {tot}")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            pass
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # AI 鍮꾩슜 line3 (?몄뀡 쨌 ?꾩썡 쨌 ?꾧컙 쨌 KRW 蹂묎린)
    # 2026-09-05: ?몄뀡 鍮꾩슜? Claude Code 媛 cost.total_cost_usd 濡?以???뺥솗??媛?.
    #   jsonl ???④??쒕줈 ?섏쭦??怨꾩궛?섎뜕 洹쇱궗移섎낫???댁そ??留욌떎. ?붋룸뀈媛꾩? ?ъ쟾??    #   ???꾨줈?앺듃 jsonl ?⑹궛?대씪 "(???꾨줈?앺듃)" ?쇰꺼???좎??쒕떎.
    global _SESSION_COST
    _delta = 0.0  # ???몄뀡??(怨듭떇媛?- jsonl 異붿젙) ???붋룸뀈 ?⑷퀎 ?덉쓽 ?몄뀡 紐ル룄 怨듭떇媛믪쑝濡?援먯껜
    try:
        _c = (data or {}).get("cost") or {}
        if isinstance(_c.get("total_cost_usd"), (int, float)):
            _official = float(_c["total_cost_usd"])
            _delta = _official - _SESSION_COST
            _SESSION_COST = _official
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass
    rate = float(os.environ.get("USD_KRW_RATE", "1350"))
    monthly = (_MONTHLY_COST + _delta) if _MONTHLY_COST > 0 else _SESSION_COST
    yearly = (_YEARLY_COST + _delta) if _YEARLY_COST > 0 else monthly
    import datetime as _dt2
    cur_m = _dt2.datetime.now().month
    if _SESSION_COST > 0.001 or monthly > 0.001 or yearly > 0.001:
        def _krw(usd):
            v = usd * rate
            return f"??int(v):,}" if v >= 1 else f"??v:.0f}"
        # 2026-09-05: monthly_cost쨌yearly_cost ??**???꾨줈?앺듃 ?대뜑??jsonl 留?* ?⑹궛?쒕떎
        #   (statusline_context.py ??monthly_cost(cwd) 李멸퀬). 洹몃옒??李쎈쭏??媛믪씠 ?ㅻⅤ????        #   lottoclaude ??9??$2,306, orchestration_v1 ? 媛숈? ??$14. ????留욌뒗 媛믪씤??        #   ?쇰꺼???놁뼱??怨꾩젙 ?꾩껜 泥?뎄?≪쑝濡??쏀삍?? 踰붿쐞瑜??곸뼱 ?붾떎.
        line3 = (
            f"API ?뺢? ?섏궛(援щ룆 泥?뎄???꾨떂) ?몄뀡 ${_SESSION_COST:,.2f} ({_krw(_SESSION_COST)}) 쨌 "
            f"{cur_m}??${monthly:,.2f} ({_krw(monthly)}) 쨌 "
            f"?곌컙 ${yearly:,.2f} ({_krw(yearly)}) 쨌 ???꾨줈?앺듃 湲곗?"
        )
    else:
        line3 = ""

    # ------------------------------------------------------------------
    # 2026-09-05: Claude Code 媛 statusline ?낅젰?쇰줈 **吏꾩쭨 ?ъ슜??*??以??
    #   rate_limits.five_hour / seven_day ??used_percentage ? resets_at ??    #   /status ?붾㈃怨?媛숈? 媛믪씠???ㅼ륫: ?몄뀡 15% resets 12:20pm, 二쇨컙 2% resets Sep 10 8am).
    #   洹몃룞?????ㅽ겕由쏀듃??洹멸구 紐?諛쏅뒗 以??뚭퀬 jsonl ???몄꽌 洹쇱궗移섎? 留뚮뱾怨??덉뿀????    #   ?몄뀡? 5?쒓컙 李?異붿젙, 二쇨컙? "?꾨줈?앺듃 ?묐떟 嫄댁닔 / ?꾩쓽 遺꾨え" ??/status ? ??留욎븯??
    #   諛쏆? 媛믪씠 ?덉쑝硫?洹멸쾬???대떎. ?놁쓣 ?뚮쭔 ?꾨옒 ?먯껜 怨꾩궛?쇰줈 臾쇰윭?쒕떎.
    def _fmt_reset(ts):
        try:
            dt = _dt.datetime.fromtimestamp(int(ts))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            return ""
        today = _dt.date.today()
        clock = dt.strftime("%I:%M%p").lstrip("0").lower()
        if dt.date() == today:
            return clock
        return dt.strftime("%b ") + str(dt.day) + " " + clock

    # 2026-09-07: rate_limits 媛 **留??뚮뜑留덈떎 ?ㅻ뒗 寃껋씠 ?꾨땲??* (?ㅼ륫).
    #   ?몄뀡 泥??뚮뜑(泥?API ?묐떟 ??쨌?쇰? ?뚮뜑?먯꽌?????먯껜媛 ?녿떎. 洹몃븣 ?꾨옒 ?먯껜 怨꾩궛?쇰줈
    #   臾쇰윭?섎㈃ "二쇨컙 ???꾨줈?앺듃 ?묐떟 232嫄?(7??쨌 ?쒕룄 誘몄꽕??" 泥섎읆 **?ㅻⅨ 吏??*媛 ??대굹?
    #   "怨좎낀?ㅻ뜑????洹?臾멸뎄" 濡??쏀삍??(2026-09-07 ?ъ슜??吏??.
    #   -> 留덉?留됱쑝濡?諛쏆? ?ㅺ컪??怨꾩젙 ?⑥쐞濡?罹먯떆???먭퀬, ?????뚮뒗 洹?媛믪쓣 ?대떎.
    #      罹먯떆???놁쑝硫??レ옄瑜?吏?대궡吏 留먭퀬 "吏묎퀎 ?湲? 濡?鍮꾩슫??(?뚯옣 A2).
    _rl_cache = os.path.join(os.path.expanduser("~"), ".claude", "state", "rate-limits.json")

    def _read_rl(d):
        """?섏씠濡쒕뱶?먯꽌 ?좏슚??rate_limits 留?戮묐뒗?? ?놁쑝硫?None."""
        rl = (d or {}).get("rate_limits") or {}
        out = {}
        for k in ("five_hour", "seven_day"):
            v = rl.get(k) or {}
            if isinstance(v.get("used_percentage"), (int, float)):
                out[k] = {"used_percentage": float(v["used_percentage"]),
                          "resets_at": v.get("resets_at")}
        return out or None

    rl = _read_rl(data)
    rl_age = 0.0
    if rl:
        try:
            os.makedirs(os.path.dirname(_rl_cache), exist_ok=True)
            import time as _time
            with open(_rl_cache, "w", encoding="utf-8") as _f:
                json.dump({"rate_limits": rl, "ts": _time.time()}, _f)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            pass
    else:
        try:
            import time as _time
            with open(_rl_cache, "r", encoding="utf-8") as _f:
                c = json.load(_f)
            cached = _read_rl(c)
            if cached:
                rl = cached
                rl_age = max(0.0, _time.time() - float(c.get("ts") or 0))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            rl = None

    if rl:
        # 罹먯떆媛 30遺??섍쾶 臾듭뿀?쇰㈃ 媛??ㅼ뿉 ~ 瑜?遺숈뿬 "吏곸쟾 ?ㅺ컪" ?꾩쓣 諛앺엺??
        mark = "~" if rl_age > 1800 else ""
        fh = rl.get("five_hour") or {}
        sd = rl.get("seven_day") or {}
        if "used_percentage" in fh:
            pct = fh["used_percentage"]
            r = _fmt_reset(fh.get("resets_at"))
            session_gauge = ("?몄뀡 " + _bar(pct) + f" {pct:.0f}%{mark}"
                             + (f" (reset {r})" if r else ""))
        if "used_percentage" in sd:
            pct = sd["used_percentage"]
            r = _fmt_reset(sd.get("resets_at"))
            week_gauge = ("二쇨컙 " + _bar(pct) + f" {pct:.0f}%{mark}"
                          + (f" (reset {r})" if r else ""))
    else:
        # ?ㅺ컪??罹먯떆???녿떎 = ?꾩쭅 ??踰덈룄 紐?諛쏆븯?? ?ㅻⅨ 吏?쒕줈 ?泥댄븯吏 ?딅뒗??
        session_gauge = "?몄뀡 (吏묎퀎 ?湲?"
        week_gauge = "二쇨컙 (吏묎퀎 ?湲?"

    # fast 異붿쿇 諭껋? ??二쇨컙 budget 蹂댄샇 쨌 ?좏겙 compact ?꾨컯留?OFF
    # ?몄뀡 % (five_hour) ??quota ?꾨컯 吏??쨌 fast on/off ? 臾닿? (reset 湲곕떎由щ㈃ ??
    # ?낃린以 (?ъ슜???뺤젙 2026-10-06 ???꾩쓽 蹂寃?湲덉?):
    #   二쇨컙 ??0%  ??[!] fast OFF (二쇨컙 N%)
    #   二쇨컙 50~79% ??fast OFF (二쇨컙 N% 蹂댄샇)
    #   ?좏겙 ??0%  ??fast OFF (?좏겙 N% 쨌 compact ?꾨컯)
    #   洹???      ??fast ON
    # ANSI ??(/clear ?좊룄??쨌 Claude 媛 slash command ?먮룞 ?ㅽ뻾 遺덇? ???ъ슜???덉뿉 ?꾧쾶)
    _RED = "\033[1;31m"; _YEL = "\033[1;33m"; _RST = "\033[0m"
    try:
        _wp = float((rl or {}).get("seven_day", {}).get("used_percentage", 0))
        _tp = float((data or {}).get("_ctx_pct", 0))
        if _tp >= 95:
            tail.append(f"{_RED}[!!] /clear 沅뚯옣 (?좏겙 {_tp:.0f}% 쨌 ?묒뾽 ?앸궗?쇰㈃ 利됱떆){_RST}")
        elif _tp >= 80:
            tail.append(f"{_YEL}[!] /clear 沅뚯옣 (?좏겙 {_tp:.0f}% 쨌 compact ?꾨컯){_RST}")
        elif _wp >= 80:
            tail.append(f"{_RED}[!!] fast OFF (二쇨컙 {_wp:.0f}%){_RST}")
        elif _wp >= 50:
            tail.append(f"{_YEL}fast OFF (二쇨컙 {_wp:.0f}% 蹂댄샇){_RST}")
        else:
            tail.append("fast ON")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # ?붿옄?맞룰컻諛?猷??꾨컲 吏??(rule-adherence.json cache 쨌 10遺?TTL 쨌 ~14ms)
    design_line = ""
    dev_line = ""
    try:
        # ?끸쁾??006 ??**?뚯씪? 遺紐???μ냼 猷⑦듃)???덇퀬 cwd ???섏쐞 ?대뜑??**
        #   ?ㅼ륫: cwd=??Project1.5 ?몃뜲 rule-adherence.json ?
        #   ??C.ICM_Agent_Go/.claude/state/ ?먮쭔 ?덈떎 ???붿옄?맞룰컻諛?以꾩씠 鍮꾩뿀??
        #   ?끸쁾洹몃옒??statusline ???뚮줈??6以? ?뚮줈??3~4以꾨줈 ?섏솕????        #     Claude Code 媛 二쇰뒗 cwd 媛 猷⑦듃???뚮쭔 留욎븯??寃껋씠??
        #   ?낅?紐⑤줈 嫄곗뒳??李얜뒗??理쒕? 4?? ??猷⑦듃媛 ?대뵒???숈옉?댁빞 ?쒕떎.
        ra = ""
        _d = os.path.abspath(cwd) if cwd else ""
        for _ in range(4):
            if not _d:
                break
            _c = os.path.join(_d, ".claude", "state", "rule-adherence.json")
            if os.path.exists(_c):
                ra = _c
                break
            _u = os.path.dirname(_d)
            if _u == _d:
                break
            _d = _u
        if ra:
            with open(ra, "r", encoding="utf-8") as f:
                _ra = json.load(f)
            def _fmt(section_name, section):
                c90 = section.get("counts_90d") or {}
                rr  = section.get("recur_rate_pct", 0)
                # 2026-10-07 ??吏묎퀎 ?뚯씪??????0嫄????놁쓬)?닿굅??鍮꾩뼱 ?덉뼱???몄뀡 ?녿뒗 ?곸쐞 ?대뜑)
                #   ??ぉ ?꾨?瑜?0 ?쇰줈 梨꾩썙 以??먯껜媛 ?щ씪吏吏 ?딄쾶 ?쒕떎 (A.RMS쨌A2 ?ㅼ륫).
                _ALL = {"design": ("?대え吏", "?щ갚", "踰꾩쟾愿由?, "?곗텧臾쇨린??),
                        "dev": ("利앸챸吏??, "誘몃컲??, "?꾩닔議곗궗skip")}
                c90 = {**{k: 0 for k in _ALL.get(section_name, ())}, **c90}
                if not c90: return ""
                # 2026-10-06 ?ъ슜??吏????媛숈? ??ぉ? ?대뒓 ?꾨줈?앺듃?먯꽌??媛숈? ??(嫄댁닔濡???諛붽씀吏 ?딆쓬).
                #   ??ぉ ?대쫫留?怨좎젙 ?됱쑝濡?媛뺤“ 쨌 ?レ옄쨌援щ텇?먮뒗 湲곕낯??쨌 0嫄대룄 ?쒖떆.
                # 2026-10-12 ?ъ슜??吏?????쒖꽌???몄뀡留덈떎 諛붾뚮㈃ ???? count DESC ?뺣젹 X 쨌 怨좎젙 ?쒖꽌.
                _HUE = {"?щ갚": "35", "?곗텧臾쇨린??: "33", "踰꾩쟾愿由?: "36", "?대え吏": "34",
                        "?꾩닔議곗궗skip": "31", "利앸챸吏??: "33", "誘몃컲??: "35"}
                _ORDER = {
                    "design": ["?곗텧臾쇨린??, "?대え吏", "?щ갚", "踰꾩쟾愿由?],
                    "dev":    ["?꾩닔議곗궗skip", "誘몃컲??, "利앸챸吏??],
                }
                def _hl(k):
                    return f"\033[1;{_HUE.get(k, '37')}m{k}\033[0m"
                order = _ORDER.get(section_name, list(c90.keys()))
                # 怨좎젙 ?쒖꽌 癒쇱?, 留ㅽ븨 諛???ぉ? ?ㅼ뿉 count DESC 濡?遺숈엫 (?좉퇋 移댄뀒怨좊━ ???
                seen = set(order)
                extras = sorted([k for k in c90.keys() if k not in seen], key=lambda k: -c90[k])
                parts = [f"{_hl(k)} {c90[k]}" for k in (order + extras) if k in c90]
                return " 쨌 ".join(parts) + f" 쨌 \033[1m?щ컻瑜?033[0m {rr}%"
            design_line = _fmt("design", _ra.get("design") or {})
            dev_line    = _fmt("dev", _ra.get("dev") or {})
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # 理쒖쥌 議곕┰ - session_gauge ??蹂꾨룄 諛섑솚 (main ?먯꽌 token_line 怨??⑹묠)
    line2_parts = []
    if week_gauge:
        line2_parts.append(week_gauge)
    if tail:
        line2_parts.extend(tail)
    line2 = " - ".join(line2_parts)
    return {"session": session_gauge, "line2": line2, "line3": line3,
            "week": week_gauge, "tail": tail, "cost": line3,
            "design": design_line, "dev": dev_line}


def main() -> None:
    # [?⑥젙 4] ?덉쇅 ?섎룄 rc=0 + 鍮?寃뚯씠吏
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        data = {}

    # 吏꾨떒??- 留덉?留?stdin ?먮Ц (?꾨뱶 ?ㅼ륫 洹쇨굅)
    try:
        _cwd0 = data.get("cwd") or ""
        if _cwd0:
            with open(os.path.join(_cwd0, ".claude", "state", "statusline-stdin.json"),
                      "w", encoding="utf-8") as _f:
                json.dump(data, _f, ensure_ascii=False, indent=2)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    model_id = ""
    try:
        model_id = (data.get("model") or {}).get("id") or ""
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    session_id = data.get("session_id") or ""
    # ?끸쁾??006 ??**Claude Code ??`cwd` 媛 ?꾨땲??`workspace.current_dir` 濡?以??**
    #   ?ㅼ륫: ??以꾩씠 鍮?臾몄옄?댁쓣 ?댁꽌 design쨌dev쨌cost 以꾩씠 **?꾨? 鍮꾩뿀怨?*,
    #   statusline ???뚰넗???쒕룄/?곹깭/鍮꾩슜??4以??먮뒗 1以?濡쒕쭔 ?섏솕??
    #   ?낃렇?곕뜲 諛붽묑 `except Exception` ???뚯륫???꾠띾쭔 李띿뼱 **?먯씤????蹂댁???*
    #     (議곗슜???대갚 ???ㅽ뙣???뚮━媛 ?놁쑝硫??꾨Т??紐?怨좎튇??쨌 A7).
    #   ?낅몢 ?대쫫??紐⑤몢 蹂몃떎 ???몄뒪?멸? ?대뒓 履쎌쑝濡?以섎룄 ?숈옉?댁빞 ?쒕떎.
    cwd = (data.get("cwd")
           or (data.get("workspace") or {}).get("current_dir")
           or (data.get("workspace") or {}).get("project_dir")
           or os.getcwd() or "")

    # ?끸쁾??006 ??**cwd 瑜?짬.claude 瑜?媛吏???μ냼 猷⑦듃쨩濡??щ┛???뺣낯 1怨?.**
    #   ?ㅼ륫: ???뚯씪?먯꽌 `os.path.join(cwd, ".claude", ??` 媛 **8怨?*?대떎
    #   (logs 쨌 orca.db 횞2 쨌 mcp-status 쨌 mcp-refresh 쨌 refresh ?ㅽ겕由쏀듃 쨌
    #    hardcoded-audit 쨌 state). cwd 媛 ?섏쐞 ?대뜑硫?**洹?8怨녹씠 ?꾨?** 鍮?媛믪씠 ?섏뼱
    #   ?붿옄?맞룰컻諛쑣룸퉬?㈑텺CP 以꾩씠 ?щ씪吏꾨떎 ??洹몃옒??statusline ???뚮줈 3以꾩씠?덈떎.
    #   ?끸쁾??怨녹뵫 怨좎튂硫?諛섎뱶????鍮좎쭊???? ??洹몃옒??**cwd 瑜???踰??뺢퇋??*?쒕떎.
    #   ?낇뙋?뺤? 짬.claude ?대뜑媛 ?덈뒗媛쨩 ???꾨줈?앺듃 援ъ“瑜?吏?대궡吏 ?딅뒗??
    if cwd:
        _p = os.path.abspath(cwd)
        for _ in range(5):
            if os.path.isdir(os.path.join(_p, "plugins")) and os.path.isdir(os.path.join(_p, ".claude")):  # kit ?ㅼ튂 猷⑦듃 湲곗?
                cwd = _p
                break
            _u = os.path.dirname(_p)
            if _u == _p:
                break
            _p = _u

    # ?곹븳 ?뺣낯 = Claude Code 媛 二쇰뒗 context_window.context_window_size. ?놁쓣 ?뚮쭔 ??異붿젙.
    _cw = data.get("context_window") or {}
    if isinstance(_cw.get("context_window_size"), int) and _cw["context_window_size"] > 0:
        limit, exact_model = _cw["context_window_size"], True
    else:
        limit, exact_model = pick_limit(model_id)

    # 2026-10-01: ?대쫫??異붿젙蹂대떎 Claude Code 媛 二쇰뒗 ?ㅼ젣 ?곹븳???뺣낯?대떎.
    #   model.id 媛 "claude-opus-5-5"([1m] ?놁쓬)??1M ?몄뀡??claude-opus-5 ??ぉ??嫄몃젮
    #   200K 濡?湲곕줉?먭퀬, ?쒖옉 吏곹썑 231K ?먯꽌 "116% 利됱떆 compact" ?덉쐞 寃쎈낫媛 ?щ떎.
    try:
        cw = int((data.get("context_window") or {}).get("context_window_size") or 0)
        if cw > 0:
            limit, exact_model = cw, True
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        pass

    # ?닿껐??而⑦뀓?ㅽ듃 ?곹븳??SoT 濡?怨듭쑀 - jsonl ??message.model ? "claude-opus-5" 濡쒕쭔
    # 湲곕줉?섏뼱 "[1m]" ?묐?媛 ?녿떎. hook(inject-compact-reminder)? stdin ??model.id 瑜?    # 蹂????놁뼱 1M ?몄뀡??200K 濡??ㅽ뙋?덈떎 (193K/200K = 93% ?덉쐞 寃쎈낫, 2026-09-05 ?ㅼ륫).
    if exact_model and cwd:
        try:
            import datetime as _dtc
            # 2026-09-10: cwd ??**?몄뀡???꾩옱 ?붾젆?곕━**?? `cd nextjs` ???쒓컙
            #   nextjs/.claude/state/ 媛 ?앷꼈怨? 洹몃젃寃?留뚮뱾?댁쭊 ?됰슧??.claude 媛
            #   8怨녠퉴吏 ?섏뼱 ?덉뿀?? 猷⑦듃 ?쒖떇??李얠븘 ?щ씪媛꾨떎.
            st = os.path.join(_project_root(cwd), ".claude", "state")
            os.makedirs(st, exist_ok=True)
            with open(os.path.join(st, "context-limit.json"), "w", encoding="utf-8") as _f:
                json.dump({"model": model_id, "limit": limit,
                           "ts": _dtc.datetime.now().isoformat(timespec="seconds")}, _f)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            pass

    tokens = 0
    no_usage = True

    if session_id and cwd:
        try:
            proj_dir = cwd_to_proj_dir(cwd)
            jsonl = os.path.join(proj_dir, f"{session_id}.jsonl")
            usage = last_assistant_usage(jsonl)
            if usage:
                tokens = int(
                    (usage.get("input_tokens") or 0)
                    + (usage.get("cache_read_input_tokens") or 0)
                    + (usage.get("cache_creation_input_tokens") or 0)
                )
                no_usage = False
            # ?몄뀡 쨌 ?대쾲 ??쨌 ?ы빐 ?꾩껜 鍮꾩슜 + cache hit + error count
            global _SESSION_COST, _MONTHLY_COST, _YEARLY_COST
            global _CACHE_HIT_RATE, _ERROR_COUNT
            _SESSION_COST = session_cost(jsonl, model_id)
            _MONTHLY_COST = monthly_cost(cwd, model_id)
            _YEARLY_COST = yearly_cost(cwd, model_id)
            _CACHE_HIT_RATE = cache_hit_rate(jsonl)
            _ERROR_COUNT = recent_error_count(cwd)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            pass

    # 3以?援ъ“: [?쒓컖 + ?좏겙 + ?몄뀡] / [二쇨컙 + MCP + ?ъ궗??+ ?섎뱶肄붾뵫 + orca + cache + err] / [AI 鍮꾩슜]
    import datetime as _dt3
    clock = _dt3.datetime.now().strftime("%m/%d %H:%M")
    token_line = render(tokens, limit, exact_model, no_usage)
    # fast 濡쒖쭅?? ?좏겙 context % inject (compact ?꾨컯 ?먯젙)
    if isinstance(data, dict) and limit and tokens:
        data["_ctx_pct"] = min(100.0, tokens / limit * 100.0)
    gauges = extra_gauges(cwd, data) if cwd else {"session": "", "line2": "", "line3": ""}
    SEP = " 쨌 "

    # 2026-10-06 ?ъ슜??吏????以?癒몃━留??대え吏 ?좎? 湲곗? ("洹?湲곗?? 吏耳쒖빞吏").
    #   VS16(U+FE0F) ???꾩슂 ?녿뒗 ?⑥씪 肄붾뱶?ъ씤?몃쭔 ?대떎 (?곕??먮쭏????씠 ?щ씪???뺣젹??源⑥쭚).
    ICONS = {"?좏겙": "?쭬", "?쒕룄": "??, "?붿옄??: "?렓", "媛쒕컻": "?뮲", "?곹깭": "?뱻", "鍮꾩슜": "?뮥"}

    def _row(label: str, body: str) -> str:
        # 癒몃━留??쒖떆??9移??대え吏 2 + 怨듬갚 1 + ?쒓? 理쒕? 6)?쇰줈 留욎땄 ??紐⑤뱺 以??댁슜??媛숈? 移몄뿉???쒖옉
        import unicodedata as _ud
        head = f"{ICONS[label]} {label}" if label in ICONS else label
        w = sum(2 if _ud.east_asian_width(ch) in ("W", "F") else 1 for ch in head)
        # 癒몃━留?援듭? 泥?줉 쨌 援щ텇???뚯깋 (?대え吏 癒몃━留???媛뺤“ ???ъ슜??吏??1006)
        return "\033[1;36m" + head + "\033[0m" + " " * max(0, 9 - w) + " \033[90m??033[0m " + body

    out = [_row("?좏겙", f"{token_line}{SEP}{clock}")]
    lim = [x for x in (gauges.get("session"), gauges.get("week")) if x]
    if lim:
        out.append(_row("?쒕룄", SEP.join(lim)))
    if gauges.get("design"):
        out.append(_row("?붿옄??, gauges["design"]))
    if gauges.get("dev"):
        out.append(_row("媛쒕컻", gauges["dev"]))
    if gauges.get("tail"):
        out.append(_row("?곹깭", SEP.join(gauges["tail"])))
    cost = gauges.get("cost") or ""
    if cost:
        out.append(_row("鍮꾩슜", cost.replace("AI 鍮꾩슜(???꾨줈?앺듃) ", "")))
    print("\n".join(out))


if __name__ == "__main__":
    try:
        main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
        # 理쒗썑 fallback
        try:
            print(EMPTY * WIDTH + " 痢≪젙 ??)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError):
            print("痢≪젙 ??)
    sys.exit(0)

