"""
audit_file_write — 파일 생성/변경 시 orca.db.file_audit 자동 기록
호출: PostToolUse Write/Edit hook 에서 파일 경로 인자로 실행
근거: 운영 grade 파일 관리 (2026-09-02)
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
    except Exception:
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
    except Exception as e:
        sys.stderr.write(f"[audit-file] {e}\n")


BANNED_PATTERNS = [
    (r"^\d+\.(jpg|jpeg|png|gif|pdf|docx?|pptx?|xlsx?|txt|md)$", "순수 숫자 파일명"),
    (r"[_-]?(copy|Copy)[_-]?", "'copy' 접미사·중간사"),
    (r"[_-]?(final|FINAL)[_-]?", "'final' 접미사"),
    (r"[_-]v\d+[._-]?", "'v<number>' 버전 접미사 (feedback_no_version_suffix)"),
    (r"^(untitled|Untitled|new|new_file|temp|tmp)[._-]", "일반명 (untitled/new/temp)"),
    (r"\s", "공백 포함"),
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
    # 명명 검증 (write/create 시)
    if action in ("create", "write"):
        warns = check_name(path)
        for w in warns:
            print(w, file=sys.stderr)
