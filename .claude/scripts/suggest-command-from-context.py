#!/usr/bin/env python
"""
suggest-command-from-context.py — 2중·3중 자동 발동 (context 기반)

2중: orca.db 최근 10 turn 키워드 cluster → 추천 command top3
3중: rule-adherence 지수 임계 초과 → 강제 모드 발동

출력: systemMessage JSON (UserPromptSubmit hook 가 호출)
TTL 5분 (매 turn 재계산 X)
"""
from __future__ import annotations
import json, os, sqlite3, sys, time, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
RA = ROOT / ".claude" / "state" / "rule-adherence.json"
CACHE = ROOT / ".claude" / "state" / "context-suggest.json"
TTL = 300  # 5분

# command 매핑 (키워드 cluster → top command)
CLUSTERS = {
    "install-mcp":       r'MCP|플러그인|install mcp|mcp 설치',
    "sec-scan":          r'보안|security|리뷰|review|audit',
    "exec_status":       r'워커|큐|heartbeat|orca|상태',
    "pdf-generate":      r'PDF|pdf|서명|워터마크',
    "excel-make":        r'엑셀|xlsx|스프레드',
    "word-make":         r'워드|docx|문서 만들',
    "ai-system-stages":  r'루틴|시스템화|자동화 체인|AI 시스템|자가발전',
    "install-to":        r'install to|배포 대상|다른 머신',
    "guard-save":        r'토큰|세션|스냅샷|저장',
    "resume-last-24h":   r'복구|이어서|어디서 멈춤',
}

# 3중 임계
THRESHOLDS = {
    "design_recur_pct":  40,   # 디자인 재발률 40%+ → /arch-auto 강제
    "misreflect_count":  5,    # 미반영 5건+ → verify-after-edit 강제
    "session_pct":       80,   # 세션 80%+ → /guard-save 강제 (statusline fast 룰 정합)
}

def cache_valid():
    if not CACHE.exists(): return False
    return (time.time() - CACHE.stat().st_mtime) < TTL

def analyze_recent_turns():
    if not DB.exists(): return {}
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content FROM conversations WHERE role='user' "
            "ORDER BY ts DESC LIMIT 10"
        ).fetchall()
    except Exception:
        return {}
    cnt = Counter()
    for (txt,) in rows:
        if not txt: continue
        for cmd, pat in CLUSTERS.items():
            if re.search(pat, txt, re.IGNORECASE):
                cnt[cmd] += 1
    return dict(cnt.most_common(3))

def check_thresholds():
    """3중 — 임계 초과 체크 → forced 모드 리턴"""
    forced = []
    if RA.exists():
        try:
            ra = json.loads(RA.read_text(encoding="utf-8"))
            design_recur = (ra.get("design") or {}).get("recur_rate_pct", 0)
            if design_recur >= THRESHOLDS["design_recur_pct"]:
                forced.append(f"[3중 강제] 디자인 재발률 {design_recur}% ≥ 40% → "
                              f"다음 디자인 작업 시 /arch-auto·app-ui-standard.md 반드시 적용")
            misreflect = (ra.get("dev") or {}).get("counts_90d", {}).get("미반영", 0)
            if misreflect >= THRESHOLDS["misreflect_count"]:
                forced.append(f"[3중 강제] 미반영 {misreflect}건 ≥ 5건 → "
                              f"수정 지시 시 verify-after-edit-mandatory.md 증명 체인 100%")
        except Exception:
            pass
    return forced

def check_reusable_solutions():
    """4중 — problem_solutions 재사용 top1 추천"""
    if not DB.exists(): return []
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT problem, solution, reusable_score, category "
            "FROM problem_solutions "
            "WHERE verified=1 AND reusable_score>=8 "
            "ORDER BY reusable_score DESC, ts DESC LIMIT 2"
        ).fetchall()
    except Exception:
        return []
    out = []
    for prob, sol, score, cat in rows:
        prob_s = (prob or "")[:50].replace("\n", " ")
        sol_s = (sol or "")[:60].replace("\n", " ")
        out.append(f"[4중 재사용 ★{score} {cat}] 유사 과거: '{prob_s}...' → '{sol_s}...'")
    return out

def check_external_signals():
    """5중 — git/task/MCP/budget 외부 신호 선제 알림"""
    import subprocess
    signals = []
    # git unstaged 많음
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=3)
        n_unstaged = len([l for l in (r.stdout or "").splitlines() if l.strip()])
        if n_unstaged >= 10:
            signals.append(f"[5중 외부신호] git unstaged {n_unstaged}건 ≥ 10 → "
                           f"/validate·/sec-scan 후 commit 묶기 권장")
    except Exception:
        pass
    # tasks pending 많음
    try:
        pending_dir = ROOT / ".claude" / "tasks" / "pending"
        if pending_dir.is_dir():
            n_pending = len(list(pending_dir.glob("*.md")))
            if n_pending >= 5:
                signals.append(f"[5중 외부신호] pending task {n_pending}건 ≥ 5 → "
                               f"/approvals 또는 /exec_status 로 큐 정리")
    except Exception:
        pass
    # MCP fail
    try:
        mcp = ROOT / ".claude" / "state" / "mcp-status.json"
        if mcp.exists():
            m = json.loads(mcp.read_text(encoding="utf-8"))
            fail = int(m.get("failed", 0))
            if fail >= 3:
                signals.append(f"[5중 외부신호] MCP fail {fail}건 ≥ 3 → "
                               f"/mcp_dev-install·/mcp_data-install 재점검")
    except Exception:
        pass
    # budget 임박 (rate-limits.json seven_day >= 70%)
    try:
        rl = Path(os.path.expanduser("~")) / ".claude" / "state" / "rate-limits.json"
        if rl.exists():
            d = json.loads(rl.read_text(encoding="utf-8"))
            wp = (d.get("rate_limits") or {}).get("seven_day", {}).get("used_percentage", 0)
            if wp >= 70:
                signals.append(f"[5중 외부신호] 주간 budget {wp:.0f}% ≥ 70% → "
                               f"/token-stats + /guard-save + fast OFF 강제")
    except Exception:
        pass
    return signals

def main():
    if cache_valid() and os.environ.get("FORCE") != "1":
        try:
            data = json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if data: _emit(data); return

    top3 = analyze_recent_turns()
    forced = check_thresholds()
    reusable = check_reusable_solutions()
    externals = check_external_signals()
    data = {
        "generated_at": time.time(),
        "top3_from_recent_10turns": top3,
        "forced_modes": forced,
        "reusable_solutions": reusable,
        "external_signals": externals,
    }
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    _emit(data)

def _emit(data):
    parts = []
    top3 = data.get("top3_from_recent_10turns") or {}
    if top3:
        reco = " · ".join(f"/{k}({v})" for k, v in top3.items())
        parts.append(f"[2중 추천 · 최근 10turn 패턴] {reco}")
    for f in data.get("forced_modes") or []:
        parts.append(f)
    for r in data.get("reusable_solutions") or []:
        parts.append(r)
    for s in data.get("external_signals") or []:
        parts.append(s)
    if not parts: return
    ctx = "\\n".join(parts)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx
        }
    }, ensure_ascii=False))

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
