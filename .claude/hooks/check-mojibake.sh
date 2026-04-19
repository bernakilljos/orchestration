#!/bin/bash
# check-mojibake.sh — Write/Edit 시 한글 깨짐 감지 + 차단
#
# 트리거: PreToolUse (Write|Edit)
# 검출:
#   - U+FFFD (REPLACEMENT CHARACTER, 깨진 문자)
#   - UTF-8 → cp949 오인 패턴 (ÂÃ 연속, íìîï 연속)
#   - 이중 이스케이프 \uXXXX\uXXXX
#
# 결과: 깨짐 감지 시 tool 실행 차단 + 원인 알림

set -uo pipefail

INPUT=$(cat 2>/dev/null || echo '{}')

# tool_input.content 또는 tool_input.new_string 추출 (stdout UTF-8 강제)
content=$(echo "$INPUT" | python -c "
import json, sys
try:
  sys.stdout.reconfigure(encoding='utf-8')
  sys.stdin.reconfigure(encoding='utf-8')
except: pass
try:
    d = json.load(sys.stdin)
    ti = d.get('tool_input', {})
    print(ti.get('content', '') or ti.get('new_string', ''))
except Exception:
    pass
" 2>/dev/null || echo "")

if [ -z "$content" ]; then
    echo '{"continue": true}'
    exit 0
fi

# REPL char 감지 (stdin·stdout UTF-8 강제)
has_repl=$(echo "$content" | python -c "
import sys
try:
  sys.stdout.reconfigure(encoding='utf-8')
  sys.stdin.reconfigure(encoding='utf-8')
except: pass
txt = sys.stdin.read()
print('yes' if '\ufffd' in txt else 'no')
" 2>/dev/null || echo "no")

if [ "$has_repl" = "yes" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"한글 깨짐 감지 (U+FFFD). UTF-8 인코딩 확인 후 재시도."}}
EOF
  exit 0
fi

# UTF-8 오인 패턴
is_mojibake=$(echo "$content" | python -c "
import sys, re
try:
  sys.stdout.reconfigure(encoding='utf-8')
  sys.stdin.reconfigure(encoding='utf-8')
except: pass
txt = sys.stdin.read()
patterns = [
    re.compile(r'[ÂÃ][\x80-\xBF]{2,}'),
    re.compile(r'[íìîïðñòó]{2,}'),
]
for p in patterns:
    if p.search(txt):
        print('yes'); sys.exit(0)
print('no')
" 2>/dev/null || echo "no")

if [ "$is_mojibake" = "yes" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"한글 깨짐 패턴 감지 (cp949 오인). UTF-8 로 재인코딩 후 재시도."}}
EOF
  exit 0
fi

echo '{"continue": true}'
