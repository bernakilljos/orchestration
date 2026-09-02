#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kit-stats — 종합 통계 CLI · Rich 없이 순수 python
실행: python .claude/scripts/kit-stats.py [command]
  command: db · cost · hooks · sessions · solutions · files · audit · all
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


def _bar(current: int, total: int, width: int = 20) -> str:
    if total <= 0:
        return "─" * width
    r = min(current / total, 1.0)
    filled = int(r * width)
    return "█" * filled + "▒" * (width - filled)


def _hr(title: str = ""):
    print()
    if title:
        print(f"── {title} " + "─" * max(0, 60 - len(title)))
    else:
        print("─" * 62)


def stats_db():
    """DB 용량·테이블별 rows."""
    _hr("📊 DB (orca.db)")
    if not DB.exists():
        print("  DB 없음")
        return
    size = DB.stat().st_size
    print(f"  파일: {DB} · {_fmt_bytes(size)}")
    tables = _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    print(f"  테이블 {len(tables)}개:")
    for (t,) in tables:
        n = _q(f"SELECT COUNT(*) FROM {t}")[0][0]
        print(f"    {t:30s} {_fmt(n):>10s} rows")
    # 백업
    baks = list(DB.parent.glob("orca.db.bak.*"))
    if baks:
        total_bak = sum(p.stat().st_size for p in baks)
        print(f"  백업: {len(baks)}개 · {_fmt_bytes(total_bak)}")


def stats_cost():
    """AI 비용 통계 (24h·7d·30d)."""
    _hr("💰 AI 비용")
    for label, since in [("오늘 (24h)", "-1 day"), ("이번 주 (7d)", "-7 days"), ("이번 달 (30d)", "-30 days")]:
        rows = _q(
            f"SELECT ai, COUNT(*), SUM(cost_usd), SUM(tokens_in), SUM(tokens_out) "
            f"FROM metrics WHERE recorded_at >= strftime('%s','now','{since}') "
            f"GROUP BY ai ORDER BY SUM(cost_usd) DESC"
        )
        print(f"\n  {label}:")
        total = 0.0
        for ai, n, cost, ti, to in rows:
            c = cost or 0.0
            total += c
            print(f"    {ai:12s} 호출:{n:>5d} tokens:{_fmt((ti or 0)+(to or 0)):>8s} cost:${c:.4f}")
        print(f"    {'합계':12s} {'':>26s} ${total:.4f}")
    # 예산
    b = _q("SELECT today_spent_usd, daily_limit_usd FROM budget LIMIT 1")
    if b:
        spent, lim = b[0]
        if lim:
            print(f"\n  일일 예산: {_bar(int((spent or 0)*100), int(lim*100), 20)} ${spent or 0:.4f}/${lim:.2f}")
        else:
            print(f"\n  일일 사용: ${spent or 0:.4f} (상한 없음)")


def stats_hooks():
    """등록된 hook 이벤트별 개수."""
    _hr("🪝 Hooks")
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
    _hr("💬 세션 (top {})".format(top))
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
        print(f"\n  누적: 세션 {n or 0}개 · turns {_fmt(t or 0)} · tokens {_fmt(tk or 0)}")
    # 이번 세션
    sid_now = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if sid_now:
        r = _q(
            "SELECT COUNT(*), COALESCE(SUM(tokens),0) FROM conversations WHERE session_id=?",
            (sid_now,),
        )
        if r:
            print(f"  현재 세션 [{sid_now[:8]}]: turns {r[0][0]} · tokens {_fmt(r[0][1])}")


def stats_solutions(top: int = 10):
    """problem_solutions 카탈로그."""
    _hr("💡 재사용 solutions (top {})".format(top))
    rows = _q(
        "SELECT category, COUNT(*), AVG(reusable_score), SUM(verified) FROM problem_solutions GROUP BY category ORDER BY COUNT(*) DESC"
    )
    print("  카테고리별:")
    print(f"  {'category':15s} {'개수':>6s} {'평균★':>6s} {'검증':>6s}")
    for cat, n, avg, ver in rows:
        print(f"  {cat or '?':15s} {n:>6d} {avg or 0:>6.1f} {ver or 0:>6d}")
    print(f"\n  Top {top} (재사용 점수 순):")
    rows = _q(
        "SELECT ts, category, substr(problem,1,50), reusable_score, verified FROM problem_solutions ORDER BY reusable_score DESC, ts DESC LIMIT ?",
        (top,),
    )
    for ts, cat, prob, score, ver in rows:
        v = "✓" if ver else " "
        print(f"  [{cat:8s} ★{score}] {v} {prob}")


def stats_files():
    """파일 audit."""
    _hr("📁 파일 audit")
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
    _hr("🔧 kit 자산")
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
    """로그 파일 크기."""
    _hr("📄 로그 파일")
    if not LOG_DIR.exists():
        print("  로그 폴더 없음")
        return
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: -p.stat().st_size)[:15]
    total = 0
    for p in logs:
        s = p.stat().st_size
        total += s
        print(f"  {_fmt_bytes(s):>10s}  {p.name}")
    print(f"\n  Top 15 합계: {_fmt_bytes(total)}")


def stats_mcp():
    """MCP 상태."""
    _hr("🔌 MCP")
    home = Path.home()
    # claude-mem
    mem = home / ".claude-mem"
    if mem.exists():
        n = sum(p.stat().st_size for p in mem.rglob("*") if p.is_file())
        print(f"  claude-mem: {_fmt_bytes(n)} · {mem}")
    else:
        print("  claude-mem: 설치·저장 없음")
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
    print(f"\n🎯 orchestration_v1 kit stats · {datetime.now():%Y-%m-%d %H:%M:%S}")
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
