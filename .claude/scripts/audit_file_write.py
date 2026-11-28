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
# R375 Hook 응답성 (2026-11-28 실측: orca.db 잠금 시 Edit 마다 약 7.5초 정지) → state_db.bounded_insert
#   (전체 마감 ORCA_HOOK_DB_TIMEOUT 검증값 · 못 쓴 기록은 스풀에 보관 후 다음에 이어 씀 · 조용한 유실 X)
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
import state_db as _sdb  # noqa: E402 — 훅 기록 정본 (전체 마감 · 스풀)
_DB_TIMEOUT = _sdb.hook_db_budget()
HASH_MAX_BYTES = 8 * 1024 * 1024      # 감사 해시 읽기 상한 (넘으면 'skip:size' — 실제 해시가 아님을 값으로 표시)
HASH_BUDGET_SEC = 0.3                  # 해시 시간 상한 (넘으면 'skip:time')


def _sha16(path: Path) -> str:
    """앞 16자리 sha256 · 읽기량(HASH_MAX_BYTES)·시간(HASH_BUDGET_SEC) 상한 · 넘으면 'skip:size'/'skip:time' · 읽기 실패 ''."""
    import time as _t
    try:
        t0 = _t.monotonic()
        h, n = hashlib.sha256(), 0
        with path.open("rb") as f:
            while chunk := f.read(65536):
                n += len(chunk)
                if n > HASH_MAX_BYTES:
                    return "skip:size"
                if _t.monotonic() - t0 > HASH_BUDGET_SEC:
                    return "skip:time"
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return ""


def log_action(action: str, path: str, reason: str = "", actor: str = "claude") -> None:
    p = Path(path)
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown")
    try:                                       # stat 오류(권한·경합 삭제)도 기록을 막지 않음
        st = p.stat() if p.is_file() else None
    except OSError:
        st = None
    size = st.st_size if st else 0
    ph = _sha16(p) if st else ""
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")   # 발생 시각 명시 (스풀 재생 때 시각 보존)
    r = _sdb.bounded_insert(DB, "file_audit", [(
        "INSERT INTO file_audit(ts,session_id,action,path,size,hash,actor,reason) VALUES(?,?,?,?,?,?,?,?)",
        [ts, sid, action, str(p), size, ph, actor, reason[:500]])])
    if not r.startswith("ok"):
        sys.stderr.write(f"[audit-file] {r}\n")
    return r


BANNED_PATTERNS = [
    (r"^\d+\.(jpg|jpeg|png|gif|pdf|docx?|pptx?|xlsx?|txt|md)$", "순수 숫자 파일명"),
    (r"[_-]?(copy|Copy)[_-]?", "'copy' 접미사-중간사"),
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
