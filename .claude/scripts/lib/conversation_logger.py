"""
conversation_logger ???몄뀡 ????붿빟 ???濡쒕뱶
?ъ슜: SessionStart / UserPromptSubmit / Stop hook ?먯꽌 ?몄텧
洹쇨굅: ?ъ슜??吏??(2026-09-02) ???몄뀡 ?딄린硫?memory ?좎떎
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


_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  turn INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT,
  tokens INTEGER,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  tags TEXT
);
CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conv_ts ON conversations(ts);

CREATE TABLE IF NOT EXISTS session_summary (
  session_id TEXT PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  turns INTEGER,
  summary TEXT,
  key_decisions TEXT,
  files_touched TEXT,
  tokens_total INTEGER,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS problem_solutions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT,
  problem TEXT NOT NULL,
  category TEXT,
  keywords TEXT,
  approach TEXT,
  solution TEXT,
  files_modified TEXT,
  commands_run TEXT,
  verified INTEGER DEFAULT 0,
  reusable_score INTEGER DEFAULT 5,
  problem_hash TEXT UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_sol_cat ON problem_solutions(category);
"""


def _conn() -> sqlite3.Connection:
    """?뚯씠釉붿씠 ?놁쑝硫?留뚮뱾怨??곕떎.

    2026-09-08: ?ㅽ궎留덈? 留뚮뱶??二쇱껜媛 ?꾨Т???놁뼱 conversations /
    session_summary / problem_solutions 媛 3媛쒖썡媛?誘몄깮???곹깭???
    留???'no such table' 濡?二쎌쑝硫댁꽌 ?몄뀡 ?멸퀎媛 ?듭㎏濡??딄꼈??
    """
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    except sqlite3.Error:
        pass
    return conn


def _session_id_from_transcript() -> str:
    """?꾩옱 ?몄뀡??transcript ?뚯씪紐?uuid)???몄뀡 id 濡??대떎.

    2026-09-08: ???ㅽ뻾 ?섍꼍??CLAUDE_CODE_SESSION_ID 媛 ?놁뼱 紐⑤뱺 ?몄뀡??    'unknown' ???⑹뼱由щ줈 ??λ릱?? load ??"?먭린 ?몄뀡 ?쒖쇅" 議곌굔?대씪
    ??긽 0嫄?-> ?멸퀎媛 ?곸썝?????먮떎. ?뚯씪紐낆? ?ㅼ륫 媛?ν븳 媛믪씠??
    """
    try:
        enc = str(PROJECT_ROOT).replace(":", "-").replace("\\", "-").replace("/", "-")
        d = Path.home() / ".claude" / "projects" / enc
        if not d.is_dir():
            cands = list((Path.home() / ".claude" / "projects").glob("*"))
            d = max((x for x in cands if x.is_dir() and PROJECT_ROOT.name in x.name),
                    key=lambda x: x.stat().st_mtime, default=None)
            if d is None:
                return ""
        files = list(d.glob("*.jsonl"))
        if not files:
            return ""
        return max(files, key=lambda f: f.stat().st_mtime).stem
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""


def get_session_id() -> str:
    return (
        os.environ.get("CLAUDE_CODE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or _session_id_from_transcript()
        or "unknown"
    )


def save_turn(role: str, content: str, tags: str | None = None) -> None:
    """UserPrompt-Assistant-Tool ?????turn ???"""
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
    """媛??理쒓렐 N ?몄뀡???붿빟 濡쒕뱶 - SessionStart ?꾨＼?꾪듃 二쇱엯??"""
    with _conn() as c:
        rows = c.execute(
            """SELECT session_id, started_at, turns, summary, key_decisions
               FROM session_summary
               WHERE session_id != ?
               ORDER BY updated_at DESC LIMIT ?""",
            (get_session_id(), n_sessions),
        ).fetchall()
    if not rows:
        return ""
    parts = ["## ?댁쟾 ?몄뀡 ?붿빟 (?먮룞 濡쒕뱶)\n"]
    for sid, st, turns, summ, dec in rows:
        parts.append(f"### {st} - {turns} turns - session={sid[:8]}")
        if summ:
            parts.append(summ)
        if dec:
            parts.append(f"**寃곗젙**: {dec}")
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

