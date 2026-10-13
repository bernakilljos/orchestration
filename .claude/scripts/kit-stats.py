#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kit-stats ??醫낇빀 ?듦퀎 CLI - Rich ?놁씠 ?쒖닔 python
?ㅽ뻾: python .claude/scripts/kit-stats.py [command]
  command: db - cost - hooks - sessions - solutions - files - audit - all
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
LOG_DIR = ROOT / ".claude" / "logs"


def _q(sql, params=()):
    if not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            return c.execute(sql, params).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return []


def _fmt(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}G"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _fmt_bytes(n: int) -> str:
    if n >= 1024**3:
        return f"{n/1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n/1024**2:.2f} MB"
    if n >= 1024:
        return f"{n/1024:.2f} KB"
    return f"{n} B"


def _bar(current: int, total: int, width: int = 10) -> str:
    """statusline ?ㅽ???- ?댿뻽?믠뼊?믠뼊?믠뼊?믠뼊 20.1% (201K/1.0M)."""
    if total <= 0:
        return "?" * width + " (?쒕룄 ?놁쓬)"
    r = min(current / total, 1.0)
    filled = int(round(r * width))
    filled = min(width, max(0, filled))
    bar = "?? * filled + "?? * (width - filled)
    pct = r * 100
    warn = "  [WARN]" if pct >= 80 else ("  " if pct >= 95 else "")
    return f"{bar} {pct:.1f}%{warn}"


def _bar_line(label: str, current, total, cur_s: str = "", tot_s: str = "") -> str:
    """?댿뻽?믠뼊?믠뼊?믠뼊?믠뼊 20.1% (201K/1.0M) ??statusline 洹몃?濡?"""
    cs = cur_s or _fmt(int(current))
    ts = tot_s or _fmt(int(total))
    return f"  {label:22s} {_bar(current, total, 10)} ({cs}/{ts})"


def _hr(title: str = ""):
    print()
    if title:
        print(f"?? {title} " + "?" * max(0, 60 - len(title)))
    else:
        print("?" * 62)


def stats_db():
    """DB ?⑸웾-?뚯씠釉붾퀎 rows - statusline ?ㅽ???bar."""
    _hr("[STAT] DB (orca.db)")
    if not DB.exists():
        print("  DB ?놁쓬")
        return
    size = DB.stat().st_size
    # ?곹븳 100MB 湲곗? (?ъ슜???ㅼ젙 媛??
    DB_LIMIT = 100 * 1024**2
    print(_bar_line("orca.db ?⑸웾", size, DB_LIMIT, _fmt_bytes(size), _fmt_bytes(DB_LIMIT)))
    tables = _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    rows = []
    for (t,) in tables:
        r = _q(f"SELECT COUNT(*) FROM {t}")
        rows.append((t, r[0][0] if r else 0))
    rows.sort(key=lambda x: -x[1])
    print(f"\n  ?뚯씠釉?{len(tables)}媛?- top 10 rows:")
    max_r = rows[0][1] if rows and rows[0][1] > 0 else 1
    for t, n in rows[:10]:
        print(_bar_line(t, n, max_r, str(n), _fmt(max_r)))
    baks = list(DB.parent.glob("orca.db.bak.*"))
    if baks:
        total_bak = sum(p.stat().st_size for p in baks)
        print(f"\n  諛깆뾽: {len(baks)}媛?- {_fmt_bytes(total_bak)}")


def stats_cost():
    """AI 鍮꾩슜 ?듦퀎 - ?쇨컙-二쇨컙-?붽컙 ?쒕룄 progress bar."""
    _hr(" AI 鍮꾩슜 - ?쒕룄")
    # 3 異??⑷퀎 癒쇱? (bar)
    sums = {}
    for label, since in [("today", "-1 day"), ("week", "-7 days"), ("month", "-30 days")]:
        r = _q(
            f"SELECT COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0)+COALESCE(SUM(tokens_out),0) "
            f"FROM metrics WHERE recorded_at >= strftime('%s','now','{since}')"
        )
        sums[label] = (r[0][0] if r else 0.0, r[0][1] if r else 0)
    # budget ?뚯씠釉?
    b = _q(
        "SELECT COALESCE(today_spent_usd,0), COALESCE(daily_limit_usd,0), "
        "COALESCE(weekly_spent_usd,0), COALESCE(weekly_limit_usd,0), "
        "COALESCE(monthly_spent_usd,0), COALESCE(monthly_limit_usd,0) "
        "FROM budget LIMIT 1"
    )
    if b:
        ds, dl, ws, wl, ms, ml = b[0]
    else:
        ds, dl, ws, wl, ms, ml = 0, 0, 0, 0, 0, 0
    ds = ds or sums["today"][0]
    ws = ws or sums["week"][0]
    ms = ms or sums["month"][0]
    # ?쒕룄 ?놁쑝硫?metrics ?⑷퀎 ?쒓린
    print(_bar_line("?쇱씪 (24h)", ds * 100, (dl or 1) * 100, f"${ds:.4f}", f"${dl:.2f}" if dl else "??))
    print(_bar_line("二쇨컙 (7d)", ws * 100, (wl or 1) * 100, f"${ws:.4f}", f"${wl:.2f}" if wl else "??))
    print(_bar_line("?붽컙 (30d)", ms * 100, (ml or 1) * 100, f"${ms:.4f}", f"${ml:.2f}" if ml else "??))
    # ?몄뀡 (?꾩옱 ?몄뀡)
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid:
        sr = _q(
            "SELECT COALESCE(SUM(cost_usd),0) FROM metrics WHERE session_id=?",
            (sid,),
        )
        if sr:
            sess_spent = sr[0][0]
            print(_bar_line("?꾩옱 ?몄뀡", sess_spent * 100, (dl or 1) * 100, f"${sess_spent:.4f}", f"${dl:.2f}" if dl else "??))
    # ?곸꽭 (紐⑤뜽蹂?24h)
    _hr("紐⑤뜽蹂?(24h)")
    rows = _q(
        "SELECT ai, COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0) "
        "FROM metrics WHERE recorded_at >= strftime('%s','now','-1 day') "
        "GROUP BY ai ORDER BY SUM(cost_usd) DESC"
    )
    if not rows:
        print("  ?곗씠???놁쓬 - route.py --record ?ъ슜 ???먮룞 ???)
        return
    max_c = max(r[2] for r in rows) or 1
    for ai, n, cost, ti, to in rows:
        print(_bar_line(ai, cost * 100, max_c * 100, f"${cost:.4f}", f"${max_c:.4f}"))
        print(f"  {'':22s}    ?몄텧 {n} - tokens {_fmt(ti+to)}")


def stats_hooks():
    """?깅줉??hook ?대깽?몃퀎 媛쒖닔."""
    _hr(" Hooks")
    p = ROOT / ".claude" / "settings.json"
    if not p.exists():
        print("  settings.json ?놁쓬")
        return
    try:
        s = json.load(open(p, encoding="utf-8-sig"))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print(f"  JSON ?뚯떛 ?ㅽ뙣: {e}")
        return
    h = s.get("hooks", {})
    for ev in ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SessionEnd"]:
        lst = h.get(ev, [])
        n = sum(len(g.get("hooks", [])) for g in lst)
        print(f"  {ev:20s} {n:>3d} hooks")
    # ?뚯씪 媛쒖닔
    hd = ROOT / ".claude" / "hooks"
    if hd.exists():
        sh = len(list(hd.glob("*.sh")))
        py = len(list(hd.glob("*.py")))
        print(f"\n  .claude/hooks/ ?뚯씪: sh={sh} py={py} = {sh+py}媛?)


def stats_sessions(top: int = 10):
    """?몄뀡 ?붿빟 top N."""
    _hr(" ?몄뀡 (top {})".format(top))
    rows = _q(
        "SELECT session_id, started_at, ended_at, turns, tokens_total FROM session_summary ORDER BY ended_at DESC LIMIT ?",
        (top,),
    )
    print(f"  {'session':10s} {'turns':>6s} {'tokens':>10s}  {'ended'}")
    for sid, st, en, turns, tokens in rows:
        print(f"  {sid[:8]:10s} {turns or 0:>6d} {_fmt(tokens or 0):>10s}  {en or ''}")
    # 珥앷퀎
    tot = _q("SELECT COUNT(*), SUM(turns), SUM(tokens_total) FROM session_summary")
    if tot:
        n, t, tk = tot[0]
        print(f"\n  ?꾩쟻: ?몄뀡 {n or 0}媛?- turns {_fmt(t or 0)} - tokens {_fmt(tk or 0)}")
    # ?대쾲 ?몄뀡
    sid_now = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid_now:
        r = _q(
            "SELECT COUNT(*), COALESCE(SUM(tokens),0) FROM conversations WHERE session_id=?",
            (sid_now,),
        )
        if r:
            print(f"  ?꾩옱 ?몄뀡 [{sid_now[:8]}]: turns {r[0][0]} - tokens {_fmt(r[0][1])}")


def stats_solutions(top: int = 10):
    """problem_solutions 移댄깉濡쒓렇 - bar ?쒓컖??"""
    _hr("[TIP] ?ъ궗??solutions")
    rows = _q(
        "SELECT category, COUNT(*), COALESCE(AVG(reusable_score),0), COALESCE(SUM(verified),0) "
        "FROM problem_solutions GROUP BY category ORDER BY COUNT(*) DESC"
    )
    if not rows:
        print("  ?곗씠???놁쓬 - save_solution.py auto 濡??먮룞 ???)
        return
    max_n = rows[0][1]
    print(f"\n  移댄뀒怨좊━蹂?(媛쒖닔 bar):")
    for cat, n, avg, ver in rows:
        print(_bar_line(cat or "?", n, max_n, f"{n}媛?, f"{max_n}媛?))
        print(f"  {'':22s}    ??avg:.1f} - 寃利?{ver}")
    print(f"\n  Top {top} (?ъ궗???먯닔 ??:")
    rows = _q(
        "SELECT ts, category, substr(problem,1,50), reusable_score, verified "
        "FROM problem_solutions ORDER BY reusable_score DESC, ts DESC LIMIT ?",
        (top,),
    )
    for ts, cat, prob, score, ver in rows:
        # ?먯닔 bar (0~10)
        bar10 = "?? * (score or 0) + "?? * (10 - (score or 0))
        v = "?? if ver else " "
        print(f"  {bar10} ??score} [{cat or '?':8s}] {v} {prob}")


def stats_files():
    """?뚯씪 audit."""
    _hr(" ?뚯씪 audit")
    rows = _q("SELECT action, COUNT(*) FROM file_audit GROUP BY action")
    for a, n in rows:
        print(f"  {a:10s} {n:>6d}")
    # ?ㅻ뒛 留뚮뱺 ?뚯씪
    rows = _q(
        "SELECT path, ts FROM file_audit WHERE ts >= datetime('now','-1 day') ORDER BY ts DESC LIMIT 10"
    )
    if rows:
        print("\n  理쒓렐 24h 蹂寃??뚯씪:")
        for path, ts in rows:
            print(f"    {ts}  {path[-70:]}")


def stats_kit():
    """kit ?먯껜 ?듦퀎."""
    _hr("[FIX] kit ?먯궛")
    for name, path in [
        ("rules", ROOT / ".claude" / "rules"),
        ("skills", ROOT / ".claude" / "skills"),
        ("hooks", ROOT / ".claude" / "hooks"),
        ("scripts", ROOT / ".claude" / "scripts"),
        ("agents", ROOT / ".claude" / "agents"),
        ("commands", ROOT / ".claude" / "commands"),
    ]:
        if path.exists():
            n = len(list(path.glob("*.md"))) + len(list(path.glob("*.sh"))) + len(list(path.glob("*.py")))
            print(f"  {name:12s} {n:>4d}")
    # plugins
    pl = ROOT / "plugins"
    if pl.exists():
        n = sum(1 for p in pl.iterdir() if p.is_dir() and not p.name.startswith("_"))
        print(f"  {'plugins':12s} {n:>4d}")


def stats_logs():
    """濡쒓렇 ?뚯씪 ?ш린 - bar ?쒓컖??"""
    _hr(" 濡쒓렇 ?뚯씪 (top 15)")
    if not LOG_DIR.exists():
        print("  濡쒓렇 ?대뜑 ?놁쓬")
        return
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: -p.stat().st_size)[:15]
    if not logs:
        print("  濡쒓렇 ?놁쓬")
        return
    max_s = logs[0].stat().st_size or 1
    # 100MB 珥덇낵 = ?꾪뿕
    for p in logs:
        s = p.stat().st_size
        marker = " " if s > 100 * 1024**2 else (" [WARN]" if s > 10 * 1024**2 else "")
        print(_bar_line(p.name[:22], s, max_s, _fmt_bytes(s), _fmt_bytes(max_s)) + marker)
    print(f"\n  ?⑷퀎: {_fmt_bytes(sum(p.stat().st_size for p in logs))}")


def stats_mcp():
    """MCP ?곹깭."""
    _hr("[MCP] MCP")
    home = Path.home()
    # claude-mem
    mem = home / ".claude-mem"
    if mem.exists():
        n = sum(p.stat().st_size for p in mem.rglob("*") if p.is_file())
        print(f"  claude-mem: {_fmt_bytes(n)} - {mem}")
    else:
        print("  claude-mem: ?ㅼ튂-????놁쓬")
    # ?깅줉??MCP servers (?꾩뿭 ~/.claude.json)
    cj = home / ".claude.json"
    if cj.exists():
        try:
            d = json.load(open(cj, encoding="utf-8"))
            ms = d.get("mcpServers") or {}
            print(f"  ?깅줉 MCP {len(ms)}媛? {', '.join(ms.keys())}")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass


def stats_all():
    print(f"\n[TGT] orchestration_v1 kit stats - {datetime.now():%Y-%m-%d %H:%M:%S}")
    stats_kit()
    stats_db()
    stats_hooks()
    stats_cost()
    stats_sessions(5)
    stats_solutions(5)
    stats_files()
    stats_mcp()
    stats_logs()
    _hr()


COMMANDS = {
    "db": stats_db,
    "cost": stats_cost,
    "hooks": stats_hooks,
    "sessions": lambda: stats_sessions(10),
    "solutions": lambda: stats_solutions(10),
    "files": stats_files,
    "kit": stats_kit,
    "logs": stats_logs,
    "mcp": stats_mcp,
    "all": stats_all,
}


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    fn = COMMANDS.get(cmd)
    if not fn:
        print(f"usage: kit-stats.py [{'|'.join(COMMANDS)}]")
        return 1
    fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())

