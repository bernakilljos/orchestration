#!/bin/bash
# orca-status.sh — 전역 orca 큐 + 워커 상태 통합 조회
#
# 출력:
#   - 로컬 태스크 (this project)
#   - 전역 큐 (~/.claude/orca/)
#   - 워커 heartbeat (최근 60초 내 활동 여부)
#   - 마지막 sync 시각

set -uo pipefail
# set -e 제외 — glob 매치 없을 때 조기 종료 방지 (ls *.md → no match)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

now=$(date +%s)

echo "=== Orca 상태 ==="
echo ""

# 로컬 태스크
echo "[로컬 태스크]"
local_tasks=$(ls .claude/tasks/task-*.md 2>/dev/null | wc -l)
local_locks=$(ls .claude/tasks/locks/*.lock 2>/dev/null | wc -l)
local_done=$(ls .claude/tasks/done/*.md 2>/dev/null | wc -l)
echo "  활성: $local_tasks  락: $local_locks  완료: $local_done"
echo ""

# 전역 큐
echo "[전역 큐 (~/.claude/orca/)]"
if [ -d ~/.claude/orca/tasks ]; then
  global_tasks=$(ls ~/.claude/orca/tasks/*.md 2>/dev/null | wc -l)
  global_done=$(ls ~/.claude/orca/done/*.md 2>/dev/null | wc -l)
  global_locks=$(ls ~/.claude/orca/locks/*.lock 2>/dev/null | wc -l)
  echo "  활성: $global_tasks  락: $global_locks  완료: $global_done"
else
  echo "  (전역 큐 미초기화 — install.sh 실행 필요)"
fi
echo ""

# 워커 heartbeat
echo "[워커 heartbeat]"
HB_LOCAL=".claude/orca-heartbeat"
HB_GLOBAL="$HOME/.claude/orca/heartbeat"
for hb_name in "local:$HB_LOCAL" "global:$HB_GLOBAL"; do
  label="${hb_name%%:*}"
  path="${hb_name#*:}"
  if [ -f "$path" ]; then
    last=$(stat -c %Y "$path" 2>/dev/null || stat -f %m "$path" 2>/dev/null || echo 0)
    diff=$((now - last))
    if [ $diff -lt 60 ]; then
      echo "  $label: ✓ 활성 ($diff 초 전)"
    elif [ $diff -lt 300 ]; then
      echo "  $label: ⚠ 지연 (${diff}초 전)"
    else
      echo "  $label: 💤 휴면 (${diff}초 전)"
    fi
  else
    echo "  $label: ❌ heartbeat 없음"
  fi
done
echo ""

# 워커 상한 설정
echo "[워커 설정]"
GLOBAL_CFG="$HOME/.claude/orca/workers-config.json"
LOCAL_CFG=".claude/orca-workers-config.json"
if [ -f "$GLOBAL_CFG" ]; then
  python -c "import json,sys; c=json.load(open(sys.argv[1])); print('  전역 상한:', c.get('max_workers', {}))" "$GLOBAL_CFG" 2>/dev/null || echo "  전역: (파싱 실패)"
fi
if [ -f "$LOCAL_CFG" ]; then
  python -c "import json,sys; c=json.load(open(sys.argv[1])); print('  로컬 상한:', c)" "$LOCAL_CFG" 2>/dev/null || echo "  로컬: (파싱 실패)"
fi
echo ""

# 마지막 sync
echo "[Sync 상태]"
SYNC_MARKER=".claude/.last-sync"
if [ -f "$SYNC_MARKER" ]; then
  echo "  마지막: $(cat "$SYNC_MARKER")"
fi
# 플러그인 파일 개수
plugins_files=$(find plugins/ -name "*.md" -not -path "*/\.*" 2>/dev/null | wc -l)
claude_files=$(find .claude/commands/ .claude/skills/ -name "*.md" 2>/dev/null | wc -l)
echo "  plugins/ 파일 수: $plugins_files"
echo "  .claude/ sync 파일 수: $claude_files"
