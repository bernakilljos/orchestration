#!/usr/bin/env bash
# check-official-features.sh — Claude Code 공식 changelog 1회/일 점검
#
# 룰: feedback_official_features_auto_check.md
# 트리거: SessionStart (async, idempotent — last-check flag 로 1일 1회)
# 출처:
#   - https://code.claude.com/docs/en/changelog
#   - https://docs.claude.com/en/release-notes/claude-code
#   - https://claude.com/blog
#
# 동작:
#   1. last-check flag 확인 (24시간 이내면 skip)
#   2. 공식 changelog 다운로드 -> 캐시
#   3. 이전 캐시와 diff
#   4. 변경 발견 -> .claude/state/changelog-new.md (Claude 가 다음 응답 전 읽음)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
STATE_DIR="${PROJECT_ROOT}/.claude/state"
CACHE_DIR="${STATE_DIR}/changelog-cache"
mkdir -p "$LOG_DIR" "$STATE_DIR" "$CACHE_DIR"

LOG="${LOG_DIR}/check-official-features.log"
FLAG="${STATE_DIR}/.changelog-last-check"
NEW_FILE="${STATE_DIR}/changelog-new.md"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# 24시간 이내면 skip
if [ -f "$FLAG" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$FLAG" 2>/dev/null || stat -f %m "$FLAG" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 86400 ] && exit 0
fi

echo "===== [$(date +%F_%T)] official features check start =====" >> "$LOG"

if ! command -v curl >/dev/null 2>&1; then
  echo "[WARN] curl 없음, skip" >> "$LOG"
  touch "$FLAG"
  exit 0
fi

URLS=(
  "https://docs.claude.com/en/release-notes/claude-code|claude-code-release.html"
  "https://code.claude.com/docs/en/changelog|claude-code-changelog.html"
  "https://docs.claude.com/en/release-notes/api|api-release.html"
)

CHANGED_ANY=0
for entry in "${URLS[@]}"; do
  url="${entry%%|*}"
  filename="${entry##*|}"
  CACHE="${CACHE_DIR}/${filename}"
  PREV="${CACHE}.prev"

  # 이전 캐시 백업
  [ -f "$CACHE" ] && cp "$CACHE" "$PREV"

  # 다운로드 (max 10초)
  if curl -sSL --max-time 10 -o "$CACHE.tmp" "$url" 2>>"$LOG"; then
    mv "$CACHE.tmp" "$CACHE"

    # diff 확인
    if [ -f "$PREV" ]; then
      if ! diff -q "$PREV" "$CACHE" >/dev/null 2>&1; then
        CHANGED_ANY=1
        echo "[CHANGED] $url" >> "$LOG"
      fi
    else
      # 첫 다운로드 = changed
      CHANGED_ANY=1
      echo "[NEW] $url" >> "$LOG"
    fi
  else
    echo "[FAIL] $url" >> "$LOG"
    rm -f "$CACHE.tmp"
  fi
done

# 변경 발견 -> 알림 파일 생성 (Claude가 다음 응답 전 읽음)
if [ "$CHANGED_ANY" = "1" ]; then
  cat > "$NEW_FILE" <<EOF
# Claude Code 공식 신기능 점검 알림

**점검 시각**: $(date +%F_%T)
**상태**: 공식 changelog 변경 감지

## 다음 행동
1. ${STATE_DIR}/changelog-cache/ 의 *.html 검토
2. 신기능 평가 (feedback_official_features_auto_check.md § 발견 -> 분석 -> 적용 매트릭스)
3.  이상 자동 적용,  이하 사용자 보고만
4. 적용 후 이 알림 파일 삭제: rm ${NEW_FILE}

## 출처
- https://docs.claude.com/en/release-notes/claude-code
- https://code.claude.com/docs/en/changelog
- https://docs.claude.com/en/release-notes/api
EOF
  echo "[$(date +%F_%T)] changelog 변경 감지 — $NEW_FILE 알림 생성" >> "$LOG"
else
  echo "[$(date +%F_%T)] no changes" >> "$LOG"
fi

touch "$FLAG"
echo "===== [$(date +%F_%T)] check done =====" >> "$LOG"
exit 0
