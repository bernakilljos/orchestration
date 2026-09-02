#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트 시 DB 이력 자동 조회 · systemMessage 주입
# 근거: 2026-09-02 사용자 지적 — "지시할 때 DB 에 이력 확인하고 하나"
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/lookup-history.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# stdin = hook JSON payload · prompt 추출
PROMPT="$(python -X utf8 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    p = d.get('user_prompt') or d.get('prompt') or ''
    print(p[:500], end='')
except Exception as e:
    sys.stderr.write(f'[parse] {e}\n')
" 2>>"$LOG")"

if [ -z "${PROMPT:-}" ]; then
  exit 0
fi

# 최근 20 turns 중 유사 프롬프트 검색 (키워드 3+ 매치)
python -X utf8 -c "
import os, re, sqlite3, sys
prompt = '''$PROMPT'''
kws = [w for w in re.findall(r'\w{3,}', prompt) if not w.isdigit()][:8]
if not kws:
    sys.exit(0)
db = os.path.join(os.environ.get('CLAUDE_PROJECT_DIR', '.'), '.claude', 'state', 'orca.db')
if not os.path.exists(db):
    sys.exit(0)
try:
    c = sqlite3.connect(db)
    like = ' OR '.join(['content LIKE ?'] * len(kws))
    params = [f'%{k}%' for k in kws]
    rows = c.execute(
        f'SELECT session_id, turn, role, substr(content,1,200) FROM conversations WHERE ({like}) AND session_id != ? ORDER BY id DESC LIMIT 3',
        (*params, os.environ.get('CLAUDE_CODE_SESSION_ID',''))
    ).fetchall()
    if rows:
        print('## 관련 이전 대화 (자동 조회 · DB)')
        for sid, turn, role, content in rows:
            print(f'- [{sid[:8]}#{turn} {role}] {content}')
    # 세션 요약 최근 관련
    sum_rows = c.execute(
        f'SELECT session_id, substr(summary,1,150) FROM session_summary WHERE summary LIKE ? OR key_decisions LIKE ? ORDER BY ended_at DESC LIMIT 2',
        (f'%{kws[0]}%', f'%{kws[0]}%')
    ).fetchall()
    if sum_rows:
        print()
        print('## 관련 세션 요약')
        for sid, summ in sum_rows:
            print(f'- [{sid[:8]}] {summ}')
except Exception as e:
    sys.stderr.write(f'[lookup] {e}\n')
" 2>>"$LOG"

exit 0
