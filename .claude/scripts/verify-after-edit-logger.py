#!/usr/bin/env python3
# verify-after-edit-logger.py ??PostToolUse Edit/Write ??"?????먯뼱" ?ъ????⑦꽩 媛먯?
# 2026-10-13 ?좎꽕 쨌 紐⑺몴 C 쨌 Auto regression tracking

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

# 1. DB ?뚯씠釉??ㅽ궎留?(?꾩슂 ???앹꽦)
def init_db():
    """DB ?뚯씠釉?蹂댁옣"""
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        log(f"[ERROR] DB init failed: {e}")

def log(msg: str):
    """濡쒓렇 湲곕줉"""
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def detect_requery_pattern(ts_edit: datetime) -> bool:
    """
    吏??1?쒓컙 ??媛숈? ?뚯씪 Edit 2???댁긽 + ?ъ씠??"?????먯뼱" ?⑦꽩 ?ㅼ썙??媛먯?
    (媛쒖꽑: UserPromptSubmit hook ?먯꽌 keyword ????꾩슂 쨌 ?꾩옱??heuristic)
    """
    # ?ㅼ젣 援ы쁽: session_summary ?먮뒗 conversations ?뚯씠釉붿뿉??    # ts_edit ?꾪썑 ??붿뿉 "??쨌"????쨌"?곸슜"쨌"?④낵" ???ㅼ썙???뺤씤
    # ?꾩떆: True 諛섑솚 (蹂댁닔?곸쑝濡?
    return True

# 2. PostToolUse Edit/Write 媛먯?
def on_edit_tool(file_path: str):
    """Edit/Write ?꾧뎄 ?ㅽ뻾 媛먯?"""
    init_db()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 吏??1?쒓컙 ??媛숈? ?뚯씪 Edit ?대젰 議고쉶
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
                log(f"[PATTERN] {file_path} ??edit #{count+1} (possible requery)")
        else:
            c.execute("""
                INSERT INTO verify_after_edit_patterns
                (file_path, edit_count)
                VALUES (?, 1)
            """, (file_path,))
            log(f"[EDIT] {file_path} ??first edit in window")

        conn.commit()
        conn.close()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        log(f"[ERROR] on_edit_tool({file_path}): {e}")

# 3. 二쇨컙 由ы룷???앹꽦
def generate_weekly_report():
    """verify-after-edit ?⑦꽩 二쇨컙 ?붿빟"""
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
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

