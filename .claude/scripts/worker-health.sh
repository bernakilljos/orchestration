#!/bin/bash
# worker-health.sh — 워커별 heartbeat 점검 + stale 감지 + 재시작 권고
#
# 현재 시스템은 단일 heartbeat 파일(.claude/orca-heartbeat)만 갱신.
# 이 스크립트는 워커별 세분화된 상태를 추적:
#   - 개별 워커 heartbeat 파일 (.claude/state/workers/<role>-<id>.hb)
#   - 5분 이상 미갱신 → stale
#   - 10분 이상 → dead (재시작 권고)
#
# 사용법:
#   bash .claude/scripts/worker-health.sh              현재 상태
#   bash .claude/scripts/worker-health.sh --check      dead 있으면 exit 2
#   bash .claude/scripts/worker-health.sh --reset <worker>  heartbeat 리셋
#   bash .claude/scripts/worker-health.sh --beat <worker>   heartbeat 갱신 (워커가 직접 호출)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

STATE_DIR=".claude/state/workers"
STALE_SEC=300    # 5 min
DEAD_SEC=600     # 10 min

mkdir -p "$STATE_DIR"

MODE="status"
TARGET=""

case "${1:-}" in
  --check) MODE="check" ;;
  --reset) MODE="reset"; TARGET="${2:-}" ;;
  --beat)  MODE="beat";  TARGET="${2:-}" ;;
  -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
esac

now=$(date +%s)

# heartbeat 기록 (워커가 호출)
if [ "$MODE" = "beat" ]; then
  [ -z "$TARGET" ] && { echo "Usage: --beat <worker_id>"; exit 1; }
  echo "$now" > "$STATE_DIR/$TARGET.hb"
  exit 0
fi

# 리셋
if [ "$MODE" = "reset" ]; then
  [ -z "$TARGET" ] && { echo "Usage: --reset <worker_id>"; exit 1; }
  rm -f "$STATE_DIR/$TARGET.hb"
  echo "Reset: $TARGET"
  exit 0
fi

# status / check
stale=0
dead=0
alive=0

echo "=== Worker Health ==="
echo "  (stale: >${STALE_SEC}s, dead: >${DEAD_SEC}s)"
echo ""

if [ -z "$(ls $STATE_DIR/*.hb 2>/dev/null)" ]; then
  echo "  (워커 heartbeat 없음 — 아직 아무도 --beat 호출 안 함)"
  echo ""
  echo "  워커 스크립트에 아래 추가:"
  echo "    bash .claude/scripts/worker-health.sh --beat codex-1"
  exit 0
fi

for hb in "$STATE_DIR"/*.hb; do
  [ -f "$hb" ] || continue
  worker=$(basename "$hb" .hb)
  last=$(cat "$hb" 2>/dev/null || echo 0)
  diff=$((now - last))

  if [ "$diff" -ge "$DEAD_SEC" ]; then
    echo "  💀 $worker: DEAD (${diff}s) — 재시작 권고"
    dead=$((dead+1))
  elif [ "$diff" -ge "$STALE_SEC" ]; then
    echo "  ⚠️  $worker: STALE (${diff}s)"
    stale=$((stale+1))
  else
    echo "  ✓  $worker: OK (${diff}s 전)"
    alive=$((alive+1))
  fi
done

echo ""
echo "  Summary: alive=$alive  stale=$stale  dead=$dead"

if [ "$dead" -gt 0 ] && [ "$MODE" = "check" ]; then
  exit 2
fi
exit 0
