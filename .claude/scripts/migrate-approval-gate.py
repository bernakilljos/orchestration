"""orca.db schema migration: approval gate (v2).

tasks 테이블에 approval_state, risk_category, risk_detail, approved_at, approved_by 컬럼 추가.
schema_version 2 기록.
"""
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))
from state_db import get_db_path


def column_exists(conn, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    db_path = get_db_path()
    if not db_path.exists():
        print(f"[migrate] DB 없음 — init-state-db.py 먼저 실행: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    try:
        # 현재 version 확인
        cur = conn.execute("SELECT MAX(version) FROM schema_version")
        current = cur.fetchone()[0] or 0
        if current >= 2:
            print(f"[migrate] schema_version={current} (이미 마이그레이션 됨)")
            return
        print(f"[migrate] schema {current} -> 2: approval gate 컬럼 추가")

        # tasks 테이블에 컬럼 추가 (IF NOT EXISTS 직접 X — column_exists 체크)
        cols_to_add = [
            ("approval_state", "TEXT DEFAULT 'not_required'"),
            ("risk_category", "TEXT"),
            ("risk_detail", "TEXT"),
            ("approved_at", "INTEGER"),
            ("approved_by", "TEXT"),
        ]
        for col, decl in cols_to_add:
            if not column_exists(conn, "tasks", col):
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {decl}")
                print(f"  + {col} {decl}")
            else:
                print(f"  ~ {col} 이미 있음")

        # 인덱스
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_approval "
            "ON tasks(approval_state) WHERE approval_state = 'waiting'"
        )
        print("  + idx_tasks_approval (waiting only)")

        # schema_version 2 기록
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (2, ?)",
            (int(time.time()),)
        )
        conn.commit()
        print("[migrate] schema_version=2 적용 완료")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
