#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kit-stats — 종합 통계 CLI - Rich 없이 순수 python
실행: python .claude/scripts/kit-stats.py [command]
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
except Exception:
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
    except Exception:
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
    """statusline 스타일 - ██▒▒▒▒▒▒▒▒ 20.1% (201K/1.0M)."""
    if total <= 0:
        return "─" * width + " (한도 없음)"
    r = min(current / total, 1.0)
    filled = int(round(r * width))
    filled = min(width, max(0, filled))
    bar = "█" * filled + "▒" * (width - filled)
    pct = r * 100
    warn = "  [WARN]" if pct >= 80 else ("  " if pct >= 95 else "")
    return f"{bar} {pct:.1f}%{warn}"


def _bar_line(label: str, current, total, cur_s: str = "", tot_s: str = "") -> str:
    """██▒▒▒▒▒▒▒▒ 20.1% (201K/1.0M) — statusline 그대로."""
    cs = cur_s or _fmt(int(current))
    ts = tot_s or _fmt(int(total))
    return f"  {label:22s} {_bar(current, total, 10)} ({cs}/{ts})"


def _hr(title: str = ""):
    print()
    if title:
        print(f"── {title} " + "─" * max(0, 60 - len(title)))
    else:
        print("─" * 62)


def stats_db():
    """DB 용량-테이블별 rows - statusline 스타일 bar."""
    _hr("[STAT] DB (orca.db)")
    if not DB.exists():
        print("  DB 없음")
        return
    size = DB.stat().st_size
    # 상한 100MB 기준 (사용자 설정 가능)
    DB_LIMIT = 100 * 1024**2
    print(_bar_line("orca.db 용량", size, DB_LIMIT, _fmt_bytes(size), _fmt_bytes(DB_LIMIT)))
    tables = _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    rows = []
    for (t,) in tables:
        r = _q(f"SELECT COUNT(*) FROM {t}")
        rows.append((t, r[0][0] if r else 0))
    rows.sort(key=lambda x: -x[1])
    print(f"\n  테이블 {len(tables)}개 - top 10 rows:")
    max_r = rows[0][1] if rows and rows[0][1] > 0 else 1
    for t, n in rows[:10]:
        print(_bar_line(t, n, max_r, str(n), _fmt(max_r)))
    baks = list(DB.parent.glob("orca.db.bak.*"))
    if baks:
        total_bak = sum(p.stat().st_size for p in baks)
        print(f"\n  백업: {len(baks)}개 - {_fmt_bytes(total_bak)}")


def stats_cost():
    """AI 비용 통계 - 일간-주간-월간 한도 progress bar."""
    _hr(" AI 비용 - 한도")
    # 3 축 합계 먼저 (bar)
    sums = {}
    for label, since in [("today", "-1 day"), ("week", "-7 days"), ("month", "-30 days")]:
        r = _q(
            f"SELECT COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0)+COALESCE(SUM(tokens_out),0) "
            f"FROM metrics WHERE recorded_at >= strftime('%s','now','{since}')"
        )
        sums[label] = (r[0][0] if r else 0.0, r[0][1] if r else 0)
    # budget 테이블
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
    # 한도 없으면 metrics 합계 표기
    print(_bar_line("일일 (24h)", ds * 100, (dl or 1) * 100, f"${ds:.4f}", f"${dl:.2f}" if dl else "∞"))
    print(_bar_line("주간 (7d)", ws * 100, (wl or 1) * 100, f"${ws:.4f}", f"${wl:.2f}" if wl else "∞"))
    print(_bar_line("월간 (30d)", ms * 100, (ml or 1) * 100, f"${ms:.4f}", f"${ml:.2f}" if ml else "∞"))
    # 세션 (현재 세션)
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid:
        sr = _q(
            "SELECT COALESCE(SUM(cost_usd),0) FROM metrics WHERE session_id=?",
            (sid,),
        )
        if sr:
            sess_spent = sr[0][0]
            print(_bar_line("현재 세션", sess_spent * 100, (dl or 1) * 100, f"${sess_spent:.4f}", f"${dl:.2f}" if dl else "∞"))
    # 상세 (모델별 24h)
    _hr("모델별 (24h)")
    rows = _q(
        "SELECT ai, COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0) "
        "FROM metrics WHERE recorded_at >= strftime('%s','now','-1 day') "
        "GROUP BY ai ORDER BY SUM(cost_usd) DESC"
    )
    if not rows:
        print("  데이터 없음 - route.py --record 사용 시 자동 저장")
        return
    max_c = max(r[2] for r in rows) or 1
    for ai, n, cost, ti, to in rows:
        print(_bar_line(ai, cost * 100, max_c * 100, f"${cost:.4f}", f"${max_c:.4f}"))
        print(f"  {'':22s}    호출 {n} - tokens {_fmt(ti+to)}")


def stats_hooks():
    """등록된 hook 이벤트별 개수."""
    _hr(" Hooks")
    p = ROOT / ".claude" / "settings.json"
    if not p.exists():
        print("  settings.json 없음")
        return
    try:
        s = json.load(open(p, encoding="utf-8-sig"))
    except Exception as e:
        print(f"  JSON 파싱 실패: {e}")
        return
    h = s.get("hooks", {})
    for ev in ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SessionEnd"]:
        lst = h.get(ev, [])
        n = sum(len(g.get("hooks", [])) for g in lst)
        print(f"  {ev:20s} {n:>3d} hooks")
    # 파일 개수
    hd = ROOT / ".claude" / "hooks"
    if hd.exists():
        sh = len(list(hd.glob("*.sh")))
        py = len(list(hd.glob("*.py")))
        print(f"\n  .claude/hooks/ 파일: sh={sh} py={py} = {sh+py}개")


def stats_sessions(top: int = 10):
    """세션 요약 top N."""
    _hr(" 세션 (top {})".format(top))
    rows = _q(
        "SELECT session_id, started_at, ended_at, turns, tokens_total FROM session_summary ORDER BY ended_at DESC LIMIT ?",
        (top,),
    )
    print(f"  {'session':10s} {'turns':>6s} {'tokens':>10s}  {'ended'}")
    for sid, st, en, turns, tokens in rows:
        print(f"  {sid[:8]:10s} {turns or 0:>6d} {_fmt(tokens or 0):>10s}  {en or ''}")
    # 총계
    tot = _q("SELECT COUNT(*), SUM(turns), SUM(tokens_total) FROM session_summary")
    if tot:
        n, t, tk = tot[0]
        print(f"\n  누적: 세션 {n or 0}개 - turns {_fmt(t or 0)} - tokens {_fmt(tk or 0)}")
    # 이번 세션
    sid_now = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid_now:
        r = _q(
            "SELECT COUNT(*), COALESCE(SUM(tokens),0) FROM conversations WHERE session_id=?",
            (sid_now,),
        )
        if r:
            print(f"  현재 세션 [{sid_now[:8]}]: turns {r[0][0]} - tokens {_fmt(r[0][1])}")


def stats_solutions(top: int = 10):
    """problem_solutions 카탈로그 - bar 시각화."""
    _hr("[TIP] 재사용 solutions")
    rows = _q(
        "SELECT category, COUNT(*), COALESCE(AVG(reusable_score),0), COALESCE(SUM(verified),0) "
        "FROM problem_solutions GROUP BY category ORDER BY COUNT(*) DESC"
    )
    if not rows:
        print("  데이터 없음 - save_solution.py auto 로 자동 저장")
        return
    max_n = rows[0][1]
    print(f"\n  카테고리별 (개수 bar):")
    for cat, n, avg, ver in rows:
        print(_bar_line(cat or "?", n, max_n, f"{n}개", f"{max_n}개"))
        print(f"  {'':22s}    ★{avg:.1f} - 검증 {ver}")
    print(f"\n  Top {top} (재사용 점수 순):")
    rows = _q(
        "SELECT ts, category, substr(problem,1,50), reusable_score, verified "
        "FROM problem_solutions ORDER BY reusable_score DESC, ts DESC LIMIT ?",
        (top,),
    )
    for ts, cat, prob, score, ver in rows:
        # 점수 bar (0~10)
        bar10 = "█" * (score or 0) + "▒" * (10 - (score or 0))
        v = "✓" if ver else " "
        print(f"  {bar10} ★{score} [{cat or '?':8s}] {v} {prob}")


def stats_files():
    """파일 audit."""
    _hr(" 파일 audit")
    rows = _q("SELECT action, COUNT(*) FROM file_audit GROUP BY action")
    for a, n in rows:
        print(f"  {a:10s} {n:>6d}")
    # 오늘 만든 파일
    rows = _q(
        "SELECT path, ts FROM file_audit WHERE ts >= datetime('now','-1 day') ORDER BY ts DESC LIMIT 10"
    )
    if rows:
        print("\n  최근 24h 변경 파일:")
        for path, ts in rows:
            print(f"    {ts}  {path[-70:]}")


def stats_kit():
    """kit 자체 통계."""
    _hr("[FIX] kit 자산")
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
    """로그 파일 크기 - bar 시각화."""
    _hr(" 로그 파일 (top 15)")
    if not LOG_DIR.exists():
        print("  로그 폴더 없음")
        return
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: -p.stat().st_size)[:15]
    if not logs:
        print("  로그 없음")
        return
    max_s = logs[0].stat().st_size or 1
    # 100MB 초과 = 위험
    for p in logs:
        s = p.stat().st_size
        marker = " " if s > 100 * 1024**2 else (" [WARN]" if s > 10 * 1024**2 else "")
        print(_bar_line(p.name[:22], s, max_s, _fmt_bytes(s), _fmt_bytes(max_s)) + marker)
    print(f"\n  합계: {_fmt_bytes(sum(p.stat().st_size for p in logs))}")


def stats_mcp():
    """MCP 상태."""
    _hr("[MCP] MCP")
    home = Path.home()
    # claude-mem
    mem = home / ".claude-mem"
    if mem.exists():
        n = sum(p.stat().st_size for p in mem.rglob("*") if p.is_file())
        print(f"  claude-mem: {_fmt_bytes(n)} - {mem}")
    else:
        print("  claude-mem: 설치-저장 없음")
    # 등록된 MCP servers (전역 ~/.claude.json)
    cj = home / ".claude.json"
    if cj.exists():
        try:
            d = json.load(open(cj, encoding="utf-8"))
            ms = d.get("mcpServers") or {}
            print(f"  등록 MCP {len(ms)}개: {', '.join(ms.keys())}")
        except Exception:
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
