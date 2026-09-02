#!/usr/bin/env bash
# Rule/CLAUDE.md 변경 시 관련 위치 자동 grep · 확산 필요 여부 알림
# 근거: 2026-09-02 사용자 지적 — "하나 알려주면 전체 페이지 기준 확인해서 바꿔야 하는데 안 바뀜"
set -eu

# guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

# PostToolUse Edit/Write · $CLAUDE_TOOL_ARGS 에 파일 경로 있음
# JSON 파싱 없이 grep 으로 확인

TOOL_INPUT="${TOOL_INPUT:-}"
if [ -z "$TOOL_INPUT" ]; then
  # stdin fallback
  TOOL_INPUT="$(cat 2>/dev/null || true)"
fi

# 변경 파일 추출
FILE=$(echo "$TOOL_INPUT" | grep -oP '"file_path"\s*:\s*"[^"]+' | head -1 | sed 's/.*"file_path"\s*:\s*"//')

# .claude/rules/*.md · CLAUDE.md · guide.txt 만 대상
case "$FILE" in
  *.claude/rules/*.md|*CLAUDE.md|*guide.txt)
    RULE_NAME=$(basename "$FILE" .md)
    ;;
  *)
    exit 0
    ;;
esac

# 확산 후보 검색
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
MATCHES=""

# CLAUDE.md § 7 조항 안 rule 참조
if [ -f "$ROOT/CLAUDE.md" ] && grep -q "$RULE_NAME" "$ROOT/CLAUDE.md" 2>/dev/null; then
  MATCHES="$MATCHES\n  · CLAUDE.md"
fi

# guide.txt
if [ -f "$ROOT/guide.txt" ] && grep -q "$RULE_NAME" "$ROOT/guide.txt" 2>/dev/null; then
  MATCHES="$MATCHES\n  · guide.txt"
fi

# 다른 rule 파일에서 참조
OTHER_RULES=$(grep -l "$RULE_NAME" "$ROOT/.claude/rules/"*.md 2>/dev/null | grep -v "$FILE" | head -5 || true)
if [ -n "$OTHER_RULES" ]; then
  while IFS= read -r r; do
    MATCHES="$MATCHES\n  · $r"
  done <<< "$OTHER_RULES"
fi

# memory 파일에서 참조
MEM_DIR="${HOME:-/tmp}/.claude/projects/C--pjt-orchestration-v1/memory"
if [ -d "$MEM_DIR" ]; then
  MEM_MATCH=$(grep -l "$RULE_NAME" "$MEM_DIR/"*.md 2>/dev/null | head -3 || true)
  if [ -n "$MEM_MATCH" ]; then
    while IFS= read -r m; do
      MATCHES="$MATCHES\n  · $m (memory)"
    done <<< "$MEM_MATCH"
  fi
fi

# setup/templates 참조
if grep -rql "$RULE_NAME" "$ROOT/setup/templates/" 2>/dev/null; then
  MATCHES="$MATCHES\n  · setup/templates/ (install 배포)"
fi

# 알림 (조합이 있을 때만)
if [ -n "$MATCHES" ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "📢 Rule 확산 필요 — [$RULE_NAME] 변경 감지. 다음 위치도 함께 갱신 필요:${MATCHES}\n\n※ '하나 알려주면 전체 안 바뀜' 방지 (auto-propagate rule)"
  }
}
EOF
fi

# log 남기기
LOG_DIR="$ROOT/.claude/logs"
mkdir -p "$LOG_DIR"
echo "[$(date -Iseconds)] $FILE → matches=$(echo -e "$MATCHES" | wc -l)" >> "$LOG_DIR/propagate.log"

exit 0
