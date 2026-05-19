#!/usr/bin/env bash
# periodic-snapshot.sh — PostToolUse .* 에 등록, 5분 간격 자동 스냅샷
# 목적: 갑자기 꺼져도 최근 5분 이내 스냅샷 보존
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_DIR" || exit 0

CACHE_DIR=".claude/context-cache"
SNAP="$CACHE_DIR/session-snapshot.md"
LAST_TS_FILE="$CACHE_DIR/.last-periodic-snapshot"
INTERVAL=300  # 5분 (초)

mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0

# 마지막 스냅샷 시각 확인 — INTERVAL 미경과면 skip (경량)
NOW=$(date +%s)
if [ -f "$LAST_TS_FILE" ]; then
  LAST=$(cat "$LAST_TS_FILE" 2>/dev/null | tr -d '[:space:]')
  ELAPSED=$(( NOW - ${LAST:-0} ))
  if [ "$ELAPSED" -lt "$INTERVAL" ]; then
    exit 0  # 5분 안 됐으면 skip
  fi
fi

# 타임스탬프 갱신
echo "$NOW" > "$LAST_TS_FILE"

TS="$(date '+%Y-%m-%d %H:%M:%S')"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"
HEAD="$(git rev-parse --short HEAD 2>/dev/null || echo 'n/a')"

# Modified files 수집
MODIFIED=$(git status -s 2>/dev/null | head -20)
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null)

# snapshot 갱신 (Last Hook Record 섹션 — pure bash, python 미사용)
LINE="[$TS] event=PeriodicSnapshot branch=$BRANCH HEAD=$HEAD"
if [ -f "$SNAP" ]; then
  if grep -q "^### Last Hook Record" "$SNAP"; then
    # Last Hook Record 다음 줄만 교체 (sed)
    sed -i "/^### Last Hook Record$/{ n; s/.*/$LINE/ }" "$SNAP" 2>/dev/null || true
  else
    printf "\n### Last Hook Record\n%s\n" "$LINE" >> "$SNAP"
  fi
else
  # 스냅샷 없으면 뼈대 생성
  cat > "$SNAP" <<EOF
# Session Snapshot — $TS (auto-periodic)

## Current State
- Branch: $BRANCH
- HEAD: $HEAD
- Event: PeriodicSnapshot (자동)

## Modified Files
$(echo "$MODIFIED" | sed 's/^/- /')

## Recent Commits
$(echo "$RECENT_COMMITS" | sed 's/^/- /')

## Pending
- Claude 능동 스냅샷 미실행 — 주기 hook 기록

### Last Hook Record
[$TS] event=PeriodicSnapshot branch=$BRANCH HEAD=$HEAD
EOF
fi

exit 0
