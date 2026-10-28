#!/usr/bin/env bash
# PostToolUse Edit/Write hook → anti-ping-pong.py record
# 2026-10-27: anti-ping-pong detector 를 실제 수정 흐름에 연결 (CONNECTED X → ✓)
# 입력: TOOL_INPUT (JSON) via stdin — file_path 추출
# 결과: ping_pong_tracker DB record · 3회+ warn (log only · block X · 안전)

set -euo pipefail

# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
SCRIPT="$ROOT/.claude/scripts/anti-ping-pong.py"
[ -f "$SCRIPT" ] || exit 0

# python 동적 검색
PY="$(command -v python 2>/dev/null || command -v py 2>/dev/null || echo python)"

# stdin 에서 tool_input JSON 받기
PAYLOAD="$(cat 2>/dev/null || true)"
# file_path 추출 (jq 없을 수 있어 python 로)
FILE_PATH="$("$PY" -c "
import json, sys
try:
    data = json.loads(sys.stdin.read() or '{}')
    inp = data.get('tool_input', {})
    # Edit/Write/MultiEdit 모두 file_path 사용
    fp = inp.get('file_path') or inp.get('path') or ''
    print(fp)
except Exception:
    print('')
" <<<"$PAYLOAD" 2>/dev/null || echo "")"

[ -n "$FILE_PATH" ] || exit 0

# diff summary (new_string / content 앞 200자 · hash 재료)
DIFF_SUMMARY="$("$PY" -c "
import json, sys
try:
    data = json.loads(sys.stdin.read() or '{}')
    inp = data.get('tool_input', {})
    d = inp.get('new_string') or inp.get('content') or ''
    print(d[:200])
except Exception:
    print('')
" <<<"$PAYLOAD" 2>/dev/null || echo "")"

# record (exit 0/1/2 모두 통과 · PostToolUse 는 block 하지 X)
"$PY" -X utf8 "$SCRIPT" record \
    --file "$FILE_PATH" \
    --diff "${DIFF_SUMMARY:0:200}" \
    --session "${CLAUDE_SESSION_ID:-unknown}" 2>>"$ROOT/.claude/logs/anti-ping-pong.log" || true

exit 0
