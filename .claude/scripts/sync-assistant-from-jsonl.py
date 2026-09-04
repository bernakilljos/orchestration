#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sync-assistant-from-jsonl - Claude Code jsonl 에서 assistant 응답 → orca.db.conversations.

배경: Claude Code 는 assistant 응답용 hook 이 없음. Stop hook 시 jsonl 파싱해 sync.
근거: 사용자 지적 (2026-09-03) - assistant 이력 유실.
"""
from __future__ import annotations
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main() -> int:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    home = os.path.expanduser("~")
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    proj_dir = os.path.join(home, ".claude", "projects", safe)
    if not os.path.isdir(proj_dir):
        print(f"[skip] proj_dir not found: {proj_dir}")
        return 0
    db = os.path.join(cwd, ".claude", "state", "orca.db")
    if not os.path.exists(db):
        print(f"[skip] db not found: {db}")
        return 0
    c = sqlite3.connect(db)
    # 이미 저장된 content_hash (중복 방지)
    existing = set(
        r[0] for r in c.execute(
            "SELECT content_hash FROM conversations WHERE role IN ('assistant','user') "
            "AND content_hash IS NOT NULL"
        ).fetchall()
    )
    added = 0
    # 최근 5 jsonl 만 sync (부하 절감)
    files = sorted(
        glob.glob(os.path.join(proj_dir, "*.jsonl")),
        key=os.path.getmtime, reverse=True
    )[:5]
    for jp in files:
        sid = os.path.splitext(os.path.basename(jp))[0]
        try:
            with open(jp, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    rtype = rec.get("type")
                    if rtype not in ("assistant", "user"):
                        continue
                    msg = rec.get("message") or {}
                    cp = msg.get("content") or []
                    if isinstance(cp, list):
                        parts = []
                        for p in cp:
                            if isinstance(p, dict):
                                t = p.get("text") or ""
                                if t:
                                    parts.append(t)
                            elif isinstance(p, str):
                                parts.append(p)
                        text = " ".join(parts)
                    elif isinstance(cp, str):
                        text = cp
                    else:
                        text = ""
                    text = (text or "").strip()[:8000]
                    if not text:
                        continue
                    ch = hashlib.sha256(
                        text.encode("utf-8", errors="replace")
                    ).hexdigest()[:16]
                    if ch in existing:
                        continue
                    existing.add(ch)
                    turn = c.execute(
                        "SELECT COALESCE(MAX(turn),0)+1 FROM conversations WHERE session_id=?",
                        (sid,)
                    ).fetchone()[0] or 1
                    c.execute(
                        "INSERT INTO conversations(session_id,turn,role,content,content_hash,tokens) "
                        "VALUES(?,?,?,?,?,?)",
                        (sid, turn, rtype, text, ch, len(text) // 4)
                    )
                    added += 1
        except Exception as e:
            print(f"[skip jsonl] {jp}: {e}", file=sys.stderr)
    c.commit()
    print(f"[ok] jsonl sync - added {added}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[err] {e}", file=sys.stderr)
        sys.exit(0)
