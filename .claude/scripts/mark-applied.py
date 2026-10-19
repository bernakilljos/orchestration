#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""mark-applied — hit (검색됨) vs apply (실제 적용) 구분 (2026-10-19 #2).

사용자 명시: "검색됐다는 것과 실제 적용했다는 것은 다름"

사용:
  python mark-applied.py <id>       # apply_count++ 수동 마킹
  python mark-applied.py stats      # hit vs apply 비율 통계
"""
from __future__ import annotations
import os, sqlite3, sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")


def mark(sid: int):
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        c.execute(
            "UPDATE problem_solutions SET apply_count = COALESCE(apply_count,0) + 1, last_apply_ts=? WHERE id=?",
            (now, sid)
        )
    print(f"[OK] solution #{sid} apply_count++ ({now})")


def stats():
    with sqlite3.connect(DB) as c:
        rows = c.execute(
            "SELECT COUNT(*), SUM(hit_count), SUM(apply_count) FROM problem_solutions"
        ).fetchone()
        total, hits, applies = rows[0], rows[1] or 0, rows[2] or 0
        # 적용률 (apply/hit) — 검색된 것 중 실제 적용된 비율
        ratio = (applies / hits * 100) if hits else 0
        # 적용된 적 있는 solution 수
        with_apply = c.execute("SELECT COUNT(*) FROM problem_solutions WHERE apply_count > 0").fetchone()[0]
    print(f"=== Hit vs Apply 구분 (2026-10-19 #2) ===")
    print(f"- 총 solutions: {total}")
    print(f"- 누적 hit (검색됨): {hits}")
    print(f"- 누적 apply (실제 적용): {applies}")
    print(f"- 적용률 (apply/hit): {ratio:.1f}%")
    print(f"- 적용된 solution 수: {with_apply}/{total}")
    print()
    print("note: 검색만 됐다 ≠ 적용 성공 · apply_count 가 신뢰 지표")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "stats":
        stats()
    else:
        try:
            mark(int(args[0]))
        except ValueError:
            print(f"ID 숫자 필요: {args[0]}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
