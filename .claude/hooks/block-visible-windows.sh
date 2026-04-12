#!/bin/bash
# Hook: PreToolUse — Bash 명령어에서 start 명령어 사용 차단
# 사용자 화면에 CMD 창이 뜨는 것을 방지

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | sed 's/"command":"//;s/"$//')

# start 명령어로 보이는 창 띄우는 패턴 감지
if echo "$COMMAND" | grep -qiE '^\s*start\s+"[^"]*"\s+cmd'; then
  echo "BLOCKED: 'start' 명령어로 보이는 CMD 창을 띄우려 합니다. run_in_background를 사용하세요." >&2
  exit 1
fi

exit 0
