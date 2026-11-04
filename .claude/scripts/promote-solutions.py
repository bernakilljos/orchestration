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


def ensure_columns(c):
    """hit_count · last_hit_ts 컬럼 + 진행 위치 표 (없으면)."""
    cols = [r[1] for r in c.execute("PRAGMA table_info(problem_solutions)").fetchall()]
    if "hit_count" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN hit_count INTEGER DEFAULT 0")
    if "last_hit_ts" not in cols:
        c.execute("ALTER TABLE problem_solutions ADD COLUMN last_hit_ts TIMESTAMP")
    # 2026-11-04 감사 재현 (조회 1·2·3 → 집계 1·3·6): 진행 위치를 별도 파일에 두면 DB 반영과 어긋나고,
    # 로그 앞 256B 해시는 짧은 로그에 줄이 붙을 때마다 바뀌어 처음부터 다시 셌다 → DB 안에 같은 트랜잭션으로 저장
    c.execute("CREATE TABLE IF NOT EXISTS promote_cursor (log TEXT PRIMARY KEY, head_len INTEGER, head TEXT,"
              " offset INTEGER)")


def scan_hits(c):
    """lookup-history.log 에서 지난 실행 이후 새로 붙은 '완성된 줄' 의 solution_id hit 카운트 (멱등).
    같은 파일 판정 = 지난번에 기록한 길이(head_len)만큼의 앞부분 해시 · 다르거나 짧아지면 교체된 새 파일로 보고 처음부터.
    반환: (hits, (head_len, head, offset)) · 진행 위치는 호출자가 DB 갱신과 같은 트랜잭션에 저장."""
    if not LOG.exists():
        return {}, None
    data = LOG.read_bytes()
    end = data.rfind(b"\n") + 1                    # 쓰는 중인 마지막 줄은 다음 실행에
    hl = min(256, end)
    new_cur = (hl, hashlib.sha256(data[:hl]).hexdigest(), end)
    row = c.execute("SELECT head_len, head, offset FROM promote_cursor WHERE log=?", (LOG.name,)).fetchone()
    if row is None:                                 # 첫 실행: 기존 hit_count 에 이미 로그가 들어 있으므로 위치만 기록
        return {}, new_cur
    head_len, head, offset = row
    same = offset <= end and head_len <= len(data) and hashlib.sha256(data[:head_len]).hexdigest() == head
    begin = offset if same else 0
    hits = {}
    pat = re.compile(r"solution[_\s#]*(\d+)|problem_hash[=:\s]+([a-f0-9]{8,})")
    for line in data[begin:end].decode("utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            key = m.group(1) or m.group(2)
            hits[key] = hits.get(key, 0) + 1
    return hits, new_cur


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
    hits_by_id, cursor = scan_hits(c)
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
    if cursor:                                   # 점수 갱신과 진행 위치를 한 트랜잭션으로 (중간 실패 시 둘 다 롤백)
        c.execute("INSERT INTO promote_cursor (log, head_len, head, offset) VALUES (?, ?, ?, ?) "
                  "ON CONFLICT(log) DO UPDATE SET head_len=excluded.head_len, head=excluded.head, offset=excluded.offset",
                  (LOG.name, *cursor))
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
