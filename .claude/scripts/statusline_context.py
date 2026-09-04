#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
statusline_context — Claude Code 토큰 잔량 표시
표준 라이브러리만 사용 - Windows 함정 4개 회피.

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

# 상한 매핑 - 긴 것부터
LIMIT_PREFIXES = [
    # [1m] 접미 - 긴 것 먼저
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
    """cwd -> ~/.claude/projects/<safe>/ 폴더명."""
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


# 모델별 rate (USD per MTok) - input · output · cache_write · cache_read
MODEL_RATES = {
    "claude-opus-5": (5.0, 25.0, 6.25, 0.5),
    "claude-opus-4-8": (5.0, 25.0, 6.25, 0.5),
    "claude-opus-4-7": (5.0, 25.0, 6.25, 0.5),
    "claude-sonnet-5": (2.0, 10.0, 2.5, 0.2),
    "claude-sonnet-4-6": (3.0, 15.0, 3.75, 0.3),
    "claude-fable-5": (10.0, 50.0, 12.5, 1.0),
    "claude-haiku-4-5": (0.25, 1.25, 0.3, 0.03),
}


def pick_rate(model_id: str) -> tuple[float, float, float, float]:
    if not model_id:
        return (5.0, 25.0, 6.25, 0.5)
    for pref, rates in MODEL_RATES.items():
        if model_id.startswith(pref):
            return rates
    return (5.0, 25.0, 6.25, 0.5)


def cache_hit_rate(jsonl_path: str) -> float:
    """세션 prompt cache 히트율 = cache_read / (cache_read + input + cache_creation) * 100."""
    if not os.path.exists(jsonl_path):
        return 0.0
    tot_in = tot_cw = tot_cr = 0
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
                if rec.get("type") != "assistant":
                    continue
                u = ((rec.get("message") or {}).get("usage")) or {}
                tot_in += u.get("input_tokens", 0) or 0
                tot_cw += u.get("cache_creation_input_tokens", 0) or 0
                tot_cr += u.get("cache_read_input_tokens", 0) or 0
    except Exception:
        return 0.0
    denom = tot_in + tot_cw + tot_cr
    if denom <= 0:
        return 0.0
    return tot_cr / denom * 100.0


def recent_error_count(cwd: str) -> int:
    """.claude/logs/*.log 안 최근 24h ERROR·WARN·[err]·[skip] 카운트."""
    import glob as _g
    import time as _t
    import re as _re
    log_dir = os.path.join(cwd, ".claude", "logs")
    if not os.path.isdir(log_dir):
        return 0
    now = _t.time()
    cutoff = now - 86400
    total = 0
    pat = _re.compile(r"\b(ERROR|WARN|FAIL|\[err\]|\[skip\]|\[!!\])", _re.IGNORECASE)
    for lp in _g.glob(os.path.join(log_dir, "*.log")):
        try:
            if os.path.getmtime(lp) < cutoff:
                continue
            with open(lp, encoding="utf-8", errors="replace") as f:
                # 마지막 500 줄만 (부하 절감)
                lines = f.readlines()[-500:]
                for ln in lines:
                    if pat.search(ln):
                        total += 1
        except Exception:
            continue
    return total


def _jsonl_cost(jsonl_path: str, default_model: str = "") -> float:
    """단일 jsonl - 파일 안 message.model 로 rate 결정, 없으면 default_model."""
    if not os.path.exists(jsonl_path):
        return 0.0
    total = 0.0
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
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message") or {}
                u = msg.get("usage") or {}
                mid = msg.get("model") or default_model
                in_r, out_r, cw_r, cr_r = pick_rate(mid)
                total += (
                    (u.get("input_tokens", 0) or 0) * in_r
                    + (u.get("output_tokens", 0) or 0) * out_r
                    + (u.get("cache_creation_input_tokens", 0) or 0) * cw_r
                    + (u.get("cache_read_input_tokens", 0) or 0) * cr_r
                ) / 1_000_000
    except Exception:
        return 0.0
    return total


def session_cost(jsonl_path: str, model_id: str) -> float:
    return _jsonl_cost(jsonl_path, model_id)


def monthly_cost(cwd: str, model_id: str) -> float:
    """이번 달 1일 ~ 오늘 · 이 프로젝트의 모든 jsonl 세션 비용 합산."""
    import glob as _g
    import datetime as _d
    try:
        proj_dir = cwd_to_proj_dir(cwd)
        if not os.path.isdir(proj_dir):
            return 0.0
        # 이번 달 1일 00:00 timestamp
        now = _d.datetime.now()
        month_start = _d.datetime(now.year, now.month, 1).timestamp()
        total = 0.0
        for jp in _g.glob(os.path.join(proj_dir, "*.jsonl")):
            try:
                if os.path.getmtime(jp) < month_start:
                    continue
                total += _jsonl_cost(jp, model_id)
            except Exception:
                continue
        return total
    except Exception:
        return 0.0


def yearly_cost(cwd: str, model_id: str) -> float:
    """올해 1월 1일 ~ 오늘 · 프로젝트의 모든 jsonl 세션 비용 합산."""
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
                total += _jsonl_cost(jp, model_id)
            except Exception:
                continue
        return total
    except Exception:
        return 0.0


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def render(tokens: int, limit: int, exact_model: bool, no_usage: bool) -> str:
    if no_usage:
        return f"토큰 {EMPTY * 8} 측정 전"
    ratio = 0.0 if limit <= 0 else min(tokens / limit, 1.0)
    W = 8
    filled = int(round(ratio * W))
    filled = min(W, max(0, filled))
    bar = FILLED * filled + EMPTY * (W - filled)
    pct = ratio * 100
    tok_s = fmt_tokens(tokens)
    lim_s = fmt_tokens(limit)
    q = "" if exact_model else "?"
    line = f"토큰 {bar} {pct:.0f}%{q} ({tok_s}/{lim_s}{q})"
    if pct >= 95:
        line += " - [!] /compact 즉시 실행"
    elif pct >= 80:
        line += " - [주의] /compact 준비"
    elif pct >= 70:
        line += " - 주의"
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
_SESSION_COST = 0.0  # 세션 누적 추정 비용 (jsonl 계산 후 셋)
_MONTHLY_COST = 0.0  # 이번 달 전체 비용 (모든 jsonl 합산)
_YEARLY_COST = 0.0   # 올해 1월 1일부터 오늘까지 합산
_CACHE_HIT_RATE = 0.0  # 세션 prompt cache 히트율 %
_ERROR_COUNT = 0     # 최근 24h .claude/logs 안 error·warn 카운트



def extra_gauges(cwd):
    """한 줄 압축 - [토큰][재사용][일간][주간][세션한도][주간한도][MCP][git]."""
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
                # 예산 (일간-주간-월간)
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
                            f"일간 {db_bar} ${ds:.2f}/{d_lim}\n"
                            f"주간 {wb_bar} ${ws:.2f}/{w_lim}\n"
                            f"월간 {mb_bar} ${ms:.2f}/{m_lim}"
                        )
                except Exception:
                    pass
                # 재사용 solutions
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(AVG(reusable_score),0) FROM problem_solutions"
                    ).fetchone()
                    if r and r[0]:
                        solutions_str = f"재사용 {r[0]}건 - 평균 {r[1]:.1f}"
                except Exception:
                    pass
                # 세션
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(SUM(turns),0), COALESCE(SUM(tokens_total),0) "
                        "FROM session_summary"
                    ).fetchone()
                    if r:
                        sessions_str = f"세션 {r[0]} - 턴 {r[1]}"
                except Exception:
                    pass
                # 오늘 파일 변경
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM file_audit "
                        "WHERE ts >= datetime('now','-1 day')"
                    ).fetchone()
                    if r and r[0]:
                        files_str = f"오늘 파일 {r[0]}건"
                except Exception:
                    pass
                # 진행 중 task
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"
                    ).fetchone()
                    if r and r[0]:
                        tasks_str = f"task {r[0]}"
                except Exception:
                    pass
    except Exception:
        pass
    # MCP - Headroom proxy 헬스체크
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=0.3)
        mcp = "MCP on"
    except Exception:
        mcp = "MCP off"
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
            git_str = f"git {branch}" + (f" ({dirty} 변경)" if dirty else " clean")
    except Exception:
        pass

    # 두 줄 구조 - line 1: 세션(토큰과 합쳐짐 in main) · line 2: 주간 + MCP + 재사용
    import datetime as _dt
    import glob as _glob
    session_gauge = ""
    week_gauge = ""

    def _bar(pct, w=8):
        pct = max(0.0, min(100.0, pct))
        filled = int(round(pct / 100.0 * w))
        return "█" * filled + "▒" * (w - filled)

    # 1) Current session — 5h window · 가장 오래된 startedAt 기준 (안정적)
    # 근거: 사용자 지시 2026-09-03 - 최신 window 급변 방지 · 최근 5h 안 window 중 가장 이른 것
    try:
        home = os.path.expanduser("~")
        sess_files = _glob.glob(os.path.join(home, ".claude", "sessions", "*.json"))
        now_ms = int(_dt.datetime.now().timestamp() * 1000)
        window_ms = 5 * 60 * 60 * 1000
        cutoff_ms = now_ms - window_ms
        oldest_in_window = None
        for sf in sess_files:
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    j = json.load(f)
                started = int(j.get("startedAt") or 0)
                # 현재 5h window 내부 · 가장 이른 것
                if started >= cutoff_ms and started > 0:
                    if oldest_in_window is None or started < oldest_in_window:
                        oldest_in_window = started
            except Exception:
                continue
        if oldest_in_window:
            elapsed = max(0, now_ms - oldest_in_window)
            pct = min(elapsed / window_ms * 100.0, 100.0)
            reset_dt = _dt.datetime.fromtimestamp((oldest_in_window + window_ms) / 1000.0)
            reset_str = reset_dt.strftime("%I:%M%p").lstrip("0").lower()
            session_gauge = f"5h창 {_bar(pct)} {pct:.0f}% 경과 (reset {reset_str})"
    except Exception:
        pass

    # 2) Current week — stats-cache 우선 · stale 시 jsonl mtime fallback
    try:
        home = os.path.expanduser("~")
        stats_p = os.path.join(home, ".claude", "stats-cache.json")
        today = _dt.date.today()
        week_msgs = 0
        stats_stale = True
        if os.path.exists(stats_p):
            import time as _time
            age_h = (_time.time() - os.path.getmtime(stats_p)) / 3600
            with open(stats_p, "r", encoding="utf-8") as f:
                sc = json.load(f)
            for row in sc.get("dailyActivity", []):
                try:
                    d = _dt.date.fromisoformat(row.get("date", ""))
                    if 0 <= (today - d).days <= 7:
                        week_msgs += int(row.get("messageCount", 0) or 0)
                        stats_stale = False
                except Exception:
                    continue
        # jsonl mtime fallback — stats-cache 데이터 부족 시
        if stats_stale or week_msgs == 0:
            import re as _re
            safe = _re.sub(r"[^a-zA-Z0-9]", "-", cwd)
            proj_dir = os.path.join(home, ".claude", "projects", safe)
            if os.path.isdir(proj_dir):
                import glob as _g
                import time as _t
                cutoff = _t.time() - 7 * 86400
                # 각 jsonl 안 assistant 응답 카운트 = 근사 message 수
                for jp in _g.glob(os.path.join(proj_dir, "*.jsonl")):
                    try:
                        if os.path.getmtime(jp) < cutoff:
                            continue
                        with open(jp, "r", encoding="utf-8", errors="replace") as f:
                            for line in f:
                                if '"type":"assistant"' in line:
                                    week_msgs += 1
                    except Exception:
                        continue
        # 주간 - 플랜 한도 실값은 로컬에 없음 (statsig X · stats-cache stale).
        # 근거 없는 상수로 % 를 만들면 A2 위반 -> 실측 메시지 수만 표기.
        # 실제 플랜 사용률은 /usage 에서 확인.
        days_to_thu = (3 - today.weekday()) % 7 or 7
        reset_day = today + _dt.timedelta(days=days_to_thu)
        reset_str = reset_day.strftime("%b ") + str(reset_day.day)
        week_gauge = f"주간 {week_msgs:,} msg (reset {reset_str} · 한도는 /usage)"
    except Exception:
        pass

    # 3) 짧은 인디케이터 (MCP - 재사용)
    tail = []
    # MCP 카운트 — .claude/state/mcp-status.json (형식: "MCP 14 on 13 off")
    mcp_shown = False
    try:
        mcp_cache = os.path.join(cwd, ".claude", "state", "mcp-status.json")
        if os.path.exists(mcp_cache):
            import time as _time
            age = _time.time() - os.path.getmtime(mcp_cache)
            with open(mcp_cache, "r", encoding="utf-8") as f:
                ms = json.load(f)
            ok = int(ms.get("connected", 0))
            fail = int(ms.get("failed", 0))
            stale = "?" if age > 14400 else ""  # 4h 이상 = 오래됨 표시
            tail.append(f"MCP {ok} on {fail} off{stale}")
            mcp_shown = True
    except Exception:
        pass
    if not mcp_shown:
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=0.3)
            tail.append("MCP on")
        except Exception:
            tail.append("MCP off")
    # git 표시 제거 (사용자 요청 2026-09-03)
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
                    tail.append(f"재사용 {cnt}건 (사용률 {rate:.0f}%)")
                # orca hit 카운터 (activations · tasks)
                try:
                    a = c.execute("SELECT COUNT(*) FROM activations").fetchone()
                    t = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN "
                        "('locked','pending','in_progress','waiting_approval')"
                    ).fetchone()
                    ac = int(a[0]) if a else 0
                    tk = int(t[0]) if t else 0
                    if ac or tk:
                        tail.append(f"orca 활성 {ac}건 · task {tk}")
                except Exception:
                    pass
                # Cache hit rate (prompt cache 절감)
                if _CACHE_HIT_RATE > 0:
                    tail.append(f"cache {_CACHE_HIT_RATE:.0f}% hit")
                # 최근 24h error·warn 카운트
                if _ERROR_COUNT > 0:
                    prefix = "[!] " if _ERROR_COUNT > 20 else ""
                    tail.append(f"{prefix}errors {_ERROR_COUNT}")
                # 하드코딩 감사 결과 (별도 캐시)
                try:
                    aud = os.path.join(cwd, ".claude", "state", "hardcoded-audit.json")
                    if os.path.exists(aud):
                        with open(aud, "r", encoding="utf-8") as f:
                            a = json.load(f)
                        st = a.get("status", "?")
                        tot = int(a.get("total_hits", 0))
                        if st == "PASS":
                            tail.append("하드코딩 감사 PASS")
                        elif st == "CRITICAL":
                            tail.append(f"[!] 하드코딩 CRITICAL {tot}")
                        else:
                            tail.append(f"하드코딩 WARN {tot}")
                except Exception:
                    pass
                # AI 비용은 별도 line3 로 분리 (여기서는 append X)
                pass
    except Exception:
        pass

    # AI 비용 line3 (세션 · 현월 · 년간 · KRW 병기)
    rate = float(os.environ.get("USD_KRW_RATE", "1350"))
    monthly = _MONTHLY_COST if _MONTHLY_COST > 0 else _SESSION_COST
    yearly = _YEARLY_COST if _YEARLY_COST > 0 else monthly
    import datetime as _dt2
    cur_m = _dt2.datetime.now().month
    if _SESSION_COST > 0.001 or monthly > 0.001 or yearly > 0.001:
        def _krw(usd):
            v = usd * rate
            return f"₩{int(v):,}" if v >= 1 else f"₩{v:.0f}"
        line3 = (
            f"AI 비용 세션 ${_SESSION_COST:.2f} ({_krw(_SESSION_COST)}) · "
            f"{cur_m}월 ${monthly:.2f} ({_krw(monthly)}) · "
            f"년간 ${yearly:.2f} ({_krw(yearly)})"
        )
    else:
        line3 = ""

    # 최종 조립 - session_gauge 는 별도 반환 (main 에서 token_line 과 합침)
    line2_parts = []
    if week_gauge:
        line2_parts.append(week_gauge)
    if tail:
        line2_parts.extend(tail)
    line2 = " - ".join(line2_parts)
    return {"session": session_gauge, "line2": line2, "line3": line3}


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

    # 해결된 상한을 SoT 로 공유 - jsonl 은 model 을 "[1m]" 없이 기록하므로
    # hook(inject-compact-reminder)은 stdin model.id 를 못 본다. 여기서만 정본 기록.
    if exact_model and cwd:
        try:
            import datetime as _dtc
            st = os.path.join(cwd, ".claude", "state")
            os.makedirs(st, exist_ok=True)
            with open(os.path.join(st, "context-limit.json"), "w", encoding="utf-8") as _f:
                json.dump({"model": model_id, "limit": limit,
                           "ts": _dtc.datetime.now().isoformat(timespec="seconds")}, _f)
        except Exception:
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
            # 세션 · 이번 달 · 올해 전체 비용 + cache hit + error count
            global _SESSION_COST, _MONTHLY_COST, _YEARLY_COST
            global _CACHE_HIT_RATE, _ERROR_COUNT
            _SESSION_COST = session_cost(jsonl, model_id)
            _MONTHLY_COST = monthly_cost(cwd, model_id)
            _YEARLY_COST = yearly_cost(cwd, model_id)
            _CACHE_HIT_RATE = cache_hit_rate(jsonl)
            _ERROR_COUNT = recent_error_count(cwd)
        except Exception:
            pass

    # 3줄 구조: [시각 + 토큰 + 세션] / [주간 + MCP + 재사용 + 하드코딩 + orca + cache + err] / [AI 비용]
    import datetime as _dt3
    clock = _dt3.datetime.now().strftime("%m/%d %H:%M")
    token_line = render(tokens, limit, exact_model, no_usage)
    gauges = extra_gauges(cwd) if cwd else {"session": "", "line2": "", "line3": ""}
    line1_parts = [clock, token_line]
    if gauges.get("session"):
        line1_parts.append(gauges["session"])
    line1 = " - ".join(line1_parts)
    line2 = gauges.get("line2", "")
    line3 = gauges.get("line3", "")
    out = [line1]
    if line2:
        out.append(line2)
    if line3:
        out.append(line3)
    print("\n".join(out))


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
