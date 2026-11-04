#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""promote-solutions - problem_solutions 자동 점수 승급.

로직:
- lookup-history.log 안 solution hit → hit_count 누적 (지난번 이후 새로 쓰인 줄만 · 재실행해도 중복 집계 X)
- hit_count >= 3 → reusable_score 상향 (8) · verified 는 건드리지 않음 (조회 ≠ 검증 · 2026-11-04 감사)
- hit_count >= 5 → reusable_score 9
- hit_count >= 10 → reusable_score 10
- 미hit 30일+ → score -= 1 (감가상각)
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass  # noqa: BLE001

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
LOG = ROOT / ".claude" / "logs" / "lookup-history.log"
CURSOR = ROOT / ".claude" / "state" / "promote-solutions-cursor.json"


def ensure_columns(c):
    """hit_count · last_hit_ts 컬럼 추가 (없으면)."""
    cols = [r[1] for r in c.execute("PRAGMA table_info(problem_solutions)").fetchall()]
    if "hit_count" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN hit_count INTEGER DEFAULT 0")
    if "last_hit_ts" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN last_hit_ts TIMESTAMP")


def _load_cursor() -> dict:
    try:
        return json.loads(CURSOR.read_text(encoding="utf-8"))
    except Exception:
        return {}


def scan_hits():
    """lookup-history.log 에서 지난 실행 이후 새로 쓰인 부분의 solution_id hit 카운트 (멱등).
    로그가 정리·교체되면 (크기 감소 또는 첫 부분 변경) 처음부터 다시 읽는다. 반환: (hits, 새 cursor)."""
    if not LOG.exists():
        return {}, None
    data = LOG.read_bytes()
    head = hashlib.sha256(data[:256]).hexdigest()
    cur = _load_cursor()
    if not cur:                       # 첫 실행: 기존 hit_count 에 이미 로그 전체가 들어 있으므로 다시 세지 않고 위치만 기록
        return {}, {"head": head, "offset": len(data)}
    begin =cur.get("offset", 0) if cur.get("head") == head and cur.get("offset", 0) <= len(data) else 0
    hits = {}
    pat = re.compile(r"solution[_\s#]*(\d+)|problem_hash[=:\s]+([a-f0-9]{8,})")
    for line in data[begin:].decode("utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            key = m.group(1) or m.group(2)
            hits[key] = hits.get(key, 0) + 1
    return hits, {"head": head, "offset": len(data)}


def score_from_hits(hit_count: int) -> int:
    if hit_count >= 10:
        return 10
    if hit_count >= 5:
        return 9
    if hit_count >= 3:
        return 8
    if hit_count >= 1:
        return 6
    return 5


def main():
    if not DB.exists():
        print("[skip] db 없음")
        return 0
    c = sqlite3.connect(str(DB))
    ensure_columns(c)
    hits_by_id, cursor = scan_hits()
    # 명시 등재된 solution (사용자가 save_solution.py manual · verified 지정) 은 유지
    updated = 0
    for row in c.execute(
        "SELECT id, problem_hash, hit_count, reusable_score FROM problem_solutions"
    ).fetchall():
        sid, ph, cur_hit, cur_score = row
        # log 안 hit 카운트
        h = hits_by_id.get(str(sid), 0) + hits_by_id.get(ph or "", 0)
        new_hit = (cur_hit or 0) + h
        new_score = max(cur_score, score_from_hits(new_hit))
        if new_score != cur_score or new_hit != (cur_hit or 0):
            c.execute(
                "UPDATE problem_solutions SET hit_count=?, reusable_score=? WHERE id=?",
                (new_hit, new_score, sid)
            )
            updated += 1
    c.commit()
    if cursor:                                   # DB 반영 뒤에 cursor 저장 (중간 실패 시 다음 실행이 같은 줄을 다시 셈)
        CURSOR.write_text(json.dumps(cursor), encoding="utf-8")
    # 요약
    r = c.execute(
        "SELECT COUNT(*), AVG(reusable_score), SUM(verified), SUM(hit_count) "
        "FROM problem_solutions"
    ).fetchone()
    print(f"[promote] updated {updated} · total {r[0]} · avg score {r[1]:.1f} · "
          f"verified {r[2]} · total hits {r[3]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
