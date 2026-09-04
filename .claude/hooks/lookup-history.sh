#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트 시 DB 이력 자동 조회 - systemMessage 주입
# 근거: 2026-09-02 사용자 지적 — "지시할 때 DB 에 이력 확인하고 하나"
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/lookup-history.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# stdin = hook JSON payload - prompt 추출
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
        print('## 관련 이전 대화 (자동 조회 - DB)')
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
    # problem_solutions 재사용 카탈로그 (2026-09-02 - 양방향)
    like2 = ' OR '.join(['keywords LIKE ? OR problem LIKE ?'] * min(len(kws), 4))
    params2 = []
    for k in kws[:4]:
        params2.extend([f'%{k}%', f'%{k}%'])
    try:
        # hit_count · last_hit_ts 컬럼 보장
        cols = [r[1] for r in c.execute('PRAGMA table_info(problem_solutions)').fetchall()]
        if 'hit_count' not in cols:
            c.execute('ALTER TABLE problem_solutions ADD COLUMN hit_count INTEGER DEFAULT 0')
        if 'last_hit_ts' not in cols:
            c.execute('ALTER TABLE problem_solutions ADD COLUMN last_hit_ts TIMESTAMP')
        sol_rows = c.execute(
            f'SELECT id, category, substr(problem,1,120), substr(solution,1,200), files_modified, reusable_score FROM problem_solutions WHERE ({like2}) ORDER BY reusable_score DESC, ts DESC LIMIT 3',
            params2
        ).fetchall()
        if sol_rows:
            print()
            print('## 재사용 가능한 해결책 (자동 조회)')
            hit_ids = []
            for sid_s, cat, prob, sol, files, score in sol_rows:
                print(f'- [{cat} - ★{score}] 문제: {prob}')
                if sol: print(f'  해결: {sol}')
                if files: print(f'  파일: {files[:150]}')
                hit_ids.append(sid_s)
            # hit_count 증가 · verified 승급 · score 상향
            for hid in hit_ids:
                c.execute(
                    'UPDATE problem_solutions SET hit_count=COALESCE(hit_count,0)+1, '
                    'last_hit_ts=CURRENT_TIMESTAMP, '
                    'reusable_score=CASE '
                    'WHEN COALESCE(hit_count,0)+1 >= 10 THEN 10 '
                    'WHEN COALESCE(hit_count,0)+1 >= 5 THEN MAX(reusable_score, 9) '
                    'WHEN COALESCE(hit_count,0)+1 >= 3 THEN MAX(reusable_score, 8) '
                    'ELSE MAX(reusable_score, 6) END, '
                    'verified=CASE WHEN COALESCE(hit_count,0)+1 >= 3 THEN 1 ELSE verified END '
                    'WHERE id=?', (hid,)
                )
            c.commit()
    except Exception:
        pass
except Exception as e:
    sys.stderr.write(f'[lookup] {e}\n')
" 2>>"$LOG"

exit 0
