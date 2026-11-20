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
# 2026-11-18: 시작·끝 표시가 한 줄에 붙으면 sed 범위가 끝 표시를 못 찾아 파일 끝까지 모든 줄을 통계 줄로 덮었다
#   (병합 뒤 CLAUDE.md 2~9장 전부 소실 · 작업 트리 실측). 표시가 각자 한 줄씩 정확히 2개일 때만 갱신한다.
MARKS=$(grep -cE '^<!-- AUTO-STATS -->'$'\r''?$' "$CLAUDE_MD" 2>/dev/null)
if [ "$MARKS" != "2" ]; then
  echo "[auto-stats] skip — AUTO-STATS 표시가 각자 한 줄로 2개가 아님 ($MARKS) · CLAUDE.md 를 덮지 않음" >&2
  exit 0
fi
# --check (R351 F2 · 2026-11-20): 쓰지 않고 바뀔지만 판정 — exit 0 = 최신 · 1 = 갱신 필요 (커밋 훅은 읽기 전용으로 이것만 쓴다)
if [ "${1:-}" = "--check" ]; then
  CUR=$(sed -n '/<!-- AUTO-STATS -->/,/<!-- AUTO-STATS -->/{/<!-- AUTO-STATS -->/!p}' "$CLAUDE_MD" | tr -d '\r')
  [ "$CUR" = "$NEW_LINE" ] && exit 0
  exit 1
fi
sed -i "/<!-- AUTO-STATS -->/,/<!-- AUTO-STATS -->/{
  /<!-- AUTO-STATS -->/!{
    /<!-- AUTO-STATS -->/!s|.*|$NEW_LINE|
  }
}" "$CLAUDE_MD" 2>/dev/null

echo "[auto-stats] $NEW_LINE"
