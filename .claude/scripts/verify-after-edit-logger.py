#!/usr/bin/env python3
# verify-after-edit-logger.py — PostToolUse Edit/Write 시 "왜 안 됐어" 재지시 패턴 감지
# 2026-10-13 신설 · 목표 C · Auto regression tracking

import os
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
DB_PATH = Path(PROJECT_DIR) / '.claude/state/orca.db'
LOG_FILE = Path(PROJECT_DIR) / '.claude/logs/verify-after-edit.log'
STATE_DIR = Path(PROJECT_DIR) / '.claude/state'

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# 1. DB 테이블 스키마 (필요 시 생성)
def init_db():
    """DB 테이블 보장"""
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS verify_after_edit_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                edit_count INTEGER DEFAULT 1,
                last_user_requery_ts TIMESTAMP,
                requery_pattern TEXT,
                reason TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"[ERROR] DB init failed: {e}")

def log(msg: str):
    """로그 기록"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def normalize_path(file_path: str) -> str:
    """기록용 경로 정규화 — 구분자 / · 대소문자(Windows) 통일 (같은 파일이 표기만 달라 따로 세지지 않게)."""
    fp = os.path.normpath(str(file_path or "")).replace("\\", "/")
    return fp.lower() if os.name == "nt" else fp


def record_edit(file_path: str, db_path=None, timeout: float = 0.25, budget: float = 0.5) -> str:
    """성공한 Edit/Write 1건을 시간 제한 안에서 기록 (R375 5차 검토 · 훅 응답 경로용 단일 정본).
    - 연결 대기 timeout(기본 0.25초) · 전체 budget(0.5초) 초과·잠금·디스크 오류 = 기록 생략 + 사유 반환 (작업을 막지 않음)
    - 연결은 finally 에서 항상 닫는다
    - 시각은 UTC 'YYYY-MM-DD HH:MM:SS' 한 형식으로 쓰고 비교 (SQLite CURRENT_TIMESTAMP 와 같은 형식 · 예전: 로컬 ISO 와 비교)
    - 반복 수정 횟수만 센다 — 사용자 재질의는 이 정보로 판정하지 않는다 (requery_pattern 은 비워 둔다 · 예전: 무조건 suspected_requery)
    반환: 'ok' | 'skip:<사유>'"""
    import time as _t
    t0 = _t.monotonic()
    fp = normalize_path(file_path)
    if not fp or fp == ".":
        return "skip:경로 없음"
    dbp = Path(db_path) if db_path else DB_PATH
    if not dbp.exists():
        return "skip:DB 없음"
    conn = None
    try:
        conn = sqlite3.connect(str(dbp), timeout=timeout)
        conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        conn.execute("""CREATE TABLE IF NOT EXISTS verify_after_edit_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL, edit_count INTEGER DEFAULT 1, last_user_requery_ts TIMESTAMP,
            requery_pattern TEXT, reason TEXT)""")
        if _t.monotonic() - t0 > budget:
            return "skip:시간 예산 초과"
        now = datetime.now(timezone.utc)
        since = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        (count,) = conn.execute("SELECT COUNT(*) FROM verify_after_edit_patterns WHERE file_path = ? AND ts > ?",
                                (fp, since)).fetchone()
        conn.execute("INSERT INTO verify_after_edit_patterns (ts, file_path, edit_count, reason) VALUES (?, ?, ?, ?)",
                     (now.strftime("%Y-%m-%d %H:%M:%S"), fp, int(count) + 1,
                      "repeat_edit_1h" if count else "first_edit_1h"))
        conn.commit()
        return "ok"
    except Exception as e:  # noqa: BLE001 — 잠금·디스크 오류 = 생략 (진단만)
        return f"skip:{type(e).__name__}"
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass


# 2. Edit/Write 기록 (CLI · 훅 공통 = record_edit)
def on_edit_tool(file_path: str):
    """CLI 호환 — record_edit 사용 (R375: 무조건 재질의 판정·로컬/UTC 시각 혼용 제거)."""
    r = record_edit(file_path, timeout=2.0, budget=5.0)
    log(f"[EDIT] {normalize_path(file_path)} — {r}")
    return r

# 3. 주간 리포트 생성
def generate_weekly_report():
    """verify-after-edit 패턴 주간 요약"""
    if not DB_PATH.exists():
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        week_ago = datetime.now() - timedelta(days=7)
        c.execute("""
            SELECT file_path, COUNT(*), MAX(ts), requery_pattern
            FROM verify_after_edit_patterns
            WHERE ts > ? AND requery_pattern = 'suspected_requery'
            GROUP BY file_path
            ORDER BY COUNT(*) DESC
        """, (week_ago.isoformat(),))

        rows = c.fetchall()
        if rows:
            log(f"[WEEKLY] verify-after-edit patterns (last 7 days):")
            for path, cnt, ts, pattern in rows:
                log(f"  {path}: {cnt} requery(ies)")

        conn.close()
    except Exception as e:
        log(f"[ERROR] weekly_report: {e}")

if __name__ == '__main__':
    import sys

    # CLI: verify-after-edit-logger.py <file_path> [--report]
    if '--report' in sys.argv:
        generate_weekly_report()
    elif len(sys.argv) > 1:
        on_edit_tool(sys.argv[1])
    else:
        log("[INFO] Usage: verify-after-edit-logger.py <file_path> [--report]")
