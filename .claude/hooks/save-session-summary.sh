#!/usr/bin/env bash
# Stop / SessionEnd hook — 세션 요약을 orca.db.session_summary 저장
# 근거: 히스토리 DB 관리 정책 (2026-09-02)
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/conversation-save.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# 세션 최근 활동 요약 (conversations 최근 20 turns 기반 · 간단 요약)
python -X utf8 -c "
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'scripts', 'lib'))
from conversation_logger import get_session_id, save_session_summary
import sqlite3
db = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'state', 'orca.db')
try:
    c = sqlite3.connect(db)
    sid = get_session_id()
    rows = c.execute('SELECT role, substr(content,1,200) FROM conversations WHERE session_id=? ORDER BY turn DESC LIMIT 20', (sid,)).fetchall()
    if rows:
        summary = ' | '.join(f'{r}:{t}' for r,t in reversed(rows))[:2000]
    else:
        summary = ''
    # 최근 결정 (decisions 테이블) 조회
    dec_rows = c.execute('SELECT ai_classified FROM decisions WHERE ts >= datetime(\"now\",\"-1 hour\") LIMIT 5').fetchall()
    key_dec = '; '.join(r[0] for r in dec_rows if r[0])[:1000]
    save_session_summary(summary, key_dec, '')
    print(f'[ok] session {sid[:8]} summary saved · {len(rows)} turns')
except Exception as e:
    print(f'[skip] {e}', file=sys.stderr)
" >>"$LOG" 2>&1 || true

# solution 자동 캡처 (2026-09-02 · 양방향 초최고)
python -X utf8 "$PROJECT_ROOT/.claude/scripts/save_solution.py" auto >>"$LOG" 2>&1 || true

exit 0
