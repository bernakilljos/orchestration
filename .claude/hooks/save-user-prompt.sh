#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트를 orca.db.conversations 자동 저장
# 근거: 사용자 지적 (2026-09-02) — 세션 끊기면 히스토리 유실 -> DB 로 관리
# 2026-10-12 ICM 개선 역병합 — python 2회 기동(추출·저장) → 1회 (ICM 실측 3.57초 · 10초 timeout 원인 중 하나)
#   프로젝트 venv 가 있으면 그걸 쓰고, 없으면 PATH 의 python (특정 폴더명 하드코딩 X)
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/conversation-save.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

PY=""
for c in "$PROJECT_ROOT"/.venv/Scripts/python.exe "$PROJECT_ROOT"/*/.venv/Scripts/python.exe "$PROJECT_ROOT"/.venv/bin/python; do
  [ -x "$c" ] && { PY="$c"; break; }
done
[ -n "$PY" ] || PY="$(command -v python || command -v python3 || true)"   # python3 는 Windows 스토어 별칭(가짜)일 수 있어 python 우선
[ -n "$PY" ] || exit 0

export PROJECT_ROOT
"$PY" -X utf8 -c "
import json, sys, os
sys.path.insert(0, os.path.join(os.environ['PROJECT_ROOT'], '.claude', 'scripts', 'lib'))
try:
    d = json.loads(sys.stdin.read() or '{}')
except Exception as e:
    sys.stderr.write('[parse error] %s\n' % e); raise SystemExit(0)
# 2026-09-19: 세션 id 는 훅 stdin 의 session_id 가 정본 (최근 mtime jsonl 추정은 동시 세션에서 남의 세션에 붙었다)
if d.get('session_id'):
    os.environ['CLAUDE_CODE_SESSION_ID'] = d['session_id']
p = d.get('user_prompt') or d.get('prompt') or ''
if not p:
    raise SystemExit(0)
try:
    import conversation_logger as CL
    CL.save_turn('user', p)
except Exception as e:
    sys.stderr.write('[save error] %s\n' % e)
" >>"$LOG" 2>&1 || true

exit 0
