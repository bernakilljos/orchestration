"""
conversation_logger — 세션 대화·요약 저장/로드
사용: SessionStart / UserPromptSubmit / Stop hook 에서 호출
근거: 사용자 지적 (2026-09-02) — 세션 끊기면 memory 유실
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "orca.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))


def get_session_id() -> str:
    return (
        os.environ.get("CLAUDE_CODE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or "unknown"
    )


def save_turn(role: str, content: str, tags: str | None = None) -> None:
    """UserPrompt·Assistant·Tool 대화 한 turn 저장."""
    if not content:
        return
    sid = get_session_id()
    ch = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
    tokens = len(content) // 4  # rough
    with _conn() as c:
        turn = (
            c.execute(
                "SELECT COALESCE(MAX(turn),0)+1 FROM conversations WHERE session_id=?",
                (sid,),
            ).fetchone()[0]
            or 1
        )
        c.execute(
            """INSERT INTO conversations(session_id,turn,role,content,content_hash,tokens,tags)
               VALUES(?,?,?,?,?,?,?)""",
            (sid, turn, role, content[:8000], ch, tokens, tags),
        )
        c.commit()


def save_session_summary(summary: str, key_decisions: str = "", files: str = "") -> None:
    sid = get_session_id()
    with _conn() as c:
        turns = c.execute(
            "SELECT COUNT(*) FROM conversations WHERE session_id=?", (sid,)
        ).fetchone()[0]
        tokens = c.execute(
            "SELECT COALESCE(SUM(tokens),0) FROM conversations WHERE session_id=?", (sid,)
        ).fetchone()[0]
        c.execute(
            """INSERT INTO session_summary(session_id,started_at,ended_at,turns,summary,key_decisions,files_touched,tokens_total)
               VALUES(?,COALESCE((SELECT started_at FROM session_summary WHERE session_id=?),CURRENT_TIMESTAMP),
                      CURRENT_TIMESTAMP,?,?,?,?,?)
               ON CONFLICT(session_id) DO UPDATE SET
                 ended_at=CURRENT_TIMESTAMP, turns=excluded.turns,
                 summary=excluded.summary, key_decisions=excluded.key_decisions,
                 files_touched=excluded.files_touched, tokens_total=excluded.tokens_total,
                 updated_at=CURRENT_TIMESTAMP""",
            (sid, sid, turns, summary[:4000], key_decisions[:4000], files[:2000], tokens),
        )
        c.commit()


def load_recent_context(n_sessions: int = 3, max_chars: int = 3000) -> str:
    """가장 최근 N 세션의 요약 로드 · SessionStart 프롬프트 주입용."""
    with _conn() as c:
        rows = c.execute(
            """SELECT session_id, started_at, turns, summary, key_decisions
               FROM session_summary
               WHERE session_id != ?
               ORDER BY ended_at DESC LIMIT ?""",
            (get_session_id(), n_sessions),
        ).fetchall()
    if not rows:
        return ""
    parts = ["## 이전 세션 요약 (자동 로드)\n"]
    for sid, st, turns, summ, dec in rows:
        parts.append(f"### {st} · {turns} turns · session={sid[:8]}")
        if summ:
            parts.append(summ)
        if dec:
            parts.append(f"**결정**: {dec}")
        parts.append("")
    out = "\n".join(parts)
    return out[:max_chars]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "save-turn":
        role = sys.argv[2]
        content = sys.stdin.read()
        save_turn(role, content)
        print(f"[ok] saved {role} turn")
    elif cmd == "save-summary":
        payload = json.loads(sys.stdin.read() or "{}")
        save_session_summary(
            payload.get("summary", ""),
            payload.get("key_decisions", ""),
            payload.get("files", ""),
        )
        print("[ok] session summary saved")
    elif cmd == "load":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        print(load_recent_context(n_sessions=n))
    else:
        print("usage: conversation_logger.py {save-turn <role>|save-summary|load [N]}")
