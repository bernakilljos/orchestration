#!/usr/bin/env bash
# stop-snapshot.sh — 턴 종료·압축 직전 최소 메타 스냅샷 기록
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

# 3. snapshot.md 에 "Last Hook Record" 섹션 append (없으면 뼈대 생성)
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
    # sed로 섹션 이후 첫 줄만 교체 (Windows Git Bash 호환 위해 단순 append 방식으로)
    python - "$SNAP" "$TS" "$EVENT" "$BRANCH" <<'PYEOF' 2>/dev/null || true
import sys, re, pathlib
p = pathlib.Path(sys.argv[1])
ts, event, branch = sys.argv[2], sys.argv[3], sys.argv[4]
text = p.read_text(encoding='utf-8', errors='ignore')
line = f"[{ts}] event={event} branch={branch}"
# Last Hook Record 섹션 교체
new = re.sub(
    r"(### Last Hook Record\n)(.*?)(\Z|\n### )",
    lambda m: f"{m.group(1)}{line}\n{m.group(3)}" if m.group(3).startswith("\n###") else f"{m.group(1)}{line}\n",
    text,
    count=1,
    flags=re.DOTALL,
)
p.write_text(new, encoding='utf-8')
PYEOF
  else
    printf "\n### Last Hook Record\n[%s] event=%s branch=%s\n" "$TS" "$EVENT" "$BRANCH" >> "$SNAP"
  fi
fi

exit 0
