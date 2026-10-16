"""상태줄의 «[!] 오류 N · 경고 M» 을 세션이 스스로 처리하게 — 새 오류가 생기면 다음 프롬프트에 1회 주입.

근거 2026-10-16: 상태줄에 «오류 73 (orca-10min-loop.log) · 경고 71» 이 사흘간 떠 있었는데
아무 세션도 손대지 않았다 (사용자 «이렇게 나오면 확인하고 해결해줘야지»). 숫자는 상태줄에만 있고
세션 컨텍스트에는 없어서 Claude 가 볼 방법이 없었다.

규칙 (상태줄 recent_log_issues 와 같은 기준 · 시각 있는 줄만 · 최근 24h):
  - 오류: 새 종류(파일+메시지 지문)가 생기면 주입
  - 경고: 같은 종류가 24h 에 20건 넘게 반복되면 주입 (일회성 경고는 잡음)
  - 이미 알린 종류는 건수가 2배 이상 늘고 6시간 지났을 때만 다시 알린다
상태: .claude/state/log-errors-seen.json
"""
from __future__ import annotations

import glob
import json
import os
import re
import time

from _common import is_loop_prompt_raw, project_path

SKIP = {"bash_commands.log", "lookup-history.log", "user-prompt-history.log", "conversation-save.log",
        "deflection-detect.log", "emotion-response.log", "mcp-health.log", "prompt-dispatch.log", "hook-trace.log",
        "tool-dispatch.log"}
TS_RE = re.compile(r"(20\d\d)-(\d\d)-(\d\d)[ T](\d\d):(\d\d):(\d\d)")
ERR_RE = re.compile(r"\b(ERROR|FAIL|Traceback|\[err\]|\[!!\])", re.I)
WARN_RE = re.compile(r"\b(WARN|\[skip\])", re.I)
WARN_REPEAT_MIN = 20       # BASIS: agreed(2026-10-16, 10분 주기 작업이 24h 에 144회 → 20회+ 반복이면 일회성이 아니다)
RENOTIFY_SEC = 6 * 3600    # BASIS: agreed(2026-10-16, 같은 오류를 매 프롬프트 넣으면 잡음 — 하루 4번 이내)


def _sig(line: str) -> str:
    """시각·숫자·경로 차이를 지운 메시지 지문 (같은 종류 오류를 한 줄로 묶는다)."""
    s = TS_RE.sub("", line)
    s = re.sub(r"\[[0-9T:.\-+ ]+\]", "", s)
    s = re.sub(r"\d+", "#", s)
    return " ".join(s.split())[:120]


def _scan(log_dir: str):
    cutoff = time.time() - 86400
    found: dict[str, dict] = {}
    for lp in glob.glob(os.path.join(log_dir, "*.log")):
        name = os.path.basename(lp)
        if name in SKIP:
            continue
        try:
            if os.path.getmtime(lp) < cutoff:
                continue
            with open(lp, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-500:]
        except OSError:
            continue
        for ln in lines:
            e, w = ERR_RE.search(ln), WARN_RE.search(ln)
            if not (e or w):
                continue
            m = TS_RE.search(ln)
            if not m or time.mktime(tuple(map(int, m.groups())) + (0, 0, -1)) < cutoff:
                continue
            key = name + " | " + _sig(ln)
            d = found.setdefault(key, {"kind": "ERROR" if e else "WARN", "n": 0, "file": name, "sample": ""})
            d["n"] += 1
            d["sample"] = ln.strip()[:200]
    return found


def run(ctx):
    if is_loop_prompt_raw(ctx.raw_stripped):
        return None
    log_dir = project_path(ctx, ".claude", "logs")
    if not os.path.isdir(log_dir):
        return None
    found = _scan(log_dir)
    if not found:
        return None
    seen_p = project_path(ctx, ".claude", "state", "log-errors-seen.json")
    try:
        with open(seen_p, "r", encoding="utf-8") as f:
            seen = json.load(f)
    except Exception:
        seen = {}
    now = time.time()
    hits = []
    for key, d in found.items():
        if d["kind"] == "WARN" and d["n"] < WARN_REPEAT_MIN:
            continue
        prev = seen.get(key)
        if prev and not (d["n"] >= 2 * prev.get("n", 1) and now - prev.get("t", 0) > RENOTIFY_SEC):
            continue
        hits.append((key, d))
    if not hits:
        return None
    for key, d in hits:
        seen[key] = {"n": d["n"], "t": now}
    try:
        os.makedirs(os.path.dirname(seen_p), exist_ok=True)
        with open(seen_p, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in seen.items() if now - v.get("t", 0) < 7 * 86400}, f, ensure_ascii=False)
    except OSError:
        pass
    hits.sort(key=lambda kd: (kd[1]["kind"] != "ERROR", -kd[1]["n"]))
    rows = [f"  - {d['kind']} ×{d['n']} ({d['file']}) {d['sample']}" for _, d in hits[:6]]
    more = f"\n  … 외 {len(hits) - 6}종" if len(hits) > 6 else ""
    return {"additionalContext": (
        "[로그 오류 자동 점검 — 상태줄 «오류/경고» 의 원인] 최근 24h 새로 생기거나 반복되는 문제:\n"
        + "\n".join(rows) + more
        + "\n★ 사용자 작업을 처리하면서 이것도 원인을 확인해 고친다 (사용자가 말하기 전에 · D6). "
          "로그만 지우는 것은 해결이 아니다 — 실행해서 재발 0 을 확인하고 보고에 1줄.")}
