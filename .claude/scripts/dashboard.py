"""
dashboard — Rich TUI 실시간 대시보드 (Task 35)
orca.db 실시간 시각화 - 세션-워커-토큰-비용-큐
실행: python .claude/scripts/dashboard.py
"""
from __future__ import annotations
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.layout import Layout
    from rich.panel import Panel
except ImportError:
    print("rich 미설치 - python -m pip install rich", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"


def _q(sql, params=()):
    if not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            return c.execute(sql, params).fetchall()
    except Exception:
        return []


def build_layout() -> Layout:
    lay = Layout()
    lay.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    lay["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    return lay


def render_sessions() -> Table:
    t = Table(title="최근 세션 (5)", show_header=True, header_style="bold cyan")
    t.add_column("session")
    t.add_column("turns", justify="right")
    t.add_column("tokens", justify="right")
    t.add_column("종료 시각")
    rows = _q(
        "SELECT session_id, turns, tokens_total, ended_at FROM session_summary ORDER BY ended_at DESC LIMIT 5"
    )
    for sid, turns, tokens, ended in rows:
        t.add_row(sid[:8], str(turns or 0), f"{(tokens or 0):,}", str(ended or ""))
    return t


def render_metrics() -> Table:
    t = Table(title="AI 사용량 (24h)", show_header=True, header_style="bold magenta")
    t.add_column("AI")
    t.add_column("호출", justify="right")
    t.add_column("tokens_in", justify="right")
    t.add_column("tokens_out", justify="right")
    t.add_column("cost", justify="right")
    rows = _q(
        """SELECT ai, COUNT(*), SUM(tokens_in), SUM(tokens_out), SUM(cost_usd)
           FROM metrics WHERE recorded_at >= strftime('%s','now','-1 day')
           GROUP BY ai ORDER BY SUM(cost_usd) DESC"""
    )
    for ai, n, ti, to, cost in rows:
        t.add_row(ai or "?", str(n), f"{ti or 0:,}", f"{to or 0:,}", f"${cost or 0:.4f}")
    return t


def render_solutions() -> Table:
    t = Table(title="재사용 solution TOP 5", show_header=True, header_style="bold green")
    t.add_column("category")
    t.add_column("problem", max_width=40)
    t.add_column("★", justify="right")
    rows = _q(
        "SELECT category, substr(problem,1,60), reusable_score FROM problem_solutions ORDER BY reusable_score DESC, ts DESC LIMIT 5"
    )
    for cat, prob, score in rows:
        t.add_row(cat, prob, str(score))
    return t


def render_tasks() -> Table:
    t = Table(title="대기 tasks", show_header=True, header_style="bold yellow")
    t.add_column("task_id")
    t.add_column("ai")
    t.add_column("status")
    rows = _q(
        "SELECT task_id, ai_assigned, status FROM tasks WHERE status != 'completed' ORDER BY created_at DESC LIMIT 8"
    )
    for tid, ai, st in rows:
        t.add_row(tid[:20], ai or "?", st or "?")
    return t


def render_dashboard() -> Layout:
    lay = build_layout()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lay["header"].update(Panel(f"[bold]Orchestration Kit v1 - Dashboard[/bold]  -  {now}", style="cyan"))
    lay["left"].update(render_sessions())
    lay["right"].update(render_metrics())
    lay["footer"].update(Panel("[green]Ctrl+C[/green] 종료  -  1s refresh", style="dim"))
    return lay


def main() -> int:
    console = Console()
    if "--once" in sys.argv:
        console.print(render_dashboard())
        console.print(render_solutions())
        console.print(render_tasks())
        return 0
    try:
        with Live(render_dashboard(), console=console, refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)
                live.update(render_dashboard())
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
