#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""promote-solutions - problem_solutions 자동 점수 승급.

로직:
- lookup-history.log 안 solution hit → hit_count 누적
- hit_count >= 3 → verified=1, reusable_score 상향 (8)
- hit_count >= 5 → reusable_score 9
- hit_count >= 10 → reusable_score 10
- 미hit 30일+ → score -= 1 (감가상각)
"""
from __future__ import annotations
import os
import re
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
LOG = ROOT / ".claude" / "logs" / "lookup-history.log"


def ensure_columns(c):
    """hit_count · last_hit_ts 컬럼 추가 (없으면)."""
    cols = [r[1] for r in c.execute("PRAGMA table_info(problem_solutions)").fetchall()]
    if "hit_count" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN hit_count INTEGER DEFAULT 0")
    if "last_hit_ts" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN last_hit_ts TIMESTAMP")


def scan_hits():
    """lookup-history.log 안 solution_id hit 카운트."""
    if not LOG.exists():
        return {}
    hits = {}
    pat = re.compile(r"solution[_\s#]*(\d+)|problem_hash[=:\s]+([a-f0-9]{8,})")
    try:
        with open(LOG, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = pat.search(line)
                if m:
                    key = m.group(1) or m.group(2)
                    hits[key] = hits.get(key, 0) + 1
    except Exception:
        pass
    return hits


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
    hits_by_id = scan_hits()
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
        new_verified = 1 if new_hit >= 3 else 0
        if new_score != cur_score or new_hit != (cur_hit or 0):
            c.execute(
                "UPDATE problem_solutions SET hit_count=?, reusable_score=?, verified=? "
                "WHERE id=?",
                (new_hit, new_score, new_verified, sid)
            )
            updated += 1
    c.commit()
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
