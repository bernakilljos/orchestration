#!/bin/bash
# HOOK-05 — Post-Deploy: 배포 후 health check + 히스토리 기록
set -e

PROJECT="${1:-$(pwd)}"
cd "$PROJECT"

# Load deploy-config.env
if [ -f ".claude/deploy-config.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .claude/deploy-config.env 2>/dev/null || true
  set +a
fi

# 1. Health check (3회 retry)
HC_OK=0
if [ -n "${REMOTE_HOST:-}" ] && [ -n "${SERVICE_PORT:-}" ] && command -v curl >/dev/null 2>&1; then
  for i in 1 2 3; do
    HC=$(curl -s -o /dev/null -w "%{http_code}" "http://${REMOTE_HOST}:${SERVICE_PORT}" 2>/dev/null || echo "000")
    if [ "$HC" = "200" ]; then
      echo "[OK] Service healthy"
      HC_OK=1
      break
    fi
    echo "[$i/3] WAIT... status=$HC"
    [ "$i" -lt 3 ] && sleep 5
  done
  if [ "$HC_OK" -eq 0 ]; then
    echo "[FAIL] Service not responding"
    [ -f ".claude/scripts/rollback.sh" ] && bash .claude/scripts/rollback.sh
    [ -f ".claude/scripts/rollback.bat" ] && command -v cmd.exe >/dev/null && cmd.exe //c .claude/scripts/rollback.bat
  fi
else
  echo "[SKIP] REMOTE_HOST/SERVICE_PORT 미설정 - health check 건너뜀"
fi

# 2. Deploy history 기록
mkdir -p "docs/deploy-history"
{
  echo ""
  echo "## Deploy $(date '+%Y-%m-%d %H:%M:%S')"
  echo "- Env  : ${TARGET_ENV:-unknown}"
  echo "- Host : ${REMOTE_HOST:-unset}:${SERVICE_PORT:-unset}"
  echo "- HC   : $([ "$HC_OK" -eq 1 ] && echo OK || echo FAIL/SKIP)"
} >> "docs/deploy-history/history.md"

exit 0
