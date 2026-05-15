#!/usr/bin/env bash
# PostToolUse Edit|Write hook — JS/TS/JSX syntax 자동 검증
# syntax error 시 decision:block + continueOnBlock 으로 Claude 자동 재수정
set +e

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+' | head -1 | sed 's/.*"\([^"]*\)$/\1/')"
fi

[ -f "$FILE_PATH" ] || exit 0

# 검사 대상 확장자
case "$FILE_PATH" in
  *.js|*.mjs|*.cjs|*.jsx)
    CHECKER="js"
    ;;
  *.ts|*.tsx)
    CHECKER="ts"
    ;;
  *)
    exit 0
    ;;
esac

# node --check (JS/JSX 기본 + JSX 는 esbuild 또는 babel 필요 — 일단 JS 만 우선)
if [ "$CHECKER" = "js" ]; then
  case "$FILE_PATH" in
    *.jsx)
      # JSX 는 node --check 불가 — esbuild 있으면 사용
      if command -v esbuild >/dev/null 2>&1; then
        ERR="$(esbuild "$FILE_PATH" --loader=jsx --target=esnext --bundle=false 2>&1 >/dev/null)"
      else
        exit 0  # JSX 검사 도구 없음 — skip
      fi
      ;;
    *)
      if ! command -v node >/dev/null 2>&1; then exit 0; fi
      ERR="$(node --check "$FILE_PATH" 2>&1)"
      ;;
  esac
  EC=$?
elif [ "$CHECKER" = "ts" ]; then
  # tsc 가 있으면 syntax-only 검사
  if command -v tsc >/dev/null 2>&1; then
    ERR="$(tsc --noEmit --target esnext --jsx preserve --skipLibCheck "$FILE_PATH" 2>&1 | head -5)"
    EC=$?
  else
    exit 0  # tsc 없음 — skip
  fi
fi

if [ $EC -ne 0 ] && [ -n "$ERR" ]; then
  BASE="$(basename "$FILE_PATH")"
  # decision: block + continueOnBlock 으로 Claude 자동 재수정 유도
  cat <<EOF
{"decision": "block", "reason": "[js-syntax] $BASE syntax error:\n$ERR\n\n즉시 fix 후 다시 저장 권장."}
EOF
fi
exit 0
