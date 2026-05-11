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

# 산출물 빌드 패턴 매칭 (확장: build-*-doc / build-*-diagrams / generate-*-ppt / render-* / pdf)
if ! echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(ppt|doc|diagrams|pdf|html)\.py|build-[a-z-]+-doc\.py'; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# PPT 검증
VERIFY_PPT="$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py"
# 일반 이미지 fit 검증 (PNG 비율 vs 페이지 비율)
VERIFY_FIT="$PROJECT_ROOT/.claude/scripts/verify-image-fit.py"

if [ -f "$VERIFY_FIT" ] && echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(diagrams|doc|html)\.py'; then
  FIT_RESULT="$(python "$VERIFY_FIT" 2>&1 || true)"
  if echo "$FIT_RESULT" | grep -q 'FAIL'; then
    cat <<EOF
{"systemMessage": "[hook-09 fit] 이미지 fit 검증 실패:\n$FIT_RESULT"}
EOF
  fi
fi

if [ ! -f "$VERIFY_PPT" ]; then
  exit 0
fi
VERIFY_SCRIPT="$VERIFY_PPT"

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
