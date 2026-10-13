"""
audit_file_write ???뚯씪 ?앹꽦/蹂寃???orca.db.file_audit ?먮룞 湲곕줉
?몄텧: PostToolUse Write/Edit hook ?먯꽌 ?뚯씪 寃쎈줈 ?몄옄濡??ㅽ뻾
洹쇨굅: ?댁쁺 grade ?뚯씪 愿由?(2026-09-02)
"""
from __future__ import annotations
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT_ROOT / ".claude" / "state" / "orca.db"


def _sha16(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()[:16]
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return ""


def log_action(action: str, path: str, reason: str = "", actor: str = "claude") -> None:
    p = Path(path)
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown")
    size = p.stat().st_size if p.exists() else 0
    ph = _sha16(p) if p.exists() else ""
    try:
        with sqlite3.connect(str(DB)) as c:
            c.execute(
                """INSERT INTO file_audit(session_id,action,path,size,hash,actor,reason)
                   VALUES(?,?,?,?,?,?,?)""",
                (sid, action, str(p), size, ph, actor, reason[:500]),
            )
            c.commit()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        sys.stderr.write(f"[audit-file] {e}\n")


BANNED_PATTERNS = [
    (r"^\d+\.(jpg|jpeg|png|gif|pdf|docx?|pptx?|xlsx?|txt|md)$", "?쒖닔 ?レ옄 ?뚯씪紐?),
    (r"[_-]?(copy|Copy)[_-]?", "'copy' ?묐???以묎컙??),
    (r"[_-]?(final|FINAL)[_-]?", "'final' ?묐???),
    (r"[_-]v\d+[._-]?", "'v<number>' 踰꾩쟾 ?묐???(feedback_no_version_suffix)"),
    (r"^(untitled|Untitled|new|new_file|temp|tmp)[._-]", "?쇰컲紐?(untitled/new/temp)"),
    (r"\s", "怨듬갚 ?ы븿"),
]


def check_name(path: str) -> list[str]:
    import re
    name = Path(path).name
    warns = []
    for pat, msg in BANNED_PATTERNS:
        if re.search(pat, name):
            warns.append(f"[{msg}] {name}")
    return warns


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: audit_file_write.py <action> <path> [reason]")
        sys.exit(0)
    action = sys.argv[1]
    path = sys.argv[2]
    reason = sys.argv[3] if len(sys.argv) > 3 else ""
    log_action(action, path, reason)
    # 紐낅챸 寃利?(write/create ??
    if action in ("create", "write"):
        warns = check_name(path)
        for w in warns:
            print(w, file=sys.stderr)

