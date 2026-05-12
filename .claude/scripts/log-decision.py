"""Observability — UserPromptSubmit 마다 decision 자동 기록 + 패턴 알람.

orca.db `decisions` table:
- id, ts, user_msg (truncated), ai_classified, memory_hits, status
- 같은 키워드 N회 발생 → 자동 알람 → systemMessage 주입

5 핵심 부품 #5 Observability — decision trace + 사용자 패턴 인지.
"""
import sys
import os
import re
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "orca.db"


def ensure_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_msg TEXT,
        ai_classified TEXT,
        memory_hits INTEGER DEFAULT 0,
        keywords TEXT,
        status TEXT DEFAULT 'logged'
    );
    CREATE INDEX IF NOT EXISTS idx_decisions_ts ON decisions(ts);
    CREATE INDEX IF NOT EXISTS idx_decisions_keywords ON decisions(keywords);
    """)


# 사고 패턴 키워드 (재발 검출 대상)
PATTERN_KEYWORDS = [
    "짤려", "짤린", "짤림", "잘림",
    "여백", "넘쳐", "안보",
    "여전", "또", "발동", "농땡이",
    "글씨", "이미지", "fit",
]


def extract_pattern_keywords(message: str) -> list:
    """사용자 메시지에서 사고 패턴 키워드 추출."""
    hits = []
    for kw in PATTERN_KEYWORDS:
        if kw in message:
            hits.append(kw)
    return hits


def log(user_msg: str, ai_classified: str = "claude", memory_hits: int = 0):
    """decision 기록 + 패턴 검출."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    ensure_table(conn)

    keywords = extract_pattern_keywords(user_msg)
    keywords_str = ",".join(keywords)

    conn.execute(
        "INSERT INTO decisions (user_msg, ai_classified, memory_hits, keywords) VALUES (?, ?, ?, ?)",
        (user_msg[:500], ai_classified, memory_hits, keywords_str),
    )
    conn.commit()

    # 패턴 검출 — 최근 1시간 같은 키워드 3회+
    alarms = []
    # SQL CURRENT_TIMESTAMP 는 UTC — cutoff 도 UTC 로 맞춤
    cutoff = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    for kw in keywords:
        cur = conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE keywords LIKE ? AND ts >= ?",
            (f"%{kw}%", cutoff),
        )
        count = cur.fetchone()[0]
        if count >= 3:
            alarms.append({"keyword": kw, "count": count, "window": "1h"})

    conn.close()
    return {"logged": True, "keywords": keywords, "alarms": alarms}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            msg = sys.stdin.read().strip()
        else:
            print("usage: log-decision.py '<사용자 메시지>' [--ai codex] [--mem-hits N]")
            sys.exit(2)
    else:
        msg = sys.argv[1]

    ai = "claude"
    mem = 0
    for i, a in enumerate(sys.argv):
        if a == "--ai" and i + 1 < len(sys.argv):
            ai = sys.argv[i + 1]
        if a == "--mem-hits" and i + 1 < len(sys.argv):
            mem = int(sys.argv[i + 1])

    result = log(msg, ai, mem)
    print(json.dumps(result, ensure_ascii=False, indent=2))
