#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
adaptive-schema-migrate — Phase 1 스키마 마이그레이션 (idempotent · 안전).

적용:
  1. recurrence_events + root_cause TEXT (NULL 허용)
  2. problem_solutions + experience_type TEXT (NULL 허용 · TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE/IMPROVEMENT_CANDIDATE)
  3. recurrence_improvements 신규 테이블 (pre/post metric · verified flag · OBSERVING/VERIFIED/REJECTED/ROLLED_BACK)

원칙:
  - idempotent: 이미 있으면 skip (여러 번 실행해도 안전)
  - 기존 데이터 보존: ADD COLUMN NULL 만 사용 · DROP 금지
  - 스키마 변경 로그: schema_version 업데이트
"""
from __future__ import annotations
import sqlite3, sys, os
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")

SCHEMA_VERSION_TAG = "adaptive_v1_2026_10_19"


def _col_exists(c, table, col):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    return col in cols


def _table_exists(c, name):
    r = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


def main():
    if not os.path.exists(DB):
        print(f"[ERR] orca.db 없음: {DB}", file=sys.stderr)
        sys.exit(1)

    changes = []
    with sqlite3.connect(DB) as c:
        # 1. recurrence_events + root_cause
        if not _col_exists(c, "recurrence_events", "root_cause"):
            c.execute("ALTER TABLE recurrence_events ADD COLUMN root_cause TEXT")
            changes.append("recurrence_events + root_cause TEXT")
        else:
            print("[skip] recurrence_events.root_cause 이미 존재")

        # 2. problem_solutions + experience_type
        if not _col_exists(c, "problem_solutions", "experience_type"):
            c.execute("ALTER TABLE problem_solutions ADD COLUMN experience_type TEXT")
            changes.append("problem_solutions + experience_type TEXT")
        else:
            print("[skip] problem_solutions.experience_type 이미 존재")

        # 3. recurrence_improvements 신규 테이블
        if not _table_exists(c, "recurrence_improvements"):
            c.execute("""
                CREATE TABLE recurrence_improvements (
                    improvement_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id          TEXT NOT NULL,
                    category         TEXT,
                    problem_summary  TEXT,
                    root_cause       TEXT,
                    improvement_plan TEXT,
                    pre_metric       REAL,
                    post_metric      REAL,
                    pre_sample_size  INTEGER,
                    post_sample_size INTEGER,
                    pre_measured_at  TEXT,
                    post_measured_at TEXT,
                    verified         INTEGER DEFAULT 0,
                    status           TEXT DEFAULT 'OBSERVING',
                    ts_created       TEXT DEFAULT (datetime('now')),
                    ts_updated       TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (rule_id) REFERENCES recurrence_rules(rule_id)
                )
            """)
            c.execute("CREATE INDEX idx_imp_rule ON recurrence_improvements(rule_id)")
            c.execute("CREATE INDEX idx_imp_status ON recurrence_improvements(status)")
            changes.append("recurrence_improvements 신규 테이블 + 2 인덱스")
        else:
            print("[skip] recurrence_improvements 이미 존재")

        # 4. schema_version 업데이트 (INTEGER · auto-increment)
        if _table_exists(c, "schema_version"):
            import time as _t
            try:
                max_v = c.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
                c.execute(
                    "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
                    (max_v + 1, int(_t.time())),
                )
            except Exception as e:
                print(f"[warn] schema_version 기록 실패 (무해): {e}")

        c.commit()

    print(f"\n[OK] 적용 변경: {len(changes)}건")
    for ch in changes:
        print(f"  + {ch}")
    if not changes:
        print("  (모두 이미 존재 · no-op)")


if __name__ == "__main__":
    main()
