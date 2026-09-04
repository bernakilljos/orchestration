#!/usr/bin/env bash
# post-session.sh — Claude Code v2.1.169+ lifecycle hook
#
# 트리거: Claude Code 세션이 *어떻게든* 종료될 때 (사용자 명시 종료-kill-crash-timeout)
# vs SessionEnd: 사용자 명시 종료만
# 용도: self-hosted runner (exec_remote VPS 24/7) 환경에서 snapshot-sync-log archive
#
# 동작:
#   1. 종료 시각 + reason (env: CLAUDE_SESSION_END_REASON) log
#   2. .claude/state/ 의 마지막 metric snapshot 보존 (logs/post-session.log)
#   3. exec_remote/exec_session_guard 가 활성이면 sync 트리거 (있을 때만)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/post-session.log"

REASON="${CLAUDE_SESSION_END_REASON:-unspecified}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TS=$(date +%F_%T)

echo "===== [$TS] post-session start =====" >> "$LOG"
echo "[session_id] $SESSION_ID" >> "$LOG"
echo "[reason]     $REASON" >> "$LOG"

# Optional snapshot — exec_session_guard skill 활성이면 호출
if [ -x "${PROJECT_ROOT}/.claude/scripts/guard-save.sh" ]; then
  bash "${PROJECT_ROOT}/.claude/scripts/guard-save.sh" --reason "post-session:$REASON" >> "$LOG" 2>&1 || true
fi

# Optional sync — exec_remote 활성이면 호출 (sync-to-team 또는 remote heartbeat)
if [ -x "${PROJECT_ROOT}/.claude/scripts/sync-to-team.sh" ] && [ "${POST_SESSION_AUTO_SYNC:-0}" = "1" ]; then
  bash "${PROJECT_ROOT}/.claude/scripts/sync-to-team.sh" --quiet >> "$LOG" 2>&1 || true
fi

echo "===== [$(date +%F_%T)] post-session done =====" >> "$LOG"
exit 0
