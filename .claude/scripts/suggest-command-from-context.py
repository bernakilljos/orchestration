#!/usr/bin/env python
"""
suggest-command-from-context.py ??2以뫢?以??먮룞 諛쒕룞 (context 湲곕컲)

2以? orca.db 理쒓렐 10 turn ?ㅼ썙??cluster ??異붿쿇 command top3
3以? rule-adherence 吏???꾧퀎 珥덇낵 ??媛뺤젣 紐⑤뱶 諛쒕룞

異쒕젰: systemMessage JSON (UserPromptSubmit hook 媛 ?몄텧)
TTL 5遺?(留?turn ?ш퀎??X)
"""
from __future__ import annotations
import json, os, sqlite3, sys, time, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
RA = ROOT / ".claude" / "state" / "rule-adherence.json"
CACHE = ROOT / ".claude" / "state" / "context-suggest.json"
TTL = 300  # 5遺?

# command 留ㅽ븨 (?ㅼ썙??cluster ??top command)
CLUSTERS = {
    "install-mcp":       r'MCP|?뚮윭洹몄씤|install mcp|mcp ?ㅼ튂',
    "sec-scan":          r'蹂댁븞|security|由щ럭|review|audit',
    "exec_status":       r'?뚯빱|??heartbeat|orca|?곹깭',
    "pdf-generate":      r'PDF|pdf|?쒕챸|?뚰꽣留덊겕',
    "excel-make":        r'?묒?|xlsx|?ㅽ봽?덈뱶',
    "word-make":         r'?뚮뱶|docx|臾몄꽌 留뚮뱾',
    "ai-system-stages":  r'猷⑦떞|?쒖뒪?쒗솕|?먮룞??泥댁씤|AI ?쒖뒪???먭?諛쒖쟾',
    "install-to":        r'install to|諛고룷 ????ㅻⅨ 癒몄떊',
    "guard-save":        r'?좏겙|?몄뀡|?ㅻ깄?????,
    "resume-last-24h":   r'蹂듦뎄|?댁뼱???대뵒??硫덉땄',
}

# 3以??꾧퀎
THRESHOLDS = {
    "design_recur_pct":  40,   # ?붿옄???щ컻瑜?40%+ ??/arch-auto 媛뺤젣
    "misreflect_count":  5,    # 誘몃컲??5嫄? ??verify-after-edit 媛뺤젣
    "session_pct":       80,   # ?몄뀡 80%+ ??/guard-save 媛뺤젣 (statusline fast 猷??뺥빀)
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return {}
    cnt = Counter()
    for (txt,) in rows:
        if not txt: continue
        for cmd, pat in CLUSTERS.items():
            if re.search(pat, txt, re.IGNORECASE):
                cnt[cmd] += 1
    return dict(cnt.most_common(3))

def check_thresholds():
    """3以????꾧퀎 珥덇낵 泥댄겕 ??forced 紐⑤뱶 由ы꽩"""
    forced = []
    if RA.exists():
        try:
            ra = json.loads(RA.read_text(encoding="utf-8"))
            design_recur = (ra.get("design") or {}).get("recur_rate_pct", 0)
            if design_recur >= THRESHOLDS["design_recur_pct"]:
                forced.append(f"[3以?媛뺤젣] ?붿옄???щ컻瑜?{design_recur}% ??40% ??"
                              f"?ㅼ쓬 ?붿옄???묒뾽 ??/arch-auto쨌app-ui-standard.md 諛섎뱶???곸슜")
            misreflect = (ra.get("dev") or {}).get("counts_90d", {}).get("誘몃컲??, 0)
            if misreflect >= THRESHOLDS["misreflect_count"]:
                forced.append(f"[3以?媛뺤젣] 誘몃컲??{misreflect}嫄???5嫄???"
                              f"?섏젙 吏????verify-after-edit-mandatory.md 利앸챸 泥댁씤 100%")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass
    return forced

def check_reusable_solutions():
    """4以???problem_solutions ?ъ궗??top1 異붿쿇"""
    if not DB.exists(): return []
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT problem, solution, reusable_score, category "
            "FROM problem_solutions "
            "WHERE verified=1 AND reusable_score>=8 "
            "ORDER BY reusable_score DESC, ts DESC LIMIT 2"
        ).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return []
    out = []
    for prob, sol, score, cat in rows:
        prob_s = (prob or "")[:50].replace("\n", " ")
        sol_s = (sol or "")[:60].replace("\n", " ")
        out.append(f"[4以??ъ궗????score} {cat}] ?좎궗 怨쇨굅: '{prob_s}...' ??'{sol_s}...'")
    return out

def check_external_signals():
    """5以???git/task/MCP/budget ?몃? ?좏샇 ?좎젣 ?뚮┝"""
    import subprocess
    signals = []
    # git unstaged 留롮쓬
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=3)
        n_unstaged = len([l for l in (r.stdout or "").splitlines() if l.strip()])
        if n_unstaged >= 10:
            signals.append(f"[5以??몃??좏샇] git unstaged {n_unstaged}嫄???10 ??"
                           f"/validate쨌/sec-scan ??commit 臾띔린 沅뚯옣")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    # tasks pending 留롮쓬
    try:
        pending_dir = ROOT / ".claude" / "tasks" / "pending"
        if pending_dir.is_dir():
            n_pending = len(list(pending_dir.glob("*.md")))
            if n_pending >= 5:
                signals.append(f"[5以??몃??좏샇] pending task {n_pending}嫄???5 ??"
                               f"/approvals ?먮뒗 /exec_status 濡????뺣━")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    # MCP fail
    try:
        mcp = ROOT / ".claude" / "state" / "mcp-status.json"
        if mcp.exists():
            m = json.loads(mcp.read_text(encoding="utf-8"))
            fail = int(m.get("failed", 0))
            if fail >= 3:
                signals.append(f"[5以??몃??좏샇] MCP fail {fail}嫄???3 ??"
                               f"/mcp_dev-install쨌/mcp_data-install ?ъ젏寃")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    # budget ?꾨컯 (rate-limits.json seven_day >= 70%)
    try:
        rl = Path(os.path.expanduser("~")) / ".claude" / "state" / "rate-limits.json"
        if rl.exists():
            d = json.loads(rl.read_text(encoding="utf-8"))
            wp = (d.get("rate_limits") or {}).get("seven_day", {}).get("used_percentage", 0)
            if wp >= 70:
                signals.append(f"[5以??몃??좏샇] 二쇨컙 budget {wp:.0f}% ??70% ??"
                               f"/token-stats + /guard-save + fast OFF 媛뺤젣")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    return signals

def main():
    if cache_valid() and os.environ.get("FORCE") != "1":
        try:
            data = json.loads(CACHE.read_text(encoding="utf-8"))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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


def _sanitize(s):
    if not isinstance(s, str): return s
    return s.encode("utf-8", "replace").decode("utf-8", "replace")

def _emit(data):
    parts = []
    top3 = data.get("top3_from_recent_10turns") or {}
    if top3:
        reco = " 쨌 ".join(f"/{k}({v})" for k, v in top3.items())
        parts.append(f"[2以?異붿쿇 쨌 理쒓렐 10turn ?⑦꽩] {reco}")
    for f in data.get("forced_modes") or []:
        parts.append(f)
    for r in data.get("reusable_solutions") or []:
        parts.append(r)
    for s in data.get("external_signals") or []:
        parts.append(s)
    if not parts: return
    ctx = _sanitize("\\n".join(_sanitize(p) for p in parts))
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx
        }
    }, ensure_ascii=True))

if __name__ == "__main__":
    try: main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)

