#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
promote-experience — 검증된 경험을 CORE 승격 (A3).

승격 조건 (사용자 명시 "검증된 개선만"):
  1. problem_solutions 중 verified=1 AND reusable_score >= 8
  2. hit_count >= 3 (실제 재사용 입증)
  3. recurrence_improvements 중 status='VERIFIED' AND verified=1

승격 효과:
  - experience_type 를 'PROMOTED' 또는 'CORE' 로 마크
  - solution 복사하여 memory 또는 reference 로 전파 (사용자 승인 후만)

사용:
  python promote-experience.py list       # 승격 후보 조회
  python promote-experience.py mark ID    # 수동 마크 (사용자 승인)
  python promote-experience.py auto       # 자동 후보 전체 마크 (--confirm 필요)
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


def _candidates():
    with sqlite3.connect(DB) as c:
        # 1) problem_solutions
        sol_rows = c.execute(
            "SELECT id, problem, reusable_score, hit_count, verified, experience_type "
            "FROM problem_solutions "
            "WHERE verified=1 AND reusable_score >= 8 AND hit_count >= 3 "
            "AND (experience_type IS NULL OR experience_type != 'PROMOTED') "
            "ORDER BY hit_count DESC"
        ).fetchall()
        # 2) recurrence_improvements verified
        imp_rows = c.execute(
            "SELECT improvement_id, rule_id, pre_metric, post_metric, status "
            "FROM recurrence_improvements WHERE verified=1 AND status='VERIFIED'"
        ).fetchall()
    return sol_rows, imp_rows


def cmd_list():
    sol_rows, imp_rows = _candidates()
    print(f"=== 승격 후보 · solutions {len(sol_rows)} + improvements {len(imp_rows)} ===")
    print()
    print(f"[solutions] verified=1 · score≥8 · hits≥3 · PROMOTED 아님")
    for r in sol_rows:
        p = (r[1] or "")[:60]
        print(f"  #{r[0]:>3} score={r[2]} hits={r[3]} · {p}")
    print()
    print(f"[improvements] verified=1 · VERIFIED")
    for r in imp_rows:
        print(f"  #{r[0]:>3} rule={r[1]} pre={r[2]:.1f}→post={r[3]:.1f}")


def cmd_mark(args):
    sid = int(args[0])
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        c.execute(
            "UPDATE problem_solutions SET experience_type='PROMOTED', ts = ? WHERE id = ?",
            (now, sid)
        )
    print(f"[OK] solution #{sid} → PROMOTED")


def cmd_auto(args):
    if "--confirm" not in args:
        print("[GUARD] --confirm 필요 (사용자 승인 명시)")
        print("예: python promote-experience.py auto --confirm")
        sys.exit(1)
    sol_rows, _ = _candidates()
    now = datetime.now().isoformat(timespec="seconds")
    marked = 0
    with sqlite3.connect(DB) as c:
        for r in sol_rows:
            c.execute(
                "UPDATE problem_solutions SET experience_type='PROMOTED', ts=? WHERE id=?",
                (now, r[0])
            )
            marked += 1
    print(f"[OK] {marked} solutions → PROMOTED")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    args = sys.argv[2:]
    if cmd == "list":
        cmd_list()
    elif cmd == "mark":
        cmd_mark(args)
    elif cmd == "auto":
        cmd_auto(args)
    else:
        print(f"unknown: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
