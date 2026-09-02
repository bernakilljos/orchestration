#!/usr/bin/env bash
# PostToolUse Write/Edit hook — 파일 생성/변경 시 audit + 명명 검증
# 근거: 운영 grade 파일 관리 rule (2026-09-02)
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/file-audit.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# stdin = hook payload · tool_input.file_path 추출
FILE="$(python -X utf8 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    p = (d.get('tool_input') or {}).get('file_path') or (d.get('tool_input') or {}).get('path') or ''
    print(p, end='')
except Exception as e:
    sys.stderr.write(f'[parse] {e}\n')
" 2>>"$LOG")"

if [ -n "${FILE:-}" ]; then
  python -X utf8 "$PROJECT_ROOT/.claude/scripts/audit_file_write.py" write "$FILE" "PostToolUse" >>"$LOG" 2>&1 || true
fi

exit 0
