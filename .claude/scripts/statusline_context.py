#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
statusline_context — Claude Code 컨텍스트 잔량 표시
표준 라이브러리만 사용 · Windows 함정 4개 회피.

경로 예: ~/.claude/statusline_context.py
"""
from __future__ import annotations
import json
import os
import re
import sys

# [함정 1] CP949 stdout 회피
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FILLED = "█"  # █
EMPTY = "▒"   # ▒
WIDTH = 10

# 상한 매핑 · 긴 것부터
LIMIT_PREFIXES = [
    # [1m] 접미 · 긴 것 먼저
    ("claude-opus-5[1m]", 1_000_000),
    ("claude-sonnet-5[1m]", 1_000_000),
    ("claude-opus-4-8[1m]", 1_000_000),
    ("claude-opus-4-7[1m]", 1_000_000),
    ("claude-sonnet-4-6[1m]", 1_000_000),
    # 표준 200K
    ("claude-opus-5", 200_000),
    ("claude-sonnet-5", 200_000),
    ("claude-opus-4-8", 200_000),
    ("claude-opus-4-7", 200_000),
    ("claude-sonnet-4-6", 200_000),
    ("claude-fable-5", 200_000),
    ("claude-haiku-4-5", 200_000),
]
DEFAULT_LIMIT = 200_000


def pick_limit(model_id: str) -> tuple[int, bool]:
    """(상한, 정확?) 반환."""
    if not model_id:
        return DEFAULT_LIMIT, False
    for pref, lim in LIMIT_PREFIXES:
        if model_id.startswith(pref):
            return lim, True
    return DEFAULT_LIMIT, False


def cwd_to_proj_dir(cwd: str) -> str:
    """cwd → ~/.claude/projects/<safe>/ 폴더명."""
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "projects", safe)


def last_assistant_usage(jsonl_path: str) -> dict | None:
    """jsonl 마지막 assistant 레코드의 message.usage."""
    if not os.path.exists(jsonl_path):
        return None
    last = None
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") == "assistant":
                    usage = ((rec.get("message") or {}).get("usage")) or None
                    if usage:
                        last = usage
    except Exception:
        return None
    return last


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def render(tokens: int, limit: int, exact_model: bool, no_usage: bool) -> str:
    if no_usage:
        return f"{EMPTY * WIDTH} 측정 전"
    ratio = 0.0 if limit <= 0 else min(tokens / limit, 1.0)
    filled = int(round(ratio * WIDTH))
    filled = min(WIDTH, max(0, filled))
    bar = FILLED * filled + EMPTY * (WIDTH - filled)
    pct = ratio * 100
    tok_s = fmt_tokens(tokens)
    lim_s = fmt_tokens(limit)
    q = "" if exact_model else "?"
    line = f"{bar} {pct:.1f}%{q} ({tok_s}/{lim_s}{q})"
    if pct >= 95:
        line += "  compact 임박"
    elif pct >= 80:
        line += "  ⚠"
    return line


def mini_bar(cur, total, w=6):
    """짧은 bar (multi-gauge 용)."""
    if total <= 0:
        return "─" * w
    r = min(cur / total, 1.0)
    filled = int(round(r * w))
    filled = min(w, max(0, filled))
    return "█" * filled + "▒" * (w - filled)


def gauge(label, cur, total, cur_s="", tot_s="", w=6):
    """§ ██▒▒▒▒ 32% (cur/tot) 스타일."""
    if total <= 0:
        return f"{label} {'─' * w} (∞)"
    r = min(cur / total, 1.0)
    pct = r * 100
    cs = cur_s or fmt_tokens(int(cur))
    ts = tot_s or fmt_tokens(int(total))
    return f"{label} {mini_bar(cur, total, w)} {pct:.0f}% ({cs}/{ts})"


SEP = "─" * 50  # 구분선


def plan_usage(cwd):
    """Anthropic plan usage — 세션·주간 한도. jsonl 안 usage.plan_limit."""
    # Claude Code jsonl 의 message.usage 는 session_limit·week_limit 표기 X (2026-09 기준).
    # 대체: statsig cache · ~/.claude/statsig/ 안 session·week percent
    import glob
    home = os.path.expanduser("~")
    session_pct = week_pct = None
    reset_str = ""
    # try statsig cached values
    for p in glob.glob(os.path.join(home, ".claude", "statsig", "*")):
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
                # 대충 파싱 (JSON 안 usage%)
                import re
                m = re.search(r'session[_-]?limit["\s:]+([\d.]+)', txt)
                if m:
                    session_pct = float(m.group(1))
                m = re.search(r'week[_-]?limit["\s:]+([\d.]+)', txt)
                if m:
                    week_pct = float(m.group(1))
        except Exception:
            pass
    return session_pct, week_pct, reset_str


def extra_gauges(cwd):
    """한 줄 압축 · [토큰][재사용][일간][주간][세션한도][주간한도][MCP][git]."""
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
                # 예산 (일간·주간·월간)
                try:
                    b = c.execute(
                        "SELECT COALESCE(today_spent_usd,0), COALESCE(daily_limit_usd,0), "
                        "COALESCE(weekly_spent_usd,0), COALESCE(weekly_limit_usd,0), "
                        "COALESCE(monthly_spent_usd,0), COALESCE(monthly_limit_usd,0) "
                        "FROM budget LIMIT 1"
                    ).fetchone()
                    if b:
                        ds, dl, ws, wl, ms, ml = b
                        d_lim = f"${dl:.0f}" if dl else "∞"
                        w_lim = f"${wl:.0f}" if wl else "∞"
                        m_lim = f"${ml:.0f}" if ml else "∞"
                        db_bar = mini_bar(ds*100, (dl or 1)*100, 4) if dl else "────"
                        wb_bar = mini_bar(ws*100, (wl or 1)*100, 4) if wl else "────"
                        mb_bar = mini_bar(ms*100, (ml or 1)*100, 4) if ml else "────"
                        budget_str = (
                            f"💰 일간 {db_bar} ${ds:.2f}/{d_lim}\n"
                            f"📅 주간 {wb_bar} ${ws:.2f}/{w_lim}\n"
                            f"📆 월간 {mb_bar} ${ms:.2f}/{m_lim}"
                        )
                except Exception:
                    pass
                # 재사용 solutions
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(AVG(reusable_score),0) FROM problem_solutions"
                    ).fetchone()
                    if r and r[0]:
                        solutions_str = f"💡 재사용 {r[0]}건 · ★{r[1]:.1f}"
                except Exception:
                    pass
                # 세션
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(SUM(turns),0), COALESCE(SUM(tokens_total),0) "
                        "FROM session_summary"
                    ).fetchone()
                    if r:
                        sessions_str = f"💬 세션 {r[0]}·턴 {r[1]}"
                except Exception:
                    pass
                # 오늘 파일 변경
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM file_audit "
                        "WHERE ts >= datetime('now','-1 day')"
                    ).fetchone()
                    if r and r[0]:
                        files_str = f"📁 오늘 {r[0]}건"
                except Exception:
                    pass
                # 진행 중 task
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"
                    ).fetchone()
                    if r and r[0]:
                        tasks_str = f"📋 task {r[0]}"
                except Exception:
                    pass
    except Exception:
        pass
    # MCP · Headroom proxy 헬스체크
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8787/", timeout=0.3)
        mcp = "🔌 MCP 🟢"
    except Exception:
        mcp = "🔌 MCP ⚪"
    # git branch + uncommitted
    git_str = ""
    try:
        import subprocess
        b = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1
        )
        branch = b.stdout.strip() if b.returncode == 0 else ""
        s = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True, text=True, timeout=1
        )
        dirty = len([x for x in s.stdout.splitlines() if x.strip()]) if s.returncode == 0 else 0
        if branch:
            git_str = f"🌿 {branch}" + (f" ({dirty}📝)" if dirty else " ✓")
    except Exception:
        pass

    # 한 줄 압축 [라벨:값] 형식
    parts = []
    # 예산
    try:
        b_row = None
        db = os.path.join(cwd, ".claude", "state", "orca.db")
        if os.path.exists(db):
            import sqlite3
            with sqlite3.connect(db) as c:
                r = c.execute(
                    "SELECT COALESCE(today_spent_usd,0), COALESCE(daily_limit_usd,0), "
                    "COALESCE(weekly_spent_usd,0), COALESCE(weekly_limit_usd,0) "
                    "FROM budget LIMIT 1"
                ).fetchone()
                if r:
                    b_row = r
        if b_row:
            ds, dl, ws, wl = b_row
            parts.append(f"[일간 ${ds:.2f}/{f'${dl:.0f}' if dl else '∞'}]")
            parts.append(f"[주간 ${ws:.2f}/{f'${wl:.0f}' if wl else '∞'}]")
    except Exception:
        pass
    # 재사용
    try:
        import sqlite3
        db = os.path.join(cwd, ".claude", "state", "orca.db")
        if os.path.exists(db):
            with sqlite3.connect(db) as c:
                r = c.execute("SELECT COUNT(*) FROM problem_solutions").fetchone()
                if r and r[0]:
                    parts.append(f"[재사용 {r[0]}]")
                r = c.execute("SELECT COUNT(*), COALESCE(SUM(turns),0) FROM session_summary").fetchone()
                if r and r[0]:
                    parts.append(f"[세션 {r[0]}·턴 {r[1]}]")
    except Exception:
        pass
    # Plan usage (세션한도·주간한도)
    sp, wp, _ = plan_usage(cwd)
    if sp is not None:
        parts.append(f"[세션한도 {sp:.0f}%]")
    if wp is not None:
        parts.append(f"[주간한도 {wp:.0f}%]")
    # MCP
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8787/", timeout=0.3)
        parts.append("[🔌🟢]")
    except Exception:
        parts.append("[🔌⚪]")
    # git
    try:
        import subprocess
        b = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
        if b.returncode == 0:
            br = b.stdout.strip()
            s2 = subprocess.run(
                ["git", "-C", cwd, "status", "--porcelain"],
                capture_output=True, text=True, timeout=1,
            )
            dirty = len([x for x in s2.stdout.splitlines() if x.strip()]) if s2.returncode == 0 else 0
            parts.append(f"[🌿{br}{f' {dirty}📝' if dirty else ''}]")
    except Exception:
        pass
    return " ".join(parts)


def main() -> None:
    # [함정 4] 예외 나도 rc=0 + 빈 게이지
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    model_id = ""
    try:
        model_id = (data.get("model") or {}).get("id") or ""
    except Exception:
        pass

    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""

    limit, exact_model = pick_limit(model_id)

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
        except Exception:
            pass

    # 1) 컨텍스트 게이지 (기존)
    print(render(tokens, limit, exact_model, no_usage))
    # 2~6) 추가 게이지 (다중 줄)
    extra = extra_gauges(cwd) if cwd else ""
    if extra:
        print(extra)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # 최후 fallback
        try:
            print(EMPTY * WIDTH + " 측정 전")
        except Exception:
            print("측정 전")
    sys.exit(0)
