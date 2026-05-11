#!/bin/bash
# install-external-watchdog.sh — SessionStart 에서 자동 등록 (idempotent)
#
# Windows Task Scheduler 에 외부 watchdog 을 1분 간격으로 등록.
# 매 세션 시작 시 schtasks /Query 로 더블체크 — 이미 있으면 조용히 skip.
#
# 자동 등록 끄기: touch .claude/external-watchdog-disabled
# 강제 재등록: rm .claude/external-watchdog-disabled; rm .claude/state/external-watchdog-installed

set -uo pipefail

PROJECT="${CLAUDE_PROJECT_DIR:-${1:-$(pwd)}}"
cd "$PROJECT" 2>/dev/null || exit 0

# Windows 만 지원 (schtasks 필요)
command -v cmd.exe >/dev/null 2>&1 || exit 0

TASK_NAME="ClaudeOrcaExternalWatchdog"
DISABLE_FLAG="$PROJECT/.claude/external-watchdog-disabled"
REG_BAT="$PROJECT/.claude/scripts/external-watchdog-register.bat"

# 사용자가 명시적으로 끈 경우
if [ -f "$DISABLE_FLAG" ]; then
  exit 0
fi

# register .bat 없으면 skip
[ -f "$REG_BAT" ] || exit 0

# 이미 등록됐는지 확인 (TASK_NAME 공백 없어 escape 불필요)
# git bash 의 cmd.exe quote-escape 한계 우회 — 출력에서 TASK_NAME 매치만 확인
if cmd.exe //c "schtasks /Query /TN $TASK_NAME" 2>/dev/null | grep -q "$TASK_NAME"; then
  exit 0  # 이미 있음 — 조용히 통과
fi

# 등록: register.bat 을 cmd.exe 로 호출 (직접 path 만, escape 불필요)
WIN_BAT="$(cygpath -w "$REG_BAT" 2>/dev/null || echo "$REG_BAT")"
cmd.exe //c "$WIN_BAT" >/dev/null 2>&1

# 결과 확인 (다시 Query)
if cmd.exe //c "schtasks /Query /TN $TASK_NAME" 2>/dev/null | grep -q "$TASK_NAME"; then
  echo "[external-watchdog] Auto-registered ($TASK_NAME, 1m interval)"
  mkdir -p "$PROJECT/.claude/state"
  date '+%Y-%m-%dT%H:%M:%S' > "$PROJECT/.claude/state/external-watchdog-installed"
else
  echo "[external-watchdog] 등록 실패 — 수동 실행 필요: $REG_BAT"
fi

exit 0
