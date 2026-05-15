#!/usr/bin/env bash
# PreToolUse hook — best-practices §하드 경로 금지 자동 강제
# Edit|Write 시 content/new_string 에 하드 경로 패턴 매치 → systemMessage
# 차단 안 함 (informational + 권장 fix)
# CLAUDE.md §7-4 위반 사전 차단
set +e

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')"
  CONTENT="$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
  CONTENT=""
fi

# 검사 대상: code/script/config 파일만 (md 문서·rule 예시는 제외)
case "$FILE_PATH" in
  *.py|*.sh|*.bat|*.ps1|*.js|*.ts|*.json|*.toml|*.yaml|*.yml|*.ini|*.cfg|*.conf) ;;
  *) exit 0 ;;
esac

# rule 파일·문서·예시 제외 (placeholder 허용)
case "$FILE_PATH" in
  *.claude/rules/*|*docs/*|*examples/*|*.example*|*setup/templates/*) exit 0 ;;
esac

[ -n "$CONTENT" ] && [ "$CONTENT" != "null" ] || exit 0

VIOLATIONS=""

# 백슬래시 처리: JSON escape 된 \\ 또는 raw \ 둘 다 매치 ([\\]+ = 백슬래시 1+)
# 1. C:\Users\<사용자명> 또는 C:/Users/<사용자명>
if echo "$CONTENT" | grep -qE 'C:[\\/]+[Uu]sers[\\/]+[a-z][a-z0-9_]+'; then
  MATCH="$(echo "$CONTENT" | grep -oE 'C:[\\/]+[Uu]sers[\\/]+[a-z][a-z0-9_]+' | head -1)"
  VIOLATIONS="$VIOLATIONS\n  - 사용자명: $MATCH → %USERPROFILE% / Path.home()"
fi

# 2. /home/<사용자명>
if echo "$CONTENT" | grep -qE '/home/[a-z][a-z0-9_]+'; then
  MATCH="$(echo "$CONTENT" | grep -oE '/home/[a-z][a-z0-9_]+' | head -1)"
  VIOLATIONS="$VIOLATIONS\n  - Linux 사용자: $MATCH → \$HOME / Path.home()"
fi

# 3. Python3<버전> — Python310 ~ Python399 매치 (현재 + 미래 버전)
if echo "$CONTENT" | grep -qE 'Python3[0-9]{2}'; then
  MATCH="$(echo "$CONTENT" | grep -oE 'Python3[0-9]{2}' | head -1)"
  VIOLATIONS="$VIOLATIONS\n  - Python 버전: $MATCH → where python / shutil.which('python')"
fi

# 4. DESKTOP-XXX 호스트명
if echo "$CONTENT" | grep -qE 'DESKTOP-[A-Z0-9]{5,}'; then
  MATCH="$(echo "$CONTENT" | grep -oE 'DESKTOP-[A-Z0-9]{5,}' | head -1)"
  VIOLATIONS="$VIOLATIONS\n  - 호스트명: $MATCH → %COMPUTERNAME% / socket.gethostname()"
fi

if [ -n "$VIOLATIONS" ]; then
  BASE="$(basename "$FILE_PATH")"
  cat <<EOF
{"systemMessage": "[hardcoded-path] $BASE — best-practices §하드 경로 금지 위반 후보:$VIOLATIONS\n동적 검색으로 교체 권장."}
EOF
fi
exit 0
