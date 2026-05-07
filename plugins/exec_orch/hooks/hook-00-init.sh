#!/bin/bash
# HOOK-00 — Init: 프로젝트 첫 셋업
# .claude/scripts/init.bat 가 있으면 호출, 없으면 기본 폴더만 생성
set -e

PROJECT="${1:-$(pwd)}"
INIT_BAT="$PROJECT/.claude/scripts/init.bat"

# 기본 폴더 (idempotent)
mkdir -p "$PROJECT/docs/adr" \
         "$PROJECT/docs/deploy-history" \
         "$PROJECT/docs/screens" \
         "$PROJECT/.claude/context-cache" \
         "$PROJECT/.claude/tasks" \
         "$PROJECT/.claude/learning"

if [ -f "$INIT_BAT" ]; then
  if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe //c "$INIT_BAT" "$PROJECT" 2>&1 || echo "[HOOK-00] init.bat 실행 실패 (계속 진행)"
  else
    echo "[HOOK-00] cmd.exe 없음 - init.bat 건너뜀"
  fi
else
  echo "[HOOK-00] init.bat 없음 - 기본 폴더만 생성"
fi

# Stack 자동 감지 (정보 출력만)
if [ -f "$PROJECT/package.json" ]; then
  if grep -q '"vue".*"\^3' "$PROJECT/package.json" 2>/dev/null; then
    echo "[HOOK-00] Detected: Vue 3"
  elif grep -q '"vue".*"\^2' "$PROJECT/package.json" 2>/dev/null; then
    echo "[HOOK-00] Detected: Vue 2"
  fi
fi
[ -f "$PROJECT/pom.xml" ] && echo "[HOOK-00] Detected: Spring Boot"

exit 0
