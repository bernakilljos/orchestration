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
  *.vue)
    CHECKER="vue"
    ;;
  *)
    exit 0
    ;;
esac

# 2026-11-13 (R249): .vue 는 어떤 훅도 검사하지 않았다 (IFRS 에서 Claude 편집 1위 확장자 109건).
#   새 도구를 설치하지 않고 그 프로젝트에 이미 있는 Vue 컴파일러를 쓴다 — 프로젝트 Vue 와 짝인 'vue/compiler-sfc'
#   (Vue 2.7·3 모두 제공) 우선 · 없으면 '@vue/compiler-sfc' · 둘 다 없거나 node 없으면 검사 생략 (통과로 기록 안 함).
#   검사 본문 = 같은 폴더 vue-sfc-check.js (여러 줄 node -e 는 Windows node 에 첫 줄만 전달돼 별도 파일).
if [ "$CHECKER" = "vue" ]; then
  command -v node >/dev/null 2>&1 || exit 0
  ERR="$(node "$(dirname "$0")/vue-sfc-check.js" "$FILE_PATH" 2>&1)"
  EC=$?
fi

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
  # tsc 가 있으면 syntax-only 검사 — 전역 tsc 가 없으면 프로젝트의 node_modules/.bin/tsc (2026-11-13 R249)
  TSC="$(command -v tsc 2>/dev/null)"
  [ -z "$TSC" ] && [ -x "${CLAUDE_PROJECT_DIR:-$PWD}/node_modules/.bin/tsc" ] && TSC="${CLAUDE_PROJECT_DIR:-$PWD}/node_modules/.bin/tsc"
  if [ -n "$TSC" ]; then
    ERR="$("$TSC" --noEmit --target esnext --jsx preserve --skipLibCheck "$FILE_PATH" 2>&1)"
    EC=$?   # 2026-11-13: 예전엔 '| head -5' 뒤의 $? = head 의 종료 코드(늘 0) → TS 오류가 한 번도 보고되지 않았다
    ERR="$(printf '%s\n' "$ERR" | head -20)"
  else
    exit 0  # tsc 없음 — skip
  fi
fi

if [ $EC -ne 0 ] && [ -n "$ERR" ]; then
  BASE="$(basename "$FILE_PATH")"
  # decision: block + reason → Claude 에게 되돌려 재수정 (공식 hooks 문서 PostToolUse decision control)
  # 2026-11-13 (R249): 오류 원문(줄바꿈·따옴표·C:\ 역슬래시)을 heredoc 으로 끼워 JSON 이 깨졌다 → 파싱 실패 =
  #   Claude 에게 전달 안 됨 (문서: "JSON that can't be parsed … Non-blocking error"). 인코더로 만든다.
  MSG="[js-syntax] $BASE syntax error:
$ERR

이 파일을 고친 뒤 같은 검사를 다시 통과시키고 나서 완료로 보고한다."
  PY="$(cat "${CLAUDE_PROJECT_DIR:-$PWD}/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n')"
  MSG="$MSG" "${PY:-python}" -X utf8 -c 'import json,os,sys; sys.stdout.write(json.dumps({"decision": "block", "reason": os.environ["MSG"]}, ensure_ascii=False) + "\n")' 2>/dev/null \
    || { echo "$MSG" >&2; exit 2; }   # 파이썬이 없으면 exit 2 + stderr (문서: PostToolUse exit 2 = stderr 를 Claude 에게)
fi
exit 0
