#!/usr/bin/env bash
# Stop / SessionEnd hook — 세션 요약 + assistant 응답 sync
# 근거: 히스토리 DB 관리 정책 (2026-09-02) · 사용자 지적 (2026-09-03) assistant 응답 유실
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/conversation-save.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

PY=$(cat "$PROJECT_ROOT/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n') || PY=python
PY="${PY:-python}"

# 1. jsonl 에서 assistant 응답 sync (Claude Code 는 assistant hook 없음)
# 0. stdin(JSON) 의 session_id · transcript_path 가 정본 (2026-09-19 · mtime 추정으로 남의 세션에 저장되던 것)
INPUT="$(cat 2>/dev/null || true)"
eval "$(printf '%s' "$INPUT" | "$PY" -X utf8 -c "import json,sys,shlex
try:
    d=json.load(sys.stdin)
    if d.get('session_id'): print('export CLAUDE_CODE_SESSION_ID='+shlex.quote(d['session_id']))
    if d.get('transcript_path'): print('export CLAUDE_TRANSCRIPT_PATH='+shlex.quote(d['transcript_path']))
    print('export HOOK_EVENT='+shlex.quote(str(d.get('hook_event_name',''))+('/'+str(d['reason']) if d.get('reason') else '')))
except Exception: pass" 2>/dev/null)"

"$PY" -X utf8 "$PROJECT_ROOT/.claude/scripts/sync-assistant-from-jsonl.py" >>"$LOG" 2>&1 || true

# 2. session_summary 저장
"$PY" -X utf8 -c "
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
    dec_rows = c.execute('SELECT ai_classified FROM decisions WHERE ts >= datetime(\"now\",\"-1 hour\") LIMIT 5').fetchall()
    key_dec = '; '.join(r[0] for r in dec_rows if r[0])[:1000]
    if save_session_summary(summary, key_dec, ''):
        print(f'[ok] session {sid[:8]} summary saved - {len(rows)} turns')
    else:
        # transcript 없는 0건 세션(헤드리스 회차의 보조 프로세스) — 저장 안 함 · 어떤 이벤트였는지만 남긴다
        print(f'[skip] session {sid[:8]} 0 turns · transcript 없음 · event={os.environ.get(\"HOOK_EVENT\",\"?\")}')
except Exception as e:
    print(f'[skip] {e}', file=sys.stderr)
" >>"$LOG" 2>&1 || true

# 3. solution 자동 캡처
"$PY" -X utf8 "$PROJECT_ROOT/.claude/scripts/save_solution.py" auto >>"$LOG" 2>&1 || true

exit 0
