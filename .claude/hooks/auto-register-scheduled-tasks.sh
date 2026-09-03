#!/usr/bin/env bash
# auto-register-scheduled-tasks.sh — SessionStart hook
#
# 목적: 사용자가 claude 세션 안 열어도 daily 자동 점검이 돌도록 OS 수준 스케줄 등록
# 룰: CLAUDE.md § 3.6 24/7 자동화 - feedback_zero_touch_automation.md
# Idempotent: 이미 등록됐으면 ps1 가 skip 출력
#
# Windows: schtasks (Task Scheduler) 사용 — register-official-features-task.ps1
# Linux/Mac: cron (TODO — exec_remote VPS 환경에서 만들 때)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/auto-register-tasks.log"

echo "===== [$(date +%F_%T)] auto-register start =====" >> "$LOG"

# Windows 감지
if command -v schtasks.exe >/dev/null 2>&1 || [ -n "$WINDIR" ] || [ -n "$SYSTEMROOT" ]; then
  PS1="${PROJECT_ROOT}/setup/modules/register-official-features-task.ps1"
  if [ -f "$PS1" ]; then
    # cygpath 없으면 그대로 (powershell 가 unix-style path 도 처리)
    PS1_WIN=$(cygpath -w "$PS1" 2>/dev/null || echo "$PS1")
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_WIN" >> "$LOG" 2>&1 || true
  else
    echo "[WARN] ps1 not found: $PS1" >> "$LOG"
  fi
elif command -v crontab >/dev/null 2>&1; then
  # Linux/Mac (TODO 정식 지원)
  echo "[INFO] cron environment detected — manual register: crontab -e 후 0 9 * * * bash $PROJECT_ROOT/.claude/scripts/check-official-features.sh" >> "$LOG"
else
  echo "[INFO] no scheduler found — SessionStart hook 만으로 동작" >> "$LOG"
fi

echo "===== [$(date +%F_%T)] auto-register done =====" >> "$LOG"
exit 0
