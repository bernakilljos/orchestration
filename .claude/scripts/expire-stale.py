#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
expire-stale — 오래된 경험 재검증·폐기 (A4).

폐기 정책 (사용자 명시 "잘못된 경험의 폐기"):
  - last_hit_ts > 90일 전 + verified=0 → re-verify 마크 (status='STALE')
  - last_hit_ts > 180일 전 + hit_count < 2 → archive (reusable_score=0)
  - verified=1 중 last_hit_ts > 90일 → re-verify 플래그만 · 즉시 archive X

사용:
  python expire-stale.py scan             # 폐기·재검증 후보 조회
  python expire-stale.py apply --confirm  # 자동 적용 (승인 필요)
"""
from __future__ import annotations
import os, sqlite3, sys
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")

STALE_DAYS = 90
ARCHIVE_DAYS = 180


def _candidates():
    now = datetime.now()
    stale_cut = (now - timedelta(days=STALE_DAYS)).isoformat()
    archive_cut = (now - timedelta(days=ARCHIVE_DAYS)).isoformat()
    with sqlite3.connect(DB) as c:
        # 재검증 후보 (90일+)
        to_reverify = c.execute(
            "SELECT id, problem, reusable_score, hit_count, last_hit_ts, verified "
            "FROM problem_solutions "
            "WHERE (last_hit_ts IS NULL OR last_hit_ts < ?) "
            "AND reusable_score >= 5"
            " ORDER BY last_hit_ts ASC NULLS FIRST LIMIT 100",
            (stale_cut,)
        ).fetchall()
        # archive 후보 (180일+ · low hit)
        to_archive = c.execute(
            "SELECT id, problem, reusable_score, hit_count, last_hit_ts "
            "FROM problem_solutions "
            "WHERE (last_hit_ts IS NULL OR last_hit_ts < ?) "
            "AND hit_count < 2 AND reusable_score < 8",
            (archive_cut,)
        ).fetchall()
    return to_reverify, to_archive


def cmd_scan():
    reverify, archive = _candidates()
    print(f"=== 폐기·재검증 후보 ===")
    print(f"- 재검증 (last_hit {STALE_DAYS}일+): {len(reverify)}건")
    for r in reverify[:5]:
        p = (r[1] or "")[:60]
        print(f"  #{r[0]:>3} score={r[2]} hits={r[3]} last={r[4]} · {p}")
    if len(reverify) > 5:
        print(f"  ... + {len(reverify) - 5}")
    print()
    print(f"- Archive (last_hit {ARCHIVE_DAYS}일+ · hits<2 · score<8): {len(archive)}건")
    for r in archive[:5]:
        p = (r[1] or "")[:60]
        print(f"  #{r[0]:>3} score={r[2]} hits={r[3]} · {p}")


def cmd_apply(args):
    if "--confirm" not in args:
        print("[GUARD] --confirm 필요 (사용자 승인 명시)")
        sys.exit(1)
    reverify, archive = _candidates()
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        # 재검증: experience_type = 'STALE' 마크
        for r in reverify:
            c.execute(
                "UPDATE problem_solutions SET experience_type='STALE' WHERE id=? "
                "AND (experience_type IS NULL OR experience_type NOT IN ('PROMOTED','ARCHIVED'))",
                (r[0],)
            )
        # archive: experience_type='ARCHIVED' · reusable_score=0
        for r in archive:
            c.execute(
                "UPDATE problem_solutions SET experience_type='ARCHIVED', reusable_score=0 "
                "WHERE id=? AND experience_type != 'PROMOTED'",
                (r[0],)
            )
    print(f"[OK] 재검증 마크 {len(reverify)}건 · Archive {len(archive)}건")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    args = sys.argv[2:]
    if cmd == "scan":
        cmd_scan()
    elif cmd == "apply":
        cmd_apply(args)
    else:
        print(f"unknown: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
