#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kit-dashboard — orca.db · MCP · cost · 재사용 점수 시각 HTML dashboard.
실행: python .claude/scripts/kit-dashboard.py [--open]
  --open : 완료 후 브라우저 자동 열기 (Windows: start · Mac: open · Linux: xdg-open)
"""
from __future__ import annotations
import json
import os
import sqlite3
import subprocess
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
OUT_HTML = ROOT / ".claude" / "state" / "dashboard.html"


def _q(sql, params=()):
    if not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            return c.execute(sql, params).fetchall()
    except Exception:
        return []


def _fmt_bytes(n: int) -> str:
    if n >= 1024**3:
        return f"{n/1024**3:.2f} GB"
    if n >= 1024**2:
        return f"{n/1024**2:.2f} MB"
    if n >= 1024:
        return f"{n/1024:.2f} KB"
    return f"{n} B"


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _card(title, body, extra=""):
    return f'''<div class="card {extra}">
  <div class="card-title">{title}</div>
  <div class="card-body">{body}</div>
</div>'''


def sec_kit():
    counts = {}
    for name, path in [
        ("rules", ".claude/rules"),
        ("skills", ".claude/skills"),
        ("hooks", ".claude/hooks"),
        ("scripts", ".claude/scripts"),
        ("agents", ".claude/agents"),
        ("commands", ".claude/commands"),
    ]:
        p = ROOT / path
        counts[name] = (
            len(list(p.glob("*.md")))
            + len(list(p.glob("*.sh")))
            + len(list(p.glob("*.py")))
            if p.exists()
            else 0
        )
    pl = ROOT / "plugins"
    counts["plugins"] = (
        sum(1 for p in pl.iterdir() if p.is_dir() and not p.name.startswith("_"))
        if pl.exists()
        else 0
    )
    items = "".join(
        f'<div class="stat"><div class="num">{v}</div><div class="lbl">{k}</div></div>'
        for k, v in counts.items()
    )
    return _card("🔧 Kit 자산", f'<div class="stat-grid">{items}</div>')


def sec_db():
    if not DB.exists():
        return _card("📊 DB", "<p>DB 없음</p>")
    size = DB.stat().st_size
    tables = _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    rows = []
    total_rows = 0
    for (t,) in tables:
        n = _q(f"SELECT COUNT(*) FROM {t}")
        n = n[0][0] if n else 0
        total_rows += n
        rows.append((t, n))
    rows.sort(key=lambda x: -x[1])
    top = rows[:12]
    max_r = top[0][1] if top and top[0][1] > 0 else 1
    lines = ""
    for t, n in top:
        pct = int(n / max_r * 100)
        lines += f'''<div class="row">
  <span class="row-label">{t}</span>
  <div class="row-bar"><div class="row-fill" style="width:{pct}%"></div></div>
  <span class="row-num">{_fmt(n)}</span>
</div>'''
    baks = list(DB.parent.glob("orca.db.bak.*"))
    bak_info = (
        f"<p class='sub'>백업 {len(baks)}개 · {_fmt_bytes(sum(p.stat().st_size for p in baks))}</p>"
        if baks
        else ""
    )
    body = f'''<p class="big">{_fmt_bytes(size)} · 테이블 {len(tables)}개 · rows {_fmt(total_rows)}</p>
{lines}
{bak_info}'''
    return _card("📊 orca.db", body, "wide")


def sec_cost():
    rows_24h = _q(
        "SELECT ai, COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0) "
        "FROM metrics WHERE recorded_at >= strftime('%s','now','-1 day') "
        "GROUP BY ai ORDER BY SUM(cost_usd) DESC"
    )
    rows_7d = _q(
        "SELECT ai, COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0) "
        "FROM metrics WHERE recorded_at >= strftime('%s','now','-7 days') "
        "GROUP BY ai ORDER BY SUM(cost_usd) DESC"
    )
    b = _q("SELECT COALESCE(today_spent_usd,0), COALESCE(daily_limit_usd,0) FROM budget LIMIT 1")
    spent, limit = (b[0][0], b[0][1]) if b else (0, 0)
    lim_txt = f"${limit:.2f}" if limit else "상한 없음"
    bar_pct = int(min(spent / limit, 1.0) * 100) if limit > 0 else 0

    def tbl(rows, label):
        if not rows:
            return f'<p class="sub">{label}: 데이터 없음</p>'
        html = f"<h4>{label}</h4><table><tr><th>모델</th><th>호출</th><th>토큰</th><th>비용</th></tr>"
        total = 0.0
        for ai, n, cost, ti, to in rows:
            total += cost
            html += f"<tr><td>{ai}</td><td>{n}</td><td>{_fmt(ti+to)}</td><td>${cost:.4f}</td></tr>"
        html += f"<tr class='tot'><td colspan=3>합계</td><td>${total:.4f}</td></tr></table>"
        return html

    budget_html = (
        f'''<div class="budget">
  <p>일일 예산 <b>${spent:.4f}</b> / {lim_txt}</p>
  <div class="row-bar big"><div class="row-fill" style="width:{bar_pct}%;background:{'#e74c3c' if bar_pct>80 else '#3498db'}"></div></div>
</div>'''
    )
    return _card("💰 AI 비용", budget_html + tbl(rows_24h, "24h") + tbl(rows_7d, "7d"), "wide")


def sec_mcp():
    home = Path.home()
    cj = home / ".claude.json"
    servers = []
    if cj.exists():
        try:
            d = json.load(open(cj, encoding="utf-8"))
            ms = d.get("mcpServers") or {}
            for name, cfg in ms.items():
                cmd = cfg.get("command", "")
                url = cfg.get("url", "")
                status = "🟢 등록"
                servers.append((name, cmd or url or "-", status))
        except Exception as e:
            servers.append(("(파싱 실패)", str(e)[:60], "🔴"))
    # claude-mem
    mem = home / ".claude-mem"
    mem_info = ""
    if mem.exists():
        try:
            n = sum(p.stat().st_size for p in mem.rglob("*") if p.is_file())
            mem_info = f"<p class='sub'>claude-mem: {_fmt_bytes(n)}</p>"
        except Exception:
            pass
    # Headroom proxy 헬스체크
    proxy_status = "🔴 정지"
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8787/", timeout=1)
        proxy_status = "🟢 실행"
    except Exception:
        pass
    rows = "".join(
        f"<tr><td>{n}</td><td class='small'>{c[:60]}</td><td>{s}</td></tr>" for n, c, s in servers
    )
    body = f'''<p class="sub">Headroom proxy (127.0.0.1:8787): {proxy_status}</p>
{mem_info}
<table><tr><th>MCP</th><th>command/url</th><th>상태</th></tr>{rows}</table>'''
    return _card(f"🔌 MCP ({len(servers)}개)", body, "wide")


def sec_solutions():
    rows = _q(
        "SELECT category, COUNT(*), COALESCE(AVG(reusable_score),0), COALESCE(SUM(verified),0) "
        "FROM problem_solutions GROUP BY category ORDER BY COUNT(*) DESC"
    )
    if not rows:
        return _card("💡 재사용 solutions", "<p>데이터 없음</p>")
    total_n = sum(r[1] for r in rows)
    cat_html = "".join(
        f'''<div class="row">
  <span class="row-label">{cat or '?'}</span>
  <div class="row-bar"><div class="row-fill" style="width:{int(n/rows[0][1]*100)}%"></div></div>
  <span class="row-num">{n} · ★{avg:.1f} · ✓{ver}</span>
</div>'''
        for cat, n, avg, ver in rows
    )
    # Top solutions
    top = _q(
        "SELECT category, substr(problem,1,60), reusable_score, verified, ts "
        "FROM problem_solutions ORDER BY reusable_score DESC, ts DESC LIMIT 8"
    )
    top_html = "".join(
        f'''<div class="sol">
  <span class="score score-{s}">★{s}</span>
  <span class="cat">{c or '?'}</span>
  {'✓' if v else ''}
  <span class="prob">{p}</span>
</div>'''
        for c, p, s, v, ts in top
    )
    body = f'''<p class="big">총 {total_n}개</p>
<h4>카테고리별</h4>{cat_html}
<h4>Top 재사용 점수</h4>{top_html}'''
    return _card("💡 재사용 solutions (problem_solutions)", body, "wide")


def sec_hooks():
    p = ROOT / ".claude" / "settings.json"
    if not p.exists():
        return _card("🪝 Hooks", "<p>없음</p>")
    try:
        s = json.load(open(p, encoding="utf-8-sig"))
    except Exception as e:
        return _card("🪝 Hooks", f"<p>파싱 실패: {e}</p>")
    h = s.get("hooks", {})
    events = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd", "PreCompact"]
    items = ""
    for ev in events:
        lst = h.get(ev, [])
        n = sum(len(g.get("hooks", [])) for g in lst)
        items += f'<div class="stat"><div class="num">{n}</div><div class="lbl">{ev}</div></div>'
    return _card("🪝 Hooks", f'<div class="stat-grid">{items}</div>')


def sec_sessions():
    rows = _q(
        "SELECT session_id, started_at, ended_at, COALESCE(turns,0), COALESCE(tokens_total,0) "
        "FROM session_summary ORDER BY ended_at DESC LIMIT 10"
    )
    if not rows:
        return _card("💬 세션", "<p>없음</p>")
    html = "<table><tr><th>세션</th><th>turns</th><th>tokens</th><th>종료</th></tr>"
    for sid, st, en, turns, tokens in rows:
        html += f"<tr><td>{sid[:10]}</td><td>{turns}</td><td>{_fmt(tokens)}</td><td>{en or ''}</td></tr>"
    html += "</table>"
    tot = _q(
        "SELECT COUNT(*), COALESCE(SUM(turns),0), COALESCE(SUM(tokens_total),0) FROM session_summary"
    )
    if tot:
        n, t, tk = tot[0]
        html = f'<p class="big">누적 {n}세션 · turns {_fmt(t)} · tokens {_fmt(tk)}</p>' + html
    return _card("💬 세션 히스토리", html, "wide")


def sec_logs():
    if not LOG_DIR.exists():
        return _card("📄 로그", "<p>없음</p>")
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: -p.stat().st_size)[:8]
    if not logs:
        return _card("📄 로그", "<p>없음</p>")
    max_s = logs[0].stat().st_size
    rows_html = ""
    for p in logs:
        s = p.stat().st_size
        pct = int(s / max_s * 100) if max_s else 0
        color = "#e74c3c" if s > 100 * 1024**2 else "#3498db"
        rows_html += f'''<div class="row">
  <span class="row-label">{p.name}</span>
  <div class="row-bar"><div class="row-fill" style="width:{pct}%;background:{color}"></div></div>
  <span class="row-num">{_fmt_bytes(s)}</span>
</div>'''
    return _card("📄 로그 top 8 (크기)", rows_html)


CSS = """
* {box-sizing:border-box}
body {
  font-family: -apple-system, Segoe UI, Malgun Gothic, sans-serif;
  margin:0; padding:24px; background:#0f172a; color:#e2e8f0;
}
h1 {margin:0 0 8px; font-size:28px}
.time {color:#94a3b8; font-size:14px; margin-bottom:24px}
.grid {display:grid; grid-template-columns:repeat(auto-fill, minmax(340px, 1fr)); gap:16px}
.card {
  background:#1e293b; border-radius:12px; padding:20px;
  box-shadow:0 4px 12px rgba(0,0,0,.2); border:1px solid #334155;
}
.card.wide {grid-column: span 2}
@media (max-width:768px){ .card.wide {grid-column: span 1} }
.card-title {font-size:15px; font-weight:600; color:#f1f5f9; margin-bottom:12px}
.card-body {font-size:14px}
.stat-grid {display:grid; grid-template-columns:repeat(auto-fill, minmax(80px, 1fr)); gap:8px}
.stat {background:#0f172a; padding:12px 8px; border-radius:8px; text-align:center}
.stat .num {font-size:24px; font-weight:700; color:#60a5fa}
.stat .lbl {font-size:11px; color:#94a3b8; margin-top:4px}
.big {font-size:18px; font-weight:600; margin:0 0 12px; color:#f1f5f9}
.sub {font-size:12px; color:#94a3b8; margin:4px 0}
.row {display:flex; align-items:center; gap:8px; margin:4px 0; font-size:13px}
.row-label {flex:0 0 130px; color:#cbd5e1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.row-bar {flex:1; height:8px; background:#0f172a; border-radius:4px; overflow:hidden}
.row-bar.big {height:12px}
.row-fill {height:100%; background:#3498db; border-radius:4px}
.row-num {flex:0 0 auto; color:#e2e8f0; font-family: monospace; font-size:12px; min-width:60px; text-align:right}
table {width:100%; border-collapse:collapse; margin:8px 0; font-size:12px}
th, td {padding:6px 8px; text-align:left; border-bottom:1px solid #334155}
th {color:#94a3b8; font-weight:500}
.tot {font-weight:600; background:#0f172a}
.small {font-family:monospace; font-size:11px; color:#94a3b8}
.budget {margin-bottom:12px}
h4 {margin:16px 0 6px; font-size:12px; color:#94a3b8; text-transform:uppercase; letter-spacing:.5px}
.sol {padding:6px 0; border-bottom:1px solid #2d3b52; font-size:12px}
.sol .score {display:inline-block; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:6px; font-weight:600}
.score-10, .score-9, .score-8 {background:#10b981; color:white}
.score-7, .score-6, .score-5 {background:#3498db; color:white}
.score-4, .score-3, .score-2, .score-1, .score-0 {background:#64748b; color:white}
.sol .cat {color:#60a5fa; font-family:monospace; margin-right:6px}
.sol .prob {color:#cbd5e1}
footer {margin-top:24px; text-align:center; color:#64748b; font-size:11px}
"""


def build():
    sections = [
        sec_kit(),
        sec_hooks(),
        sec_db(),
        sec_cost(),
        sec_mcp(),
        sec_solutions(),
        sec_sessions(),
        sec_logs(),
    ]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>orchestration_v1 · Kit Dashboard</title>
<style>{CSS}</style>
<meta http-equiv="refresh" content="60">
</head>
<body>
<h1>🎯 orchestration_v1 kit dashboard</h1>
<div class="time">최신 갱신: {now} · 60초마다 자동 갱신 · 재실행: <code>python .claude/scripts/kit-dashboard.py --open</code></div>
<div class="grid">
{''.join(sections)}
</div>
<footer>대상: {ROOT} · orca.db {_fmt_bytes(DB.stat().st_size) if DB.exists() else 'N/A'}</footer>
</body>
</html>"""
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    return OUT_HTML


def open_browser(path: Path):
    if sys.platform == "win32":
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def main():
    out = build()
    print(f"✅ dashboard 생성: {out}")
    if "--open" in sys.argv or "-o" in sys.argv:
        open_browser(out)
        print("🌐 브라우저 열기 완료")
    else:
        print("💡 브라우저로 열려면: --open 또는 파일 더블클릭")


if __name__ == "__main__":
    main()
