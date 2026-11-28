#!/usr/bin/env python3
# verify-after-edit-logger.py — PostToolUse Edit/Write 시 "왜 안 됐어" 재지시 패턴 감지
# 2026-10-13 신설 · 목표 C · Auto regression tracking

import os
import sys
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
    """기록용 경로 정규화 (플랫폼별 계약) — Windows: \\ → / · 대소문자 통일 · POSIX: 역슬래시는 파일명 글자라 그대로 · 대소문자 유지."""
    fp = str(file_path or "")
    if os.name == "nt":
        return os.path.normpath(fp).replace("\\", "/").lower()
    return os.path.normpath(fp)


def record_edit(file_path: str, db_path=None, timeout: float = None, budget: float = None) -> str:
    """성공한 Edit/Write 1건을 시간 제한 안에서 기록 (R375 5·6차 검토 · 훅 응답 경로용 단일 정본).
    - state_db.bounded_insert: 전체 마감(budget · 기본 ORCA_HOOK_DB_TIMEOUT 검증값) 안에서 문장마다 남은 시간만 대기 · close 보장
    - 잠금·시간 초과·디스크 오류 = 스풀에 보관하고 다음 성공 때 이어 씀 (조용히 버리지 않음) · timeout 인자는 호환용(미사용)
    - 시각은 UTC 'YYYY-MM-DD HH:MM:SS' 한 형식으로 쓰고 비교 (SQLite CURRENT_TIMESTAMP 와 같은 형식 · 예전: 로컬 ISO 와 비교)
    - 반복 수정 횟수만 센다 — 사용자 재질의는 이 정보로 판정하지 않는다 (requery_pattern 은 비워 둔다 · 예전: 무조건 suspected_requery)
    반환: 'ok' | 'skip:<사유>'"""
    fp = normalize_path(file_path)
    if not fp or fp == ".":
        return "skip:경로 없음"
    dbp = Path(db_path) if db_path else DB_PATH
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    import state_db as _sdb
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    # R375 6차 검토: 횟수 세기와 기록을 한 문장으로 (동시 writer 의 count→insert 경합 제거) · 전체 마감 · 못 쓰면 스풀
    return _sdb.bounded_insert(dbp, "verify_after_edit_patterns", [(
        "INSERT INTO verify_after_edit_patterns (ts, file_path, edit_count, reason) "
        "SELECT ?, ?, COUNT(*) + 1, CASE WHEN COUNT(*) > 0 THEN 'repeat_edit_1h' ELSE 'first_edit_1h' END "
        "FROM verify_after_edit_patterns WHERE file_path = ? AND ts > ?",
        [now.strftime("%Y-%m-%d %H:%M:%S"), fp, fp, since])],
        budget=budget, setup=("""CREATE TABLE IF NOT EXISTS verify_after_edit_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL, edit_count INTEGER DEFAULT 1, last_user_requery_ts TIMESTAMP,
            requery_pattern TEXT, reason TEXT)""",))


# 2. Edit/Write 기록 (CLI · 훅 공통 = record_edit)
def on_edit_tool(file_path: str):
    """CLI 호환 — record_edit 사용 (R375: 무조건 재질의 판정·로컬/UTC 시각 혼용 제거)."""
    r = record_edit(file_path, budget=5.0)
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
