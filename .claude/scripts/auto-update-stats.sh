#!/usr/bin/env bash
# auto-update-stats.sh — CLAUDE.md AUTO-STATS 라인 자동 갱신
# Stop hook 또는 수동 호출
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

CLAUDE_MD="CLAUDE.md"
[ -f "$CLAUDE_MD" ] || exit 0

# 실제 카운트
PLUGINS=$(ls -d plugins/*/ 2>/dev/null | grep -v _template | wc -l | tr -d ' ')
RULES=$(ls .claude/rules/*.md 2>/dev/null | wc -l | tr -d ' ')
HOOKS=$(find plugins -path "*/hooks/*.sh" -type f 2>/dev/null | wc -l | tr -d ' ')
SCRIPTS=$(ls .claude/scripts/*.{sh,py} 2>/dev/null | wc -l | tr -d ' ')
TODAY=$(date +%Y-%m-%d)

NEW_LINE="> **현재 상태** ($TODAY): plugins $PLUGINS stable + 0 spec-only - rules $RULES - hooks $HOOKS - scripts $SCRIPTS"

# AUTO-STATS 태그 사이의 라인 교체
sed -i "/<!-- AUTO-STATS -->/,/<!-- AUTO-STATS -->/{
  /<!-- AUTO-STATS -->/!{
    /<!-- AUTO-STATS -->/!s|.*|$NEW_LINE|
  }
}" "$CLAUDE_MD" 2>/dev/null

echo "[auto-stats] $NEW_LINE"
