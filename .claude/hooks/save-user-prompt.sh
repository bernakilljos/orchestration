#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 프롬프트를 orca.db.conversations 자동 저장
# 근거: 사용자 지적 (2026-09-02) — 세션 끊기면 히스토리 유실 -> DB 로 관리
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/conversation-save.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# stdin = hook JSON payload - user_prompt 필드 추출
# 2026-09-19: 세션 id 를 "가장 최근 mtime 의 jsonl" 로 추정하다 창 4개 동시 세션에서 남의 세션(/loop 3dedce8f) 에
# 턴이 전부 붙었다. 훅 stdin 의 session_id 가 정본이다 (CLAUDE.md § 3.1.1).
INPUT="$(cat)"
export CLAUDE_CODE_SESSION_ID="$(printf '%s' "$INPUT" | python -X utf8 -c "import json,sys
try: print(json.load(sys.stdin).get('session_id') or '', end='')
except Exception: pass" 2>/dev/null)"
[ -n "$CLAUDE_CODE_SESSION_ID" ] || unset CLAUDE_CODE_SESSION_ID
PROMPT="$(printf '%s' "$INPUT" | python -X utf8 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    p = d.get('user_prompt') or d.get('prompt') or ''
    print(p, end='')
except Exception as e:
    sys.stderr.write(f'[parse error] {e}\n')
" 2>>"$LOG")"

if [ -n "${PROMPT:-}" ]; then
  printf '%s' "$PROMPT" | python -X utf8 "$PROJECT_ROOT/.claude/scripts/lib/conversation_logger.py" save-turn user >>"$LOG" 2>&1 || true
fi

exit 0
