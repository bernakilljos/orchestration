"""
statusline_context — 매 turn 대상·토큰·진행률·최근 활동 표시
근거: 2026-09-02 사용자 지적 · 다른 CLI progress bar 예시 · 우리 kit 통합
호출: settings.json statusLine.command
"""
from __future__ import annotations
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def _find_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in [p.parent, *p.parents]:
        if (parent / ".claude").is_dir() and (parent / "plugins").is_dir():
            return parent
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))


ROOT = _find_project_root()
DB = ROOT / ".claude" / "state" / "orca.db"


def _q(sql: str, params: tuple = ()) -> list:
    if not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            return c.execute(sql, params).fetchall()
    except Exception:
        return []


def _session_id() -> str:
    return os.environ.get("CLAUDE_CODE_SESSION_ID", "")


def _bar(current: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return "─" * width
    ratio = min(current / total, 1.0)
    filled = int(ratio * width)
    return "█" * filled + "▒" * (width - filled)


def _fmt_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def _fmt_cost(usd: float) -> str:
    if usd >= 1.0:
        return f"${usd:.2f}"
    if usd >= 0.01:
        return f"${usd:.3f}"
    return f"${usd:.4f}"


def _target() -> str:
    """대상 판정 — 기존 statusline.sh 축약."""
    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR", ROOT))
    base = cwd.name
    if (cwd / ".claude-plugin" / "plugin.json").exists() and (cwd / "plugins").exists():
        return f"🔧 kit"
    if base == "templates" and cwd.parent.name == "setup":
        return "📦 templates"
    if str(cwd).startswith(str(Path.home() / ".claude")):
        return "🌐 global"
    return f"🎯 target/{base}"


def _session_stats() -> dict:
    sid = _session_id()
    if not sid:
        return {"turns": 0, "tokens": 0, "cost_usd": 0.0}
    rows = _q(
        "SELECT COUNT(*), COALESCE(SUM(tokens),0) FROM conversations WHERE session_id=?",
        (sid,),
    )
    turns, tokens = (rows[0] if rows else (0, 0))
    cost = _q(
        "SELECT COALESCE(SUM(cost_usd),0) FROM metrics WHERE recorded_at >= strftime('%s','now','-1 day')"
    )
    return {
        "turns": turns or 0,
        "tokens": tokens or 0,
        "cost_usd": (cost[0][0] if cost else 0.0) or 0.0,
    }


def _budget() -> tuple[float, float]:
    rows = _q("SELECT today_spent_usd, daily_limit_usd FROM budget LIMIT 1")
    if not rows:
        return (0.0, 0.0)
    spent, limit = rows[0]
    return (spent or 0.0, limit or 0.0)


def _recent_decisions(n: int = 1) -> str:
    rows = _q(
        "SELECT substr(user_msg,1,40) FROM decisions ORDER BY ts DESC LIMIT ?", (n,)
    )
    if not rows:
        return ""
    return rows[0][0] or ""


def _hooks_count() -> int:
    hooks = ROOT / ".claude" / "hooks"
    if not hooks.is_dir():
        return 0
    return sum(1 for p in hooks.glob("*.sh")) + sum(1 for p in hooks.glob("*.py"))


def main() -> None:
    target = _target()
    stats = _session_stats()
    spent, limit = _budget()

    # 진행률 (200k context 기준 근사)
    ctx_used = stats["tokens"]
    ctx_max = 1_000_000  # Opus 5 1M
    bar = _bar(ctx_used, ctx_max, 10)
    pct = min(100.0, (ctx_used / ctx_max) * 100)

    # 예산 진행률
    if limit > 0:
        bud_bar = _bar(int(spent * 100), int(limit * 100), 6)
        bud = f" 💰{bud_bar} {_fmt_cost(spent)}/{_fmt_cost(limit)}"
    else:
        bud = f" 💰{_fmt_cost(spent)}"

    turns = stats["turns"]
    tokens = _fmt_num(ctx_used)
    hooks = _hooks_count()
    ts = datetime.now().strftime("%H:%M")

    # 한 줄 status
    line = (
        f"{target} │ {bar} {pct:4.1f}% ({tokens}/1.0M) │ "
        f"turns:{turns} │ hooks:{hooks}{bud} │ {ts}"
    )
    sys.stdout.write(line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[statusline] {e}\n")
        sys.stdout.write("🔧 kit")
