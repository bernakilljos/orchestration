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
    pass  # noqa: BLE001

FILLED = "█"  # █
EMPTY = "▒"   # ▒
WIDTH = 10

# 상한 매핑 - 긴 것부터
LIMIT_PREFIXES = [
    # Opus 5.5 = 1M 기본 (접미 유무 무관) - "claude-opus-5" 보다 먼저 와야 함
    ("claude-opus-5-5", 1_000_000),
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



def _project_root(start: str) -> str:
    """루트 표식(.git 또는 .claude+plugins)이 있는 조상 디렉터리를 돌려준다.

    못 찾으면 start 를 그대로 준다(안전측 — 없던 곳에 새로 만들지는 않는다).
    CLAUDE_PROJECT_DIR 이 있으면 그것이 정본이다.
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
    """(상한, 정확?) 반환."""
    if not model_id:
        return DEFAULT_LIMIT, False
    # 2026-09-23: 이름표만 보면 새 모델(claude-opus-5-5[1m])이 claude-opus-5 에 걸려 200K 로 오판됐다
    # (실제 26% 인데 "125% 즉시 compact"). [1m] 접미가 곧 1M 이다 — 이름과 무관하게 먼저 본다.
    if "[1m]" in model_id.lower():
        return 1_000_000, True
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
    """jsonl 마지막 assistant 레코드의 message.usage.

    2026-10-06 — 끝에서부터 256KB 씩 거꾸로 읽고 찾으면 멈춘다 (127MB 세션 전체 읽기 → 수 초 실측)."""
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
                    except Exception:
                        continue
                    if rec.get("type") == "assistant":
                        usage = ((rec.get("message") or {}).get("usage")) or None
                        if usage:
                            return usage
    except Exception:
        return None
    return None


# 모델별 rate - 정본은 lib/pricing.py (여기 따로 두면 갈린다 · 헌장 E)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
try:
    from pricing import rates_for as _rates_for
except Exception:
    _rates_for = None


def pick_rate(model_id: str) -> tuple[float, float, float, float]:
    """(input, output, cache_write, cache_read) USD/MTok. 모르는 모델은 0 (추정 안 함)."""
    p = _rates_for(model_id) if _rates_for else None
    if not p:
        return (0.0, 0.0, 0.0, 0.0)
    return (p["input"] or 0.0, p["output"] or 0.0,
            p["cache_write"] or 0.0, p["cache_read"] or 0.0)


def cache_hit_rate(jsonl_path: str) -> float:
    """세션 prompt cache 히트율 = cache_read / (cache_read + input + cache_creation) * 100."""
    _c, tot_in, tot_cw, tot_cr = _scan_jsonl(jsonl_path, "")
    denom = tot_in + tot_cw + tot_cr
    if denom <= 0:
        return 0.0
    return tot_cr / denom * 100.0


def recent_error_count(cwd: str) -> int:
    """하위호환 — 오류 수만."""
    return recent_log_issues(cwd)[0]


def recent_log_issues(cwd: str):
    """(오류 수, 경고 수, 오류 최다 로그) — 줄 안 시각이 최근 24h 인 것만 센다.

    2026-10-06: 예전엔 «24h 안에 갱신된 로그의 마지막 500줄»을 시각 무관하게 셌고 WARN·skip 까지
    섞어 «errors 121» 처럼 부풀었다 (실측: kit 36건 전부 시각 없는 줄 · 24h 내 실제 오류 0).
    시각 없는 줄은 언제 것인지 모르므로 세지 않는다.
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
    # 2026-09-23: 명령·프롬프트·조회를 그대로 적는 기록용 로그는 뺀다. 명령 문자열에 "error" 가 있으면
    # 오류로 세어 90건 중 65건이 bash_commands.log 였다(실제 오류 아님).
    skip = {"bash_commands.log", "lookup-history.log", "user-prompt-history.log",
            "conversation-save.log", "deflection-detect.log", "emotion-response.log",
            # 2026-10-12: mcp-health.log 는 MCP 섹션에서 별도 집계 (중복 방지)
            "mcp-health.log",
            # 2026-10-16: hook-trace.log 는 사용자 프롬프트 원문을 적는다 → 프롬프트의 "failed" 글자가 오류로 세졌다
            "hook-trace.log", "prompt-dispatch.log", "tool-dispatch.log"}
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
        except Exception:
            continue
    top = errs.most_common(1)[0][0] if errs else ""
    return sum(errs.values()), warns, top


# 2026-10-06 — 렌더마다 모든 jsonl 을 처음부터 다시 읽었다 (월·연 합계로 같은 파일 2번 · 127MB 세션 4초 실측).
#   파일별 (크기·읽은 위치·message.id 별 집계) 를 state 에 두고 **늘어난 뒷부분만** 읽는다.
#   크기가 줄면(덮어쓰기) 처음부터 다시. 결과는 전체 재계산과 같다 (id 별 마지막 usage 규칙 동일).
_SCAN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state", "jsonl-scan-cache.json")
_SCAN: dict | None = None
_SCAN_DIRTY = False


def _scan_load() -> dict:
    global _SCAN
    if _SCAN is None:
        try:
            with open(_SCAN_PATH, encoding="utf-8") as f:
                _SCAN = json.load(f)
        except Exception:
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
    except Exception:
        pass  # noqa: BLE001


import atexit as _atexit
_atexit.register(_scan_save)


def _scan_jsonl(jsonl_path: str, default_model: str = "", ts_prefix: str = "") -> tuple[float, int, int, int]:
    """(비용 USD, input, cache_write, cache_read) — message.id 별 마지막 usage 만 센다.

    ts_prefix ("2026-10"·"2026") 가 있으면 그 기간 timestamp 의 응답만 합산한다.
    2026-09-23: 월·년 합산을 파일 mtime 으로만 걸러 8월 기록까지 9월에 더했다($4,635 → 실제 $2,924).
    """
    global _SCAN_DIRTY
    if not os.path.exists(jsonl_path):
        return (0.0, 0, 0, 0)
    cache = _scan_load()
    key = os.path.abspath(jsonl_path) + "|" + (default_model or "") + "|v2"  # v2: 항목에 timestamp 추가
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
                    except Exception:
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
        except Exception:
            return (0.0, 0, 0, 0)
    vals = [v for v in ent["ids"].values() if not ts_prefix or (len(v) > 4 and v[4].startswith(ts_prefix))]
    return (sum(v[0] for v in vals), sum(v[1] for v in vals), sum(v[2] for v in vals), sum(v[3] for v in vals))


def _jsonl_cost(jsonl_path: str, default_model: str = "", ts_prefix: str = "") -> float:
    """단일 jsonl - 파일 안 message.model 로 rate 결정, 없으면 default_model."""
    return _scan_jsonl(jsonl_path, default_model, ts_prefix)[0]


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
                total += _jsonl_cost(jp, model_id, now.strftime("%Y-%m"))
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
                total += _jsonl_cost(jp, model_id, now.strftime("%Y"))
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
        return f"{EMPTY * 8} 측정 전"
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
        line += " · [!] 자동 compact 임박 (끝났으면 /clear)"
    elif pct >= 80:
        line += " · 작업 끝나면 /clear"
    elif pct >= 70:
        line += " · 주의"
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


# 2026-09-05: plan_usage() 를 걷어냈다. ~/.claude/statsig/ 파일을 정규식으로 훑어
#   session_limit·week_limit 을 뽑으려 했는데 그 폴더에는 파일이 0개였고(실측),
#   호출하는 곳도 없었다. Anthropic 실제 한도는 이 스크립트가 읽을 수 없다 —
#   못 읽는 값을 지어내느니 안 띄운다 (헌장 A2).

def extra_gauges(cwd, data=None):
    """한 줄 압축 - [토큰][재사용][일간][주간][세션한도][주간한도][MCP][git]."""
    # ★★★1006 — **정규화는 여기서 한다(정본 1곳 · ⑥).**
    #   처음엔 main() 쪽에만 넣었는데 이 함수 안의 8개 경로가 그대로 하위 폴더를
    #   보고 있어 MCP·비용이 계속 비었다 — 「한 곳씩 고치면 또 빠진다」를 내가 했다.
    #   ★판정은 «.claude 폴더가 있는가»다(프로젝트 구조를 지어내지 않는다).
    if cwd:
        _p0 = os.path.abspath(cwd)
        for _ in range(5):
            if os.path.isdir(os.path.join(_p0, "plugins")) and os.path.isdir(os.path.join(_p0, ".claude")):  # kit 설치 루트 (하위 폴더의 로컬 .claude 에서 멈추지 않게 · hook guard 와 같은 기준)
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
                    pass  # noqa: BLE001
                # 재사용 solutions
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(AVG(reusable_score),0) FROM problem_solutions"
                    ).fetchone()
                    if r and r[0]:
                        solutions_str = f"재사용 {r[0]}건 - 평균 {r[1]:.1f}"
                except Exception:
                    pass  # noqa: BLE001
                # 세션
                try:
                    r = c.execute(
                        "SELECT COUNT(*), COALESCE(SUM(turns),0), COALESCE(SUM(tokens_total),0) "
                        "FROM session_summary"
                    ).fetchone()
                    if r:
                        sessions_str = f"세션 {r[0]} - 턴 {r[1]}"
                except Exception:
                    pass  # noqa: BLE001
                # 오늘 파일 변경
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM file_audit "
                        "WHERE ts >= datetime('now','-1 day')"
                    ).fetchone()
                    if r and r[0]:
                        files_str = f"오늘 파일 {r[0]}건"
                except Exception:
                    pass  # noqa: BLE001
                # 진행 중 task
                try:
                    r = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN ('pending','in_progress')"
                    ).fetchone()
                    if r and r[0]:
                        tasks_str = f"task {r[0]}"
                except Exception:
                    pass  # noqa: BLE001
    except Exception:
        pass  # noqa: BLE001
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
            git_str = f"git {branch}" + (f" ({dirty} 변경)" if dirty else " clean")
    except Exception:
        pass  # noqa: BLE001

    # Agent 진행 섹션 (2026-10-12 · 10-16 등급별 색으로 교체)
    #   기록: .claude/hooks/tool/track_agent_dispatch.py (SubagentStart/Stop · 키=agent_id)
    #   색 = 등급(모델): haiku 녹 · sonnet 청 · opus/inherit 보라 · fable/mythos 빨강. 숫자 = 그 등급 중 최장 경과.
    agent_str = ""
    try:
        active_agents_file = os.path.join(cwd, ".claude", "state", "active-agents.json")
        if os.path.exists(active_agents_file):
            with open(active_agents_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            agents = raw if isinstance(raw, list) else []
            import datetime as _dt_mod
            now_ts = _dt_mod.datetime.now(_dt_mod.timezone.utc).replace(tzinfo=None)
            _GRADES = [  # (판정 키워드, 순위, ANSI, 표식, 이름)
                (("fable", "mythos"), 4, "[1;31m", "🔴", "F"),
                (("opus", "inherit"), 3, "[1;35m", "🟣", "O"),
                (("sonnet",), 2, "[1;36m", "🔵", "S"),
                (("haiku",), 1, "[1;32m", "🟢", "H"),
            ]

            def _grade(model):
                m = (model or "inherit").lower()
                for keys, rank, ansi, mark, nm in _GRADES:
                    if any(k in m for k in keys):
                        return rank, ansi, mark, nm
                return 3, "[1;35m", "🟣", "O"  # 모르는 값 = 메인 모델 상속으로 본다

            def _dur(sec):
                return f"{sec // 60}m{sec % 60:02d}s" if sec >= 60 else f"{sec}s"

            def _k(n):
                return f"{n / 1000:.0f}k" if n >= 1000 else str(n)

            # 서브에이전트 기록 파일 증분 읽기 — 도구 수 · 현재 컨텍스트 토큰 · 마지막 동작
            #   (파일이 MB 단위라 매번 전체를 읽지 않는다: 읽은 위치를 .claude/state/agent-scan.json 에 둔다)
            scan_p = os.path.join(cwd, ".claude", "state", "agent-scan.json")
            try:
                with open(scan_p, "r", encoding="utf-8") as f:
                    scan = json.load(f)
            except Exception:
                scan = {}

            def _scan(path):
                st = scan.get(path) or {"off": 0, "tools": 0, "ctx": 0, "last": ""}
                try:
                    size = os.path.getsize(path)
                    if size < st["off"]:
                        st = {"off": 0, "tools": 0, "ctx": 0, "last": ""}
                    if size > st["off"]:
                        with open(path, "rb") as f:
                            f.seek(st["off"])
                            chunk = f.read(size - st["off"])
                        end = chunk.rfind(b"\n") + 1  # 완성된 줄까지만
                        for line in chunk[:end].splitlines():
                            try:
                                o = json.loads(line)
                            except Exception:
                                continue
                            m = o.get("message") or {}
                            if not isinstance(m, dict):
                                continue
                            u = m.get("usage")
                            if isinstance(u, dict):
                                st["ctx"] = (int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0)
                                             + int(u.get("cache_creation_input_tokens") or 0) + int(u.get("output_tokens") or 0))
                            content = m.get("content")
                            for c in (content if isinstance(content, list) else []):
                                if isinstance(c, dict) and c.get("type") == "tool_use":
                                    st["tools"] += 1
                                    ti = c.get("input") or {}
                                    nm_ = c.get("name", "")
                                    # Claude Code 에이전트 목록처럼 «무엇을 하는 중» 으로 읽히게 (예: Write dbg_one.py)
                                    fp = os.path.basename(str(ti.get("file_path") or ti.get("notebook_path") or ""))
                                    if ti.get("description"):
                                        act = str(ti["description"])
                                    elif fp:
                                        act = f"{nm_} {fp}"
                                    elif ti.get("pattern"):
                                        act = f"{nm_} {ti['pattern']}"
                                    elif ti.get("command"):
                                        act = str(ti["command"])
                                    elif ti.get("url") or ti.get("query"):
                                        act = f"{nm_} {ti.get('url') or ti.get('query')}"
                                    else:
                                        act = nm_
                                    act = " ".join(act.split())
                                    st["last"] = act if len(act) <= 40 else act[:39] + "…"
                        st["off"] += end
                    scan[path] = st
                except OSError:
                    pass
                return st

            proj_dir = cwd_to_proj_dir(cwd)
            rows = []
            for a in agents:
                if a.get("end_ts"):
                    continue
                try:
                    st0 = _dt_mod.datetime.strptime(a.get("start_ts", ""), "%Y-%m-%dT%H:%M:%SZ")
                    dur = max(0, int((now_ts - st0).total_seconds()))
                except Exception:
                    dur = 0
                tp = a.get("transcript") or ""
                if not (tp and os.path.exists(tp)) and a.get("id"):  # 경로가 없으면 이 프로젝트 세션 폴더에서 찾는다
                    import glob as _g
                    hits = _g.glob(os.path.join(proj_dir, "*", "subagents", f"agent-{a['id']}.jsonl"))
                    tp = hits[0] if hits else ""
                # 이 프로젝트 세션의 기록만 읽는다 — 다른 프로젝트 에이전트의 동작이 섞여 보이지 않게 (2026-10-16)
                if tp and os.path.normcase(os.path.abspath(tp)).find(os.path.normcase(os.path.abspath(proj_dir))) != 0:
                    tp = ""
                info = _scan(tp) if tp else None
                rows.append((_grade(a.get("model")), a, dur, info, tp))
            try:  # 열린 에이전트의 스캔 기록만 남긴다
                live = {r[4] for r in rows if r[4]}
                with open(scan_p, "w", encoding="utf-8") as f:
                    json.dump({k: v for k, v in scan.items() if k in live}, f)
            except Exception:
                pass
            rows.sort(key=lambda r: (-r[0][0], -r[2]))
            # 긴급도 (2026-10-16 사용자 지시 «긴급도 하나 넣어서 7줄로»)
            #   긴급 = 기록 파일이 3분+ 안 늘어남(멈춤 의심) · 주의 = 10분+ 실행 · 정상 = 그 외
            import time as _tm
            stalled = set()
            for r in rows:
                try:
                    if r[4] and r[2] > 180 and _tm.time() - os.path.getmtime(r[4]) > 180:
                        stalled.add(id(r[1]))
                except OSError:
                    pass
            if stalled:
                urgency = "[1;31m긴급 멈춤의심 " + str(len(stalled)) + "[0m"
            elif any(r[2] > 600 for r in rows):
                urgency = "[1;33m주의 10분+[0m"
            else:
                urgency = "[1;32m정상[0m"
            parts = []
            for (rank, ansi, mark, nm), a, dur, info, _tp in rows[:3]:
                name = (a.get("type") or "agent").split(":")[-1]
                desc = a.get("description") or ""
                desc = f"「{desc[:14]}」" if desc and desc != name else ""
                extra = ""
                if info:
                    extra = f" 도구{info['tools']} {_k(info['ctx'])}" + (f" {info['last']}" if info.get("last") else "")
                warn = " ⛔정지" if id(a) in stalled else (" ⏳" if dur > 600 else "")
                parts.append(f"{ansi}{mark}{nm} {name}{desc} {_dur(dur)}{extra}{warn}\033[0m")
            if len(rows) > 3:
                # 나머지는 "..." + 등급별 색상 아이콘 + 개수 (우선순위 보이게 · 2026-10-16)
                extras = {}
                for (rank, ansi, mark, nm), *_rest in rows[3:]:
                    key = (ansi, mark, nm)
                    extras[key] = extras.get(key, 0) + 1
                extra_parts = [f"{a}{m}{n}+{c}\033[0m" for (a, m, n), c in extras.items()]
                parts.append("\033[90m...\033[0m " + " ".join(extra_parts))
            agent_str = (" · ".join(parts) + " · " + urgency) if parts else ""
    except Exception:
        pass  # noqa: BLE001

    # 두 줄 구조 - line 1: 세션(토큰과 합쳐짐 in main) · line 2: 주간 + MCP + 재사용 + agent
    import datetime as _dt
    import glob as _glob
    session_gauge = ""
    week_gauge = ""

    def _bar(pct, w=8):
        pct = max(0.0, min(100.0, pct))
        filled = int(round(pct / 100.0 * w))
        return "█" * filled + "▒" * (w - filled)

    # 2026-09-07: 세션·주간 자체 추정(5h창 경과 · 프로젝트 jsonl 응답 수)을 걷어냈다.
    #   아래 rate_limits 블록이 항상 덮어써서 죽은 코드였고, 매 렌더마다 7일치 jsonl 을
    #   전부 읽느라 상태바만 느려졌다. 실값은 stdin rate_limits + 캐시로 충분하다.

    # 3) 짧은 인디케이터 (MCP - 재사용)
    tail = []
    # MCP 카운트 — .claude/state/mcp-status.json (형식: "MCP 14 on 13 off")
    mcp_shown = False
    try:
        mcp_cache = os.path.join(cwd, ".claude", "state", "mcp-status.json")
        # 파일이 아예 없을 때도 백그라운드 측정 시작 (새로 병합된 폴더에서 'MCP off' 로만 뜨던 것 · 1006 A1 실측)
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
            except Exception:
                pass  # noqa: BLE001
        if os.path.exists(mcp_cache):
            import time as _time
            age = _time.time() - os.path.getmtime(mcp_cache)
            with open(mcp_cache, "r", encoding="utf-8") as f:
                ms = json.load(f)
            ok = int(ms.get("connected", 0))
            fail = int(ms.get("failed", 0))
            # 1h 넘으면 백그라운드 재측정 (SessionStart 에서만 갱신돼 며칠 세션엔 91h 전 값이 떴다)
            #   창 없음 · 10분 안 재실행 방지 마커 · 렌더는 기다리지 않음 (claude mcp list ~30s)
            if age > 3600:
                try:
                    mk = os.path.join(cwd, ".claude", "state", "mcp-refresh.started")
                    if not os.path.exists(mk) or _time.time() - os.path.getmtime(mk) > 600:
                        open(mk, "w").close()
                        import subprocess as _sp
                        _sp.Popen(["bash", os.path.join(cwd, ".claude", "scripts", "refresh-mcp-status.sh")],
                                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, stdin=_sp.DEVNULL,
                                  creationflags=(0x08000000 | 0x00000008) if os.name == "nt" else 0)
                except Exception:
                    pass  # noqa: BLE001
            # 4h 넘으면 몇 시간 전 값인지 적는다 (예전 "?" 는 뜻이 안 보였다)
            stale = f" ({int(age // 3600)}h 전)" if age > 14400 else ""
            tot = ok + fail
            tail.append((f"MCP {ok}/{tot}" if not fail else f"[!] MCP {ok}/{tot} ({fail} 실패)") + stale)
            mcp_shown = True
    except Exception:
        pass  # noqa: BLE001
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
                    tail.append(f"재사용 {cnt} ({rate:.0f}%)")
                # orca hit 카운터 (activations · tasks)
                try:
                    a = c.execute("SELECT COUNT(*) FROM activations").fetchone()
                    t = c.execute(
                        "SELECT COUNT(*) FROM tasks WHERE status IN "
                        "('locked','pending','in_progress','waiting_approval')"
                    ).fetchone()
                    ac = int(a[0]) if a else 0
                    tk = int(t[0]) if t else 0
                    # 칸 안에 '·' 를 또 쓰면 칸 구분과 섞인다 · task 0 은 표시 안 함
                    if ac:
                        tail.append(f"orca {ac}")
                    if tk:
                        tail.append(f"task {tk}")
                except Exception:
                    pass  # noqa: BLE001
                # AI 비용은 별도 line3 로 분리 (여기서는 append X)
                pass
    except Exception:
        pass  # noqa: BLE001
    # 2026-10-02: 아래 3개는 orca.db 와 무관 — DB 없는 PC 에서도 표시 (전엔 db 블록 안에 갇혀 사라짐)
    # 2026-10-12: Agent 진행률 추가
    # 에이전트는 상태 줄이 아니라 전용 7번째 줄 (gauges['agents'])
    try:
        # Cache hit rate (prompt cache 절감)
        # stdin prompt_cache.hit_ratio (Claude Code 실측) 우선, 없으면 jsonl 계산
        _pc = (data or {}).get("prompt_cache") or {}
        _hr = _pc.get("hit_ratio")
        _cr = float(_hr) * 100 if isinstance(_hr, (int, float)) else _CACHE_HIT_RATE
        if _cr > 0:
            tail.append(f"cache {_cr:.0f}%")
        # 최근 24h error·warn 카운트
        _e, _w, _top = recent_log_issues(cwd)
        if _e:
            tail.append(("[!] " if _e > 20 else "") + f"오류 {_e}" + (f" ({_top})" if _top else ""))
        if _w:
            tail.append(f"경고 {_w}")
        # 하드코딩 감사 결과 (별도 캐시)
        try:
            aud = os.path.join(cwd, ".claude", "state", "hardcoded-audit.json")
            if os.path.exists(aud):
                with open(aud, "r", encoding="utf-8") as f:
                    a = json.load(f)
                st = a.get("status", "?")
                tot = int(a.get("total_hits", 0))
                if st == "PASS":
                    tail.append("하드코딩 0")
                elif st == "CRITICAL":
                    tail.append(f"[!] 하드코딩 {tot}")
                else:
                    tail.append(f"하드코딩 {tot}")
        except Exception:
            pass  # noqa: BLE001
    except Exception:
        pass  # noqa: BLE001

    # AI 비용 line3 (세션 · 현월 · 년간 · KRW 병기)
    # 2026-09-05: 세션 비용은 Claude Code 가 cost.total_cost_usd 로 준다(정확한 값).
    #   jsonl 을 단가표로 되짚어 계산하던 근사치보다 이쪽이 맞다. 월·년간은 여전히
    #   이 프로젝트 jsonl 합산이라 "(이 프로젝트)" 라벨을 유지한다.
    global _SESSION_COST
    _delta = 0.0  # 이 세션의 (공식값 - jsonl 추정) — 월·년 합계 안의 세션 몫도 공식값으로 교체
    try:
        _c = (data or {}).get("cost") or {}
        if isinstance(_c.get("total_cost_usd"), (int, float)):
            _official = float(_c["total_cost_usd"])
            _delta = _official - _SESSION_COST
            _SESSION_COST = _official
    except Exception:
        pass  # noqa: BLE001
    rate = float(os.environ.get("USD_KRW_RATE", "1350"))
    monthly = (_MONTHLY_COST + _delta) if _MONTHLY_COST > 0 else _SESSION_COST
    yearly = (_YEARLY_COST + _delta) if _YEARLY_COST > 0 else monthly
    import datetime as _dt2
    cur_m = _dt2.datetime.now().month
    if _SESSION_COST > 0.001 or monthly > 0.001 or yearly > 0.001:
        def _krw(usd):
            v = usd * rate
            return f"₩{int(v):,}" if v >= 1 else f"₩{v:.0f}"
        # 2026-09-05: monthly_cost·yearly_cost 는 **이 프로젝트 폴더의 jsonl 만** 합산한다
        #   (statusline_context.py 의 monthly_cost(cwd) 참고). 그래서 창마다 값이 다르다 —
        #   lottoclaude 는 9월 $2,306, orchestration_v1 은 같은 날 $14. 둘 다 맞는 값인데
        #   라벨이 없어서 계정 전체 청구액으로 읽혔다. 범위를 적어 둔다.
        line3 = (
            f"세션 ${_SESSION_COST:,.2f} ({_krw(_SESSION_COST)}) · "
            f"{cur_m}월 ${monthly:,.2f} ({_krw(monthly)}) · "
            f"연간 ${yearly:,.2f} ({_krw(yearly)})"
        )
    else:
        line3 = ""

    # ------------------------------------------------------------------
    # 2026-09-05: Claude Code 가 statusline 입력으로 **진짜 사용량**을 준다.
    #   rate_limits.five_hour / seven_day 의 used_percentage 와 resets_at 이
    #   /status 화면과 같은 값이다(실측: 세션 15% resets 12:20pm, 주간 2% resets Sep 10 8am).
    #   그동안 이 스크립트는 그걸 못 받는 줄 알고 jsonl 을 세서 근사치를 만들고 있었다 —
    #   세션은 5시간 창 추정, 주간은 "프로젝트 응답 건수 / 임의 분모" 라 /status 와 안 맞았다.
    #   받은 값이 있으면 그것을 쓴다. 없을 때만 아래 자체 계산으로 물러난다.
    def _fmt_reset(ts):
        try:
            dt = _dt.datetime.fromtimestamp(int(ts))
        except Exception:
            return ""
        today = _dt.date.today()
        clock = dt.strftime("%I:%M%p").lstrip("0").lower()
        if dt.date() == today:
            return clock
        return dt.strftime("%b ") + str(dt.day) + " " + clock

    # 2026-09-07: rate_limits 가 **매 렌더마다 오는 것이 아니다** (실측).
    #   세션 첫 렌더(첫 API 응답 전)·일부 렌더에서는 키 자체가 없다. 그때 아래 자체 계산으로
    #   물러나면 "주간 이 프로젝트 응답 232건 (7일 · 한도 미설정)" 처럼 **다른 지표**가 튀어나와
    #   "고쳤다더니 또 그 문구" 로 읽혔다 (2026-09-07 사용자 지적).
    #   -> 마지막으로 받은 실값을 계정 단위로 캐시해 두고, 안 올 때는 그 값을 쓴다.
    #      캐시도 없으면 숫자를 지어내지 말고 "집계 대기" 로 비운다 (헌장 A2).
    _rl_cache = os.path.join(os.path.expanduser("~"), ".claude", "state", "rate-limits.json")

    def _read_rl(d):
        """페이로드에서 유효한 rate_limits 만 뽑는다. 없으면 None."""
        rl = (d or {}).get("rate_limits") or {}
        out = {}
        for k in ("five_hour", "seven_day"):
            v = rl.get(k) or {}
            if isinstance(v.get("used_percentage"), (int, float)):
                out[k] = {"used_percentage": float(v["used_percentage"]),
                          "resets_at": v.get("resets_at")}
        return out or None

    # 2026-10-14: 세션(five_hour)·주간(seven_day)은 **같이 오지 않을 때가 있다**(실측: 주간만 온 렌더).
    #   종전엔 「하나라도 오면 그것만 쓰고 캐시를 통째로 덮었다」 → 안 온 쪽이 화면에서 빠지고
    #   캐시에서도 지워져 «나왔다 안 나왔다» 했다. -> 키별로 합친다: 온 것은 새 값, 안 온 것은 캐시.
    import time as _time
    fresh = _read_rl(data) or {}
    cached, c_ts = {}, {}
    try:
        with open(_rl_cache, "r", encoding="utf-8") as _f:
            c = json.load(_f)
        cached = _read_rl(c) or {}
        c_ts = c.get("key_ts") or {k: float(c.get("ts") or 0) for k in cached}
    except Exception:
        pass
    now = _time.time()
    rl, key_ts = {}, {}
    for k in ("five_hour", "seven_day"):
        if k in fresh:
            rl[k], key_ts[k] = fresh[k], now
        elif k in cached:
            rl[k], key_ts[k] = cached[k], float(c_ts.get(k) or 0)
    if fresh:
        try:
            os.makedirs(os.path.dirname(_rl_cache), exist_ok=True)
            with open(_rl_cache, "w", encoding="utf-8") as _f:
                json.dump({"rate_limits": rl, "ts": now, "key_ts": key_ts}, _f)
        except Exception:
            pass
    rl_age = max([now - key_ts[k] for k in key_ts if k not in fresh] or [0.0])
    rl = rl or None

    if rl:
        try:
            os.makedirs(os.path.dirname(_rl_cache), exist_ok=True)
            import time as _time
            with open(_rl_cache, "w", encoding="utf-8") as _f:
                json.dump({"rate_limits": rl, "ts": _time.time()}, _f)
        except Exception:
            pass  # noqa: BLE001
    else:
        try:
            import time as _time
            with open(_rl_cache, "r", encoding="utf-8") as _f:
                c = json.load(_f)
            cached = _read_rl(c)
            if cached:
                rl = cached
                rl_age = max(0.0, _time.time() - float(c.get("ts") or 0))
        except Exception:
            rl = None

    if rl:
        # 캐시가 30분 넘게 묵었으면 값 뒤에 ~ 를 붙여 "직전 실값" 임을 밝힌다.
        mark = "~" if rl_age > 1800 else ""
        fh = rl.get("five_hour") or {}
        sd = rl.get("seven_day") or {}
        if "used_percentage" in fh:
            pct = fh["used_percentage"]
            r = _fmt_reset(fh.get("resets_at"))
            session_gauge = ("세션 " + _bar(pct) + f" {pct:.0f}%{mark}"
                             + (f" (reset {r})" if r else ""))
        if "used_percentage" in sd:
            pct = sd["used_percentage"]
            r = _fmt_reset(sd.get("resets_at"))
            week_gauge = ("주간 " + _bar(pct) + f" {pct:.0f}%{mark}"
                          + (f" (reset {r})" if r else ""))
    else:
        # 실값도 캐시도 없다 = 아직 한 번도 못 받았다. 다른 지표로 대체하지 않는다.
        session_gauge = "세션 (집계 대기)"
        week_gauge = "주간 (집계 대기)"

    # fast 추천 뱃지 — 주간 budget 보호 · 토큰 compact 임박만 OFF
    # 세션 % (five_hour) 는 quota 임박 지표 · fast on/off 와 무관 (reset 기다리면 됨)
    # ★기준 (사용자 확정 2026-10-06 — 임의 변경 금지):
    #   주간 ≥80%  → [!] fast OFF (주간 N%)
    #   주간 50~79% → fast OFF (주간 N% 보호)
    #   토큰 ≥80%  → fast OFF (토큰 N% · compact 임박)
    #   그 외       → fast ON
    # ANSI 색 (/clear 유도용 · Claude 가 slash command 자동 실행 불가 → 사용자 눈에 띄게)
    _RED = "\033[1;31m"; _YEL = "\033[1;33m"; _RST = "\033[0m"
    fast_badge = ""  # 2026-10-16 사용자 지시 — fast·/clear 표시는 상태 줄이 아니라 토큰 줄 옆 (기준은 동결 · 위치만)
    try:
        _wp = float((rl or {}).get("seven_day", {}).get("used_percentage", 0))
        _tp = float((data or {}).get("_ctx_pct", 0))
        if _tp >= 95:
            fast_badge = (f"{_RED}[!!] /clear 권장 (토큰 {_tp:.0f}% · 작업 끝났으면 즉시){_RST}")
        elif _tp >= 80:
            fast_badge = (f"{_YEL}[!] /clear 권장 (토큰 {_tp:.0f}% · compact 임박){_RST}")
        elif _wp >= 80:
            fast_badge = (f"{_RED}[!!] fast OFF (주간 {_wp:.0f}%){_RST}")
        elif _wp >= 50:
            fast_badge = (f"{_YEL}fast OFF (주간 {_wp:.0f}% 보호){_RST}")
        else:
            fast_badge = ("fast ON")
    except Exception:
        pass  # noqa: BLE001

    # 디자인·개발 룰 위반 지수 (rule-adherence.json cache · 10분 TTL · ~14ms)
    design_line = ""
    dev_line = ""
    try:
        # ★★★1006 — **파일은 부모(저장소 루트)에 있고 cwd 는 하위 폴더다.**
        #   실측: cwd=…/Project1.5 인데 rule-adherence.json 은
        #   …/C.ICM_Agent_Go/.claude/state/ 에만 있다 → 디자인·개발 줄이 비었다.
        #   ★★그래서 statusline 이 때로는 6줄, 때로는 3~4줄로 나왔다 —
        #     Claude Code 가 주는 cwd 가 루트일 때만 맞았던 것이다.
        #   ★부모로 거슬러 찾는다(최대 4단) — 루트가 어디든 동작해야 한다.
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
                # 2026-10-07 — 집계 파일이 옛 판(0건 키 없음)이거나 비어 있어도(세션 없는 상위 폴더)
                #   항목 전부를 0 으로 채워 줄 자체가 사라지지 않게 한다 (A.RMS·A2 실측).
                _ALL = {"design": ("이모지", "여백", "버전관리", "산출물기한"),
                        "dev": ("증명지시", "미반영", "전수조사skip")}
                c90 = {**{k: 0 for k in _ALL.get(section_name, ())}, **c90}
                if not c90: return ""
                # 2026-10-06 사용자 지시 — 같은 항목은 어느 프로젝트에서나 같은 색 (건수로 색 바꾸지 않음).
                #   항목 이름만 고정 색으로 강조 · 숫자·구분자는 기본색 · 0건도 표시.
                # 2026-10-12 사용자 지시 — 순서도 세션마다 바뀌면 안 됨. count DESC 정렬 X · 고정 순서.
                _HUE = {"여백": "35", "산출물기한": "33", "버전관리": "36", "이모지": "34",
                        "전수조사skip": "31", "증명지시": "33", "미반영": "35"}
                _ORDER = {
                    "design": ["산출물기한", "이모지", "여백", "버전관리"],
                    "dev":    ["전수조사skip", "미반영", "증명지시"],
                }
                def _hl(k):
                    return f"\033[1;{_HUE.get(k, '37')}m{k}\033[0m"
                order = _ORDER.get(section_name, list(c90.keys()))
                # 고정 순서 먼저, 매핑 밖 항목은 뒤에 count DESC 로 붙임 (신규 카테고리 대응)
                seen = set(order)
                extras = sorted([k for k in c90.keys() if k not in seen], key=lambda k: -c90[k])
                parts = [f"{_hl(k)} {c90[k]}" for k in (order + extras) if k in c90]
                return " · ".join(parts) + f" · \033[1m재발률\033[0m {rr}%"
            design_line = _fmt("design", _ra.get("design") or {})
            dev_line    = _fmt("dev", _ra.get("dev") or {})
    except Exception:
        pass  # noqa: BLE001

    # 최종 조립 - session_gauge 는 별도 반환 (main 에서 token_line 과 합침)
    line2_parts = []
    if week_gauge:
        line2_parts.append(week_gauge)
    if tail:
        line2_parts.extend(tail)
    line2 = " - ".join(line2_parts)
    return {"session": session_gauge, "line2": line2, "line3": line3,
            "week": week_gauge, "tail": tail, "agents": agent_str, "fast": fast_badge, "cost": line3,
            "design": design_line, "dev": dev_line}


def main() -> None:
    # [함정 4] 예외 나도 rc=0 + 빈 게이지
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    # 진단용 - 마지막 stdin 원문 (필드 실측 근거)
    try:
        _cwd0 = data.get("cwd") or ""
        if _cwd0:
            with open(os.path.join(_cwd0, ".claude", "state", "statusline-stdin.json"),
                      "w", encoding="utf-8") as _f:
                json.dump(data, _f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # noqa: BLE001

    model_id = ""
    try:
        model_id = (data.get("model") or {}).get("id") or ""
    except Exception:
        pass  # noqa: BLE001

    session_id = data.get("session_id") or ""
    # ★★★1006 — **Claude Code 는 `cwd` 가 아니라 `workspace.current_dir` 로 준다.**
    #   실측: 이 줄이 빈 문자열을 내서 design·dev·cost 줄이 **전부 비었고**,
    #   statusline 이 「토큰/한도/상태/비용」 4줄(또는 1줄)로만 나왔다.
    #   ★그런데 바깥 `except Exception` 이 「측정 전」만 찍어 **원인이 안 보였다**
    #     (조용한 폴백 — 실패에 소리가 없으면 아무도 못 고친다 · A7).
    #   ★두 이름을 모두 본다 — 호스트가 어느 쪽으로 줘도 동작해야 한다.
    cwd = (data.get("cwd")
           or (data.get("workspace") or {}).get("current_dir")
           or (data.get("workspace") or {}).get("project_dir")
           or os.getcwd() or "")

    # ★★★1006 — **cwd 를 «.claude 를 가진 저장소 루트»로 올린다(정본 1곳).**
    #   실측: 이 파일에서 `os.path.join(cwd, ".claude", …)` 가 **8곳**이다
    #   (logs · orca.db ×2 · mcp-status · mcp-refresh · refresh 스크립트 ·
    #    hardcoded-audit · state). cwd 가 하위 폴더면 **그 8곳이 전부** 빈 값이 되어
    #   디자인·개발·비용·MCP 줄이 사라진다 — 그래서 statusline 이 때로 3줄이었다.
    #   ★★한 곳씩 고치면 반드시 또 빠진다(⑥) — 그래서 **cwd 를 한 번 정규화**한다.
    #   ★판정은 «.claude 폴더가 있는가» — 프로젝트 구조를 지어내지 않는다.
    if cwd:
        _p = os.path.abspath(cwd)
        for _ in range(5):
            if os.path.isdir(os.path.join(_p, "plugins")) and os.path.isdir(os.path.join(_p, ".claude")):  # kit 설치 루트 기준
                cwd = _p
                break
            _u = os.path.dirname(_p)
            if _u == _p:
                break
            _p = _u

    # 상한 정본 = Claude Code 가 주는 context_window.context_window_size. 없을 때만 표 추정.
    _cw = data.get("context_window") or {}
    if isinstance(_cw.get("context_window_size"), int) and _cw["context_window_size"] > 0:
        limit, exact_model = _cw["context_window_size"], True
    else:
        limit, exact_model = pick_limit(model_id)

    # 2026-10-01: 이름표 추정보다 Claude Code 가 주는 실제 상한이 정본이다.
    #   model.id 가 "claude-opus-5-5"([1m] 없음)인 1M 세션이 claude-opus-5 항목에 걸려
    #   200K 로 기록됐고, 시작 직후 231K 에서 "116% 즉시 compact" 허위 경보가 났다.
    try:
        cw = int((data.get("context_window") or {}).get("context_window_size") or 0)
        if cw > 0:
            limit, exact_model = cw, True
    except Exception:
        pass  # noqa: BLE001

    # 해결된 컨텍스트 상한을 SoT 로 공유 - jsonl 의 message.model 은 "claude-opus-5" 로만
    # 기록되어 "[1m]" 접미가 없다. hook(inject-compact-reminder)은 stdin 의 model.id 를
    # 볼 수 없어 1M 세션을 200K 로 오판했다 (193K/200K = 93% 허위 경보, 2026-09-05 실측).
    if exact_model and cwd:
        try:
            import datetime as _dtc
            # 2026-09-10: cwd 는 **세션의 현재 디렉터리**다. `cd nextjs` 한 순간
            #   nextjs/.claude/state/ 가 생겼고, 그렇게 만들어진 엉뚱한 .claude 가
            #   8곳까지 늘어 있었다. 루트 표식을 찾아 올라간다.
            st = os.path.join(_project_root(cwd), ".claude", "state")
            os.makedirs(st, exist_ok=True)
            with open(os.path.join(st, "context-limit.json"), "w", encoding="utf-8") as _f:
                json.dump({"model": model_id, "limit": limit,
                           "ts": _dtc.datetime.now().isoformat(timespec="seconds")}, _f)
        except Exception:
            pass  # noqa: BLE001

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
            pass  # noqa: BLE001

    # 3줄 구조: [시각 + 토큰 + 세션] / [주간 + MCP + 재사용 + 하드코딩 + orca + cache + err] / [AI 비용]
    import datetime as _dt3
    clock = _dt3.datetime.now().strftime("%m/%d %H:%M")
    token_line = render(tokens, limit, exact_model, no_usage)
    # fast 로직용: 토큰 context % inject (compact 임박 판정)
    if isinstance(data, dict) and limit and tokens:
        data["_ctx_pct"] = min(100.0, tokens / limit * 100.0)
    gauges = extra_gauges(cwd, data) if cwd else {"session": "", "line2": "", "line3": ""}
    SEP = " · "

    # 2026-10-06 사용자 지시 — 줄 머리말 이모지 유지 기준 ("그 기준은 지켜야지").
    #   VS16(U+FE0F) 이 필요 없는 단일 코드포인트만 쓴다 (터미널마다 폭이 달라져 정렬이 깨짐).
    ICONS = {"토큰": "🧠", "한도": "⏳", "디자인": "🎨", "개발": "💻", "상태": "📡", "서브": "🤖", "비용": "💰"}

    def _row(label: str, body: str) -> str:
        # 머리말 표시폭 9칸(이모지 2 + 공백 1 + 한글 최대 6)으로 맞춤 → 모든 줄 내용이 같은 칸에서 시작
        import unicodedata as _ud
        head = f"{ICONS[label]} {label}" if label in ICONS else label
        w = sum(2 if _ud.east_asian_width(ch) in ("W", "F") else 1 for ch in head)
        # 머리말 굵은 청록 · 구분선 회색 (이모지 머리말 색 강조 — 사용자 지시 1006)
        return "\033[1;36m" + head + "\033[0m" + " " * max(0, 9 - w) + " \033[90m│\033[0m " + body

    out = [_row("토큰", f"{token_line}{SEP}{clock}" + (SEP + gauges["fast"] if gauges.get("fast") else ""))]
    lim = [x for x in (gauges.get("session"), gauges.get("week")) if x]
    if lim:
        out.append(_row("한도", SEP.join(lim)))
    if gauges.get("design"):
        out.append(_row("디자인", gauges["design"]))
    if gauges.get("dev"):
        out.append(_row("개발", gauges["dev"]))
    if gauges.get("tail"):
        out.append(_row("상태", SEP.join(gauges["tail"])))
    # 서브 줄은 항상 (7줄 확정 · 2026-10-16) — 도는 에이전트가 없으면 회색 «실행 중 없음»
    out.append(_row("서브", gauges.get("agents") or "[90m실행 중 없음[0m"))
    cost = gauges.get("cost") or ""
    if cost:
        out.append(_row("비용", cost.replace("AI 비용(이 프로젝트) ", "")))
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
