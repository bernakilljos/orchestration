#!/usr/bin/env bash
# HOOK-09 — OCR Overflow Verify
#
# PostToolUse hook — Bash 명령에 'generate-*-ppt.py' 패턴이 포함되면 자동 검증.
# stdin 으로 hook input JSON 받음 (tool_input.command).

set -e

# stdin 의 JSON 에서 command 추출
INPUT="$(cat)"

# jq 가 있으면 정확 추출, 없으면 grep fallback
if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$INPUT" | jq -r '.tool_input.command // ""')"
else
  CMD="$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
fi

# generate-*-ppt.py 패턴 매칭 (자동화·team·plugins·final 모두)
if ! echo "$CMD" | grep -qE 'generate-([a-z]+-)?ppt\.py'; then
  exit 0
fi

# 프로젝트 루트 (.claude/hooks/ 의 부모의 부모)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERIFY_SCRIPT="$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py"

if [ ! -f "$VERIFY_SCRIPT" ]; then
  echo '{"systemMessage": "[hook-09] verify-ppt-overflow.py not found — skipping OCR verify"}' >&2
  exit 0
fi

# 검증 실행
RESULT="$(python "$VERIFY_SCRIPT" 2>&1 || true)"
EXIT_CODE=$?

# suspects 발견 시 Claude 에게 알림 (systemMessage)
if echo "$RESULT" | grep -q '\[!\]'; then
  SUSPECTS="$(echo "$RESULT" | grep -E '^\s*-\s+slide-' | sed 's/^\s*//' | head -10)"
  cat <<EOF
{
  "systemMessage": "[hook-09 OCR Verify] PPT 렌더 후 잘림 의심 슬라이드 발견 — Read tool 로 직접 OCR 검증 권장:\n${SUSPECTS}\n\noverflow-report.md 참조"
}
EOF
fi

exit 0
