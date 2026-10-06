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
                    # ★★★1002 — `ts` 를 **jsonl 의 실제 대화 시각**으로 넣는다.
                    #   종전엔 `ts` 를 안 주어 `DEFAULT CURRENT_TIMESTAMP`(=적재 시각)가
                    #   들어갔다. 그래서 **과거 세션 전부가 「오늘」로 찍혔다** —
                    #   실측 1002: 세션 5개가 전부 `07:55:47` 한 시각이었고(9/30 세션 포함),
                    #   7일·30일·90일 창이 **같은 404건**이 됐다.
                    #   ★★그 결과 statusline 의 **재발률이 구조적으로 100%** 였다
                    #     (산식 = 7일 ÷ 30일). 「항상 재발한다」가 아니라
                    #     **「비교할 과거가 없다」**였다 — 분모가 분자와 같은 집합이다.
                    #   ★A10: 두 창이 같은 자로 잰 값이면 비교가 답이 아니라 소음이다.
                    _ts = (rec.get("timestamp") or "").strip()
                    if _ts:
                        # "2026-09-30T00:22:04.982Z" → "2026-09-30 00:22:04"
                        _ts = _ts.replace("T", " ").replace("Z", "").split(".")[0]
                    if _ts:
                        c.execute(
                            "INSERT INTO conversations"
                            "(session_id,turn,role,content,content_hash,tokens,ts) "
                            "VALUES(?,?,?,?,?,?,?)",
                            (sid, turn, rtype, text, ch, len(text) // 4, _ts)
                        )
                    else:
                        # ★시각이 없으면 **지어내지 않는다** — 기본값(적재 시각)에 맡기고
                        #   그 사실이 집계에서 «오늘»로 보이는 것은 감수한다(A8).
                        c.execute(
                            "INSERT INTO conversations"
                            "(session_id,turn,role,content,content_hash,tokens) "
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
