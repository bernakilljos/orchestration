#!/usr/bin/env bash
# pre-commit-full-check.sh — git commit 시 모든 갱신 의무 점검
# 기존 pre-commit-infra-check.sh 를 대체하는 종합 버전
# PreToolUse Bash (git commit 감지) 에서 실행
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

INPUT=$(cat 2>/dev/null || echo '{}')
CMD=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' 2>/dev/null || echo "")

# git commit 아니면 skip
echo "$CMD" | grep -qE 'git\s+commit' || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 0

STAGED=$(git diff --cached --name-only 2>/dev/null)
MISSING=""

# 1. plugins/hooks/scripts 변경 → guide.txt 필수
INFRA=$(echo "$STAGED" | grep -cE '^(plugins/|\.claude/hooks/|\.claude/scripts/|setup/)' || echo "0")
if [ "$INFRA" -gt 0 ]; then
  echo "$STAGED" | grep -q "^guide.txt" || MISSING="$MISSING\n  - guide.txt (§6·§12·§17)"
  echo "$STAGED" | grep -q "^CLAUDE.md" || MISSING="$MISSING\n  - CLAUDE.md (AUTO-STATS 라인)"
fi

# 2. 새 플러그인 → marketplace.json
NEW_PLUGIN=$(echo "$STAGED" | grep -oP '^plugins/[^/]+/plugin\.json$' | head -1)
if [ -n "$NEW_PLUGIN" ]; then
  echo "$STAGED" | grep -q "marketplace.json" || MISSING="$MISSING\n  - .claude-plugin/marketplace.json"
fi

# 3. 새 hook → settings.json
NEW_HOOK=$(echo "$STAGED" | grep -E '^(plugins|\.claude)/.*hooks/.*\.sh$' | head -1)
if [ -n "$NEW_HOOK" ]; then
  echo "$STAGED" | grep -q "settings.json" || MISSING="$MISSING\n  - .claude/settings.json (hook 등록)"
fi

# 4. setup 모듈 변경 → BUILD.md
SETUP_MOD=$(echo "$STAGED" | grep -cE '^setup/modules/' || echo "0")
if [ "$SETUP_MOD" -gt 0 ]; then
  echo "$STAGED" | grep -q "BUILD.md" || MISSING="$MISSING\n  - setup/BUILD.md (모듈 설명)"
fi

# 5. 레퍼런스 추가 → sync 실행 확인
NEW_REF=$(echo "$STAGED" | grep -cE '^plugins/.*/references/' || echo "0")
if [ "$NEW_REF" -gt 0 ]; then
  # sync는 별도 체크 불필요 (commit 전 수동)
  :
fi

if [ -n "$MISSING" ]; then
  cat <<MSG

❌ [BLOCK] 커밋 시 갱신 누락 감지!

  다음 파일을 같이 stage 하세요:
$(echo -e "$MISSING")

  배포용 솔루션 규칙: 기능 변경과 관련 문서는 같은 커밋에.
  불필요한 경우 (bugfix 등): git commit --no-verify

MSG
  exit 2
fi

exit 0
