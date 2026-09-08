#!/usr/bin/env bash
# stop-snapshot.sh — 턴 종료-압축 직전 최소 메타 스냅샷 기록
# 토큰 부족으로 Claude가 말 못 하고 끊겨도 이 훅은 항상 실행됨
# Windows Git Bash 호환
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_DIR" || exit 0

CACHE_DIR=".claude/context-cache"
LOG="$CACHE_DIR/guard.log"
SNAP="$CACHE_DIR/session-snapshot.md"

mkdir -p "$CACHE_DIR" 2>/dev/null || exit 0

# 본문 재생성 — session-snapshot-save.py 가 정본 (한 줄만 갱신하던 결함 교정 2026-09-08)
_regen_snapshot() {
  local PY
  PY="$(command -v python 2>/dev/null || command -v python3 2>/dev/null)"
  [ -n "$PY" ] || return 1
  "$PY" "$PROJECT_DIR/.claude/scripts/session-snapshot-save.py" >/dev/null 2>&1
}

TS="$(date '+%Y-%m-%d %H:%M:%S')"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'n/a')"
EVENT="${1:-Stop}"

# 1. guard.log 에 append (히스토리 유지)
{
  echo "---"
  echo "[$TS] event=$EVENT branch=$BRANCH"
  echo "## git status"
  git status -s 2>/dev/null | head -30
  echo "## recent edits (last 10 tracked)"
  git diff --name-only HEAD 2>/dev/null | head -10
} >> "$LOG"

# 2. guard.log 크기 관리 (500줄 넘으면 뒤 300줄만 유지)
LINES=$(wc -l < "$LOG" 2>/dev/null | tr -d ' ')
if [ "${LINES:-0}" -gt 500 ]; then
  tail -n 300 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

# 3. 문맥이 끊기는 시점(PreCompact/PostCompact/SessionEnd)에는 본문 전체를 다시 쓴다.
#    Stop 은 턴마다 발생하므로 한 줄만 갱신 (비용).
case "$EVENT" in
  PreCompact|PostCompact|SessionEnd)
    if _regen_snapshot; then
      printf "
### Last Hook Record
[%s] event=%s branch=%s
" "$TS" "$EVENT" "$BRANCH" >> "$SNAP"
      exit 0
    fi
    ;;
esac

# 4. snapshot.md 에 "Last Hook Record" 섹션 append (없으면 뼈대 생성)
if [ ! -f "$SNAP" ]; then
  cat > "$SNAP" <<EOF
## Session Snapshot - $TS

### Current Task
- Title:  [작업 미지정 — Claude가 다음 턴에 채움]
- Goal:   [미정]
- Status: unknown

### Pipeline Progress
- [ ] 상태 미기록

### Next Command
[미정]

### Modified Files
$(git status -s 2>/dev/null | head -20 | sed 's/^/- /')

### Key Decisions
[미기록]

### Pending / Caution
- Claude의 능동 스냅샷(guard_snapshot skill) 미실행 — 훅만 기록됨

### Last Hook Record
[$TS] event=$EVENT branch=$BRANCH
EOF
else
  # 기존 파일의 "Last Hook Record" 섹션만 갱신 (없으면 append)
  if grep -q "^### Last Hook Record" "$SNAP"; then
    LINE="[$TS] event=$EVENT branch=$BRANCH"
    sed -i "/^### Last Hook Record$/{ n; s/.*/$LINE/ }" "$SNAP" 2>/dev/null || true
  else
    printf "\n### Last Hook Record\n[%s] event=%s branch=%s\n" "$TS" "$EVENT" "$BRANCH" >> "$SNAP"
  fi
fi

exit 0
