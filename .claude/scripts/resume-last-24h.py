#!/usr/bin/env python
"""
resume-last-24h.py — 최근 24시간 작업 자동 복구 요약
SessionStart hook 가 호출 → stdout → systemMessage 로 주입

출력 포함:
- 최근 24h session_summary (어제·오늘)
- 미완료 task (.claude/tasks pending·in_progress)
- 최근 24h git commit
- 마지막 user 지시 3개 (대화 복원)
- session-snapshot.md 안 최종 상태

사용자 설명 요구 X · 재부팅·메모리 종료 복구 자동.
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
MAX_CHARS = 3000  # systemMessage 폭주 방지

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
    except Exception:
        return ""
    if not rows: return ""
    out = [_h(f"최근 {CUTOFF_HOURS}h 세션 요약")]
    for sid, ended, turns, summ, dec in rows:
        s = (summ or "")[:400]
        d = (dec or "")[:200]
        out.append(f"- **[{sid[:8]}]** turns={turns} · ended={ended or '진행중'}")
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
                except Exception:
                    first = "?"
                pending.append(f"  - [{d}] {f.name} — {first}")
    if not pending: return ""
    return _h(f"미완료 task") + "\n".join(pending)

def section_recent_commits() -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "log", f"--since={CUTOFF_HOURS} hours ago",
             "--oneline", "-10"],
            capture_output=True, text=True, encoding="utf-8", timeout=5
        )
        lines = (r.stdout or "").strip().splitlines()
    except Exception:
        return ""
    if not lines: return ""
    return _h(f"최근 {CUTOFF_HOURS}h commit") + "\n".join(f"  - {ln}" for ln in lines[:10])

def section_last_prompts() -> str:
    if not DB.exists(): return ""
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content, ts FROM conversations WHERE role='user' "
            "ORDER BY ts DESC LIMIT 3"
        ).fetchall()
    except Exception:
        return ""
    if not rows: return ""
    out = [_h("마지막 사용자 지시 3개 (최신→과거)")]
    for txt, ts in rows:
        snip = (txt or "")[:150].replace("\n", " ")
        out.append(f"  - [{ts}] {snip}")
    return "\n".join(out)

def section_snapshot() -> str:
    if not SNAPSHOT.exists(): return ""
    try:
        txt = SNAPSHOT.read_text(encoding="utf-8", errors="replace")[:600]
    except Exception:
        return ""
    if not txt.strip(): return ""
    return _h("최종 세션 스냅샷") + txt

def main():
    parts = [
        section_session_summary(),
        section_pending_tasks(),
        section_recent_commits(),
        section_last_prompts(),
        section_snapshot(),
    ]
    body = "\n".join(p for p in parts if p).strip()
    if not body: return  # 복구할 거 없음
    body = body[:MAX_CHARS]
    header = f"# 자동 복구 (최근 {CUTOFF_HOURS}h · resume-last-24h.py)\n"
    header += "재부팅·메모리 종료 전 작업 상태. 사용자 설명 요구 X · 바로 이어서.\n"
    print(header + body)

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
