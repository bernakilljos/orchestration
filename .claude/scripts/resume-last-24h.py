#!/usr/bin/env python
"""
resume-last-24h.py ??理쒓렐 24?쒓컙 ?묒뾽 ?먮룞 蹂듦뎄 ?붿빟
SessionStart hook 媛 ?몄텧 ??stdout ??systemMessage 濡?二쇱엯

異쒕젰 ?ы븿:
- 理쒓렐 24h session_summary (?댁젣쨌?ㅻ뒛)
- 誘몄셿猷?task (.claude/tasks pending쨌in_progress)
- 理쒓렐 24h git commit
- 留덉?留?user 吏??3媛?(???蹂듭썝)
- session-snapshot.md ??理쒖쥌 ?곹깭

?ъ슜???ㅻ챸 ?붽뎄 X 쨌 ?щ??끒룸찓紐⑤━ 醫낅즺 蹂듦뎄 ?먮룞.
"""
from __future__ import annotations
import json, os, sqlite3, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
TASKS = ROOT / ".claude" / "tasks"
SNAPSHOT = ROOT / ".claude" / "context-cache" / "session-snapshot.md"

CUTOFF_HOURS = 24
MAX_CHARS = 3000  # systemMessage ??＜ 諛⑹?

def _h(title: str) -> str:
    return f"\n## {title}\n"

def section_session_summary() -> str:
    if not DB.exists(): return ""
    cutoff = (datetime.now() - timedelta(hours=CUTOFF_HOURS)).isoformat()
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT session_id, ended_at, turns, summary, key_decisions "
            "FROM session_summary WHERE updated_at >= ? "
            "ORDER BY updated_at DESC LIMIT 5",
            (cutoff,)
        ).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""
    if not rows: return ""
    out = [_h(f"理쒓렐 {CUTOFF_HOURS}h ?몄뀡 ?붿빟")]
    for sid, ended, turns, summ, dec in rows:
        s = (summ or "")[:400]
        d = (dec or "")[:200]
        out.append(f"- **[{sid[:8]}]** turns={turns} 쨌 ended={ended or '吏꾪뻾以?}")
        if s: out.append(f"  summary: {s}")
        if d: out.append(f"  decisions: {d}")
    return "\n".join(out)

def section_pending_tasks() -> str:
    if not TASKS.exists(): return ""
    pending = []
    for d in ("pending", "in_progress", "locks"):
        p = TASKS / d
        if p.is_dir():
            for f in sorted(p.glob("*.md"))[:5]:
                try:
                    first = f.read_text(encoding="utf-8", errors="replace").splitlines()[0][:80]
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                    first = "?"
                pending.append(f"  - [{d}] {f.name} ??{first}")
    if not pending: return ""
    return _h(f"誘몄셿猷?task") + "\n".join(pending)

def section_recent_commits() -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "log", f"--since={CUTOFF_HOURS} hours ago",
             "--oneline", "-10"],
            capture_output=True, text=True, encoding="utf-8", timeout=5
        )
        lines = (r.stdout or "").strip().splitlines()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""
    if not lines: return ""
    return _h(f"理쒓렐 {CUTOFF_HOURS}h commit") + "\n".join(f"  - {ln}" for ln in lines[:10])

def section_last_prompts() -> str:
    if not DB.exists(): return ""
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content, ts FROM conversations WHERE role='user' "
            "ORDER BY ts DESC LIMIT 3"
        ).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""
    if not rows: return ""
    out = [_h("留덉?留??ъ슜??吏??3媛?(理쒖떊?믨낵嫄?")]
    for txt, ts in rows:
        snip = (txt or "")[:150].replace("\n", " ")
        out.append(f"  - [{ts}] {snip}")
    return "\n".join(out)

def section_snapshot() -> str:
    if not SNAPSHOT.exists(): return ""
    try:
        txt = SNAPSHOT.read_text(encoding="utf-8", errors="replace")[:600]
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""
    if not txt.strip(): return ""
    return _h("理쒖쥌 ?몄뀡 ?ㅻ깄??) + txt

def _sanitize(s: str) -> str:
    """unpaired surrogate ?쒓굅 (orca.db ??cp949?봴tf-8 蹂???붿옱) ??Claude API lone surrogate 400 諛⑹?"""
    if not isinstance(s, str): return s
    return s.encode("utf-8", "replace").decode("utf-8", "replace")

def main():
    parts = [
        section_session_summary(),
        section_pending_tasks(),
        section_recent_commits(),
        section_last_prompts(),
        section_snapshot(),
    ]
    body = "\n".join(p for p in parts if p).strip()
    if not body: return  # 蹂듦뎄??嫄??놁쓬
    body = _sanitize(body)[:MAX_CHARS]
    header = f"# ?먮룞 蹂듦뎄 (理쒓렐 {CUTOFF_HOURS}h 쨌 resume-last-24h.py)\n"
    header += "?щ??끒룸찓紐⑤━ 醫낅즺 ???묒뾽 ?곹깭. ?ъ슜???ㅻ챸 ?붽뎄 X 쨌 諛붾줈 ?댁뼱??\n"
    # ?ъ슜??吏??'--json' ??SessionStart hook JSON 吏곸젒 諛섑솚 (shell escape ?고쉶)
    if "--json" in sys.argv:
        import json as _j
        print(_j.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": _sanitize(header + body)
            }
        }, ensure_ascii=True))
    else:
        print(header + body)

if __name__ == "__main__":
    try: main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)

