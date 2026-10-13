#!/usr/bin/env python3
# verify-after-edit-logger.py — PostToolUse Edit/Write 시 "왜 안 됐어" 재지시 패턴 감지
# 2026-10-13 신설 · 목표 C · Auto regression tracking

import os
import json
import sqlite3
from datetime import datetime, timedelta
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

def detect_requery_pattern(ts_edit: datetime) -> bool:
    """
    지난 1시간 내 같은 파일 Edit 2회 이상 + 사이에 "왜 안 됐어" 패턴 키워드 감지
    (개선: UserPromptSubmit hook 에서 keyword 저장 필요 · 현재는 heuristic)
    """
    # 실제 구현: session_summary 또는 conversations 테이블에서
    # ts_edit 전후 대화에 "왜"·"안 됐"·"적용"·"효과" 등 키워드 확인
    # 임시: True 반환 (보수적으로)
    return True

# 2. PostToolUse Edit/Write 감지
def on_edit_tool(file_path: str):
    """Edit/Write 도구 실행 감지"""
    init_db()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 지난 1시간 내 같은 파일 Edit 이력 조회
        hour_ago = datetime.now() - timedelta(hours=1)
        c.execute("""
            SELECT COUNT(*), MAX(ts) FROM verify_after_edit_patterns
            WHERE file_path = ? AND ts > ?
        """, (file_path, hour_ago.isoformat()))
        count, last_ts = c.fetchone()

        if count > 0 and last_ts:
            last_ts_obj = datetime.fromisoformat(last_ts)
            if detect_requery_pattern(last_ts_obj):
                c.execute("""
                    INSERT INTO verify_after_edit_patterns
                    (file_path, edit_count, last_user_requery_ts, requery_pattern, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (file_path, count + 1, datetime.now().isoformat(), 'suspected_requery',
                      'Multiple edits within 1h + likely user requery'))
                log(f"[PATTERN] {file_path} — edit #{count+1} (possible requery)")
        else:
            c.execute("""
                INSERT INTO verify_after_edit_patterns
                (file_path, edit_count)
                VALUES (?, 1)
            """, (file_path,))
            log(f"[EDIT] {file_path} — first edit in window")

        conn.commit()
        conn.close()
    except Exception as e:
        log(f"[ERROR] on_edit_tool({file_path}): {e}")

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
