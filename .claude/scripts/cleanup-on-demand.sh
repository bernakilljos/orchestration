#!/usr/bin/env bash
# cleanup-on-demand.sh — /cleanup command 의 handler
# 사용자 명시 지시 시만 발동. dry-run 기본, --apply 시 실삭제·archive.
#
# 사용:
#   bash .claude/scripts/cleanup-on-demand.sh <target> [--apply]
#   target: outputs | docs | screens | state | logs | tasks | plugins | all

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

TARGET="${1:-}"
APPLY="${2:-}"
DRY_RUN=1
[ "$APPLY" = "--apply" ] && DRY_RUN=0

TS=$(date '+%Y-%m-%d_%H%M')
LOG=".claude/logs/cleanup-on-demand.log"
BACKUP_DIR=".claude/backups"
mkdir -p "$(dirname "$LOG")" "$BACKUP_DIR"

if [ -z "$TARGET" ]; then
  echo "usage: $0 <outputs|docs|screens|state|logs|tasks|plugins|all> [--apply]"
  exit 2
fi

# 보호 목록 (절대 건드림 X)
PROTECTED=(
  ".claude/state/orca.db"
  ".claude/state/session-snapshot.md"
  ".claude/state/workers"
  ".env"
  ".git"
  ".claude-plugin"
)

is_protected() {
  local path="$1"
  for p in "${PROTECTED[@]}"; do
    case "$path" in
      "$p"|"$p"/*) return 0;;
    esac
  done
  return 1
}

log_line() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

cleanup_outputs() {
  local age_days=30
  local archive_dir="outputs/_archive/$(date '+%Y-%m')"
  local count=0
  local size_total=0

  echo "=== cleanup outputs (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="
  [ ! -d outputs ] && { echo "outputs/ 없음 — skip"; return; }

  mkdir -p "$archive_dir"

  while IFS= read -r f; do
    is_protected "$f" && continue
    size=$(du -k "$f" 2>/dev/null | cut -f1)
    size_total=$((size_total + size))
    count=$((count + 1))
    echo "  - $f ($size KB)"
    if [ $DRY_RUN -eq 0 ]; then
      rel=$(echo "$f" | sed 's|^outputs/||')
      mkdir -p "$archive_dir/$(dirname "$rel")"
      mv "$f" "$archive_dir/$rel" 2>/dev/null && log_line "archived: $f"
    fi
  done < <(find outputs -mindepth 2 -type f -mtime +$age_days \
                       ! -path "outputs/_archive/*" 2>/dev/null | head -200)

  echo "후보: $count 파일 ($((size_total / 1024)) MB)"
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_docs() {
  local age_days=90
  local archive_dir="docs/_archive/$(date '+%Y-%m')"
  local count=0

  echo "=== cleanup docs (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="

  mkdir -p "$archive_dir"

  for dir in docs/[0-9][0-9][0-9][0-9]-*; do
    [ ! -d "$dir" ] && continue
    is_protected "$dir" && continue
    # 디렉토리 mtime
    mtime=$(stat -c %Y "$dir" 2>/dev/null || stat -f %m "$dir" 2>/dev/null || echo 0)
    age=$(( ($(date +%s) - mtime) / 86400 ))
    if [ "$age" -gt $age_days ]; then
      count=$((count + 1))
      echo "  - $dir (age ${age}d)"
      if [ $DRY_RUN -eq 0 ]; then
        mv "$dir" "$archive_dir/" 2>/dev/null && log_line "archived: $dir"
      fi
    fi
  done

  # docs/deploy-history/, docs/screens/_*.log 등 임시 — 14일+ 삭제
  find docs -maxdepth 2 -name "_*.log" -mtime +14 2>/dev/null | while read f; do
    echo "  - $f (log 14d+)"
    [ $DRY_RUN -eq 0 ] && { rm -f "$f"; log_line "removed: $f"; }
  done

  echo "후보: $count 디렉토리"
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_screens() {
  local age_days=14
  echo "=== cleanup screens (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="
  [ ! -d docs/screens ] && { echo "docs/screens/ 없음 — skip"; return; }

  local count=0
  find docs/screens -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.log" \) -mtime +$age_days 2>/dev/null | head -200 | while read f; do
    count=$((count + 1))
    echo "  - $f"
    [ $DRY_RUN -eq 0 ] && { rm -f "$f"; log_line "removed: $f"; }
  done
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_state() {
  local age_days=30
  echo "=== cleanup state (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="
  [ ! -d .claude/state ] && return

  find .claude/state -type f -mtime +$age_days 2>/dev/null | while read f; do
    is_protected "$f" && continue
    echo "  - $f"
    [ $DRY_RUN -eq 0 ] && { rm -f "$f"; log_line "removed: $f"; }
  done
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_logs() {
  local age_days=14
  echo "=== cleanup logs (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="
  find .claude/logs -type f -name "*.log" -mtime +$age_days 2>/dev/null | while read f; do
    echo "  - $f"
    [ $DRY_RUN -eq 0 ] && { rm -f "$f"; log_line "removed: $f"; }
  done
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_tasks() {
  local age_days=30
  echo "=== cleanup tasks (mode=$([ $DRY_RUN -eq 1 ] && echo dry-run || echo apply)) ==="
  [ ! -d .claude/tasks/done ] && return
  find .claude/tasks/done -type f -mtime +$age_days 2>/dev/null | while read f; do
    echo "  - $f"
    [ $DRY_RUN -eq 0 ] && { rm -f "$f"; log_line "removed: $f"; }
  done
  [ $DRY_RUN -eq 1 ] && echo "실삭제: --apply 옵션 필요"
}

cleanup_plugins() {
  echo "=== cleanup plugins — spec-only 휴면 review (manual) ==="
  for p in plugins/*/plugin.json; do
    [ -f "$p" ] || continue
    status=$(grep -E '"status":\s*"' "$p" | head -1 | sed -E 's/.*"status":\s*"([^"]+)".*/\1/')
    if [ "$status" = "spec-only" ]; then
      plug=$(dirname "$p" | xargs -n1 basename)
      # 마지막 commit
      last_commit=$(git log -1 --format=%ct -- "plugins/$plug" 2>/dev/null || echo 0)
      age=$(( ($(date +%s) - last_commit) / 86400 ))
      if [ "$age" -gt 90 ]; then
        echo "  - $plug (spec-only, last commit ${age}d ago) → deprecated 후보"
      fi
    fi
  done
  echo "수동 review 필요. plugin.json 에 \"deprecated\": true 추가 후 commit."
}

case "$TARGET" in
  outputs)  cleanup_outputs  ;;
  docs)     cleanup_docs     ;;
  screens)  cleanup_screens  ;;
  state)    cleanup_state    ;;
  logs)     cleanup_logs     ;;
  tasks)    cleanup_tasks    ;;
  plugins)  cleanup_plugins  ;;
  all)
    cleanup_outputs; echo
    cleanup_docs; echo
    cleanup_screens; echo
    cleanup_state; echo
    cleanup_logs; echo
    cleanup_tasks; echo
    cleanup_plugins
    ;;
  *)
    echo "unknown target: $TARGET" >&2
    exit 2
    ;;
esac

log_line "cleanup-on-demand: target=$TARGET dry-run=$DRY_RUN done"
