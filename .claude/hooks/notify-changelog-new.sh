#!/usr/bin/env bash
# notify-changelog-new.sh — SessionStart hook
# changelog-new.md 가 존재하면 systemMessage 로 노출 → Claude 가 반드시 Read 하게 강제
# 2026-10-12 신설 — 알림 파일 만들어도 Claude 가 안 읽는 결함 fix
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

NOTIFY="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/state/changelog-new.md"
[ -f "$NOTIFY" ] || exit 0

cat <<EOF
[CHANGELOG ALERT] 공식 Claude Code / API changelog 변경 감지됨 — 지금 즉시 Read 필수.
  경로: $NOTIFY
  cache: $(dirname "$NOTIFY")/changelog-cache/
  룰: feedback_official_features_auto_check.md (⭐⭐+ 자율 적용 · ⭐⭐ 이하 보고만)
  처리 후: rm $NOTIFY
EOF
exit 0
