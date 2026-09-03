#!/bin/bash
# =====================================================
# monitor.sh — Server health monitoring
# Usage: bash .claude/scripts/monitor.sh [--health-only] [--all]
# --health-only  Health check only (use right after deploy)
# --all          Check all servers (based on check_server list in this script)
# =====================================================
source .claude/deploy-config.env 2>/dev/null || true

HEALTH_ONLY=false
CHECK_ALL=false
MAX_RETRY=5
INTERVAL=10
REPORT="docs/monitor-report.md"
mkdir -p docs

while [[ $# -gt 0 ]]; do
  case "$1" in
    --health-only) HEALTH_ONLY=true; shift ;;
    --all) CHECK_ALL=true; shift ;;
    *) shift ;;
  esac
done

# -------------------------------------------------------
# Health check loop (right after deploy)
# -------------------------------------------------------
health_check_loop() {
  local host="$1"
  local port="$2"
  local app="$3"
  local fail=0

  echo "Health check loop: http://${host}:${port} (max ${MAX_RETRY} attempts)"

  for i in $(seq 1 $MAX_RETRY); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      "http://${host}:${port}" 2>/dev/null || echo "000")

    if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ] || [ "$STATUS" = "301" ]; then
      echo "[${i}/${MAX_RETRY}] OK [$STATUS]"
      return 0
    else
      fail=$((fail+1))
      echo "[${i}/${MAX_RETRY}] FAIL [$STATUS] -> ${fail} failure(s)"
      if [ "$fail" -ge 3 ]; then
        echo "3 consecutive failures -> Triggering auto rollback"
        bash .claude/scripts/rollback.sh
        bash .claude/scripts/notify.sh "danger" \
          "Health check failed 3 times -> Auto rollback executed (${host}:${port})"
        return 1
      fi
      sleep $INTERVAL
    fi
  done

  echo "[FAIL] Health check final failure"
  return 1
}

# -------------------------------------------------------
# Single server detailed check
# -------------------------------------------------------
check_server() {
  local user_host="$1"
  local label="$2"

  echo ""
  echo "=== $label ($user_host) ==="

  ssh -o ConnectTimeout=5 "$user_host" << 'REMOTE' 2>/dev/null || echo "[Connection failed]"
echo "--- PM2 ---"
pm2 list --no-color 2>/dev/null | grep -E "online|stopped|error|errored" | head -10 || echo "No PM2"

echo "--- Nginx ---"
systemctl is-active nginx 2>/dev/null || echo "Nginx not found/inactive"

echo "--- Ports ---"
ss -tlnp 2>/dev/null | grep -E ":(6060|6061|7777|7778|3333|8080|80|443) " | awk '{print $4}' || echo "No matching ports"

echo "--- Memory ---"
free -h | awk 'NR==2{printf "Used: %s / Total: %s\n", $3, $2}'

echo "--- Disk ---"
df -h / | awk 'NR==2{print "Root:", $5, "("$4" free)"}'

echo "--- CPU Load ---"
uptime | awk -F'load average:' '{print "Load:" $2}'

echo "--- PM2 Crash Detection ---"
pm2 jlist 2>/dev/null | python3 -c "
import json, sys
try:
    apps = json.load(sys.stdin)
    for app in apps:
        name = app.get('name','')
        status = app.get('pm2_env',{}).get('status','')
        restarts = app.get('pm2_env',{}).get('restart_time',0)
        if status != 'online':
            print(f'  FAIL: {name} status={status}')
        elif restarts > 5:
            print(f'  WARN: {name} restarted {restarts} times')
        else:
            print(f'  OK:   {name}')
except:
    print('  No PM2 info')
" 2>/dev/null || true
REMOTE
}

# -------------------------------------------------------
# Execute
# -------------------------------------------------------
if [ "$HEALTH_ONLY" = true ]; then
  health_check_loop "$REMOTE_HOST" "$SERVICE_PORT" "$PM2_APP_NAME"
  exit $?
fi

if [ "$CHECK_ALL" = true ]; then
  echo "=============================="
  echo " All Servers Check"
  echo " $(date '+%Y-%m-%d %H:%M:%S')"
  echo "=============================="

  # Add your servers here:
  # check_server "ec2-user@SERVER_IP" "server-name (role)"
  check_server "${REMOTE_USER}@${REMOTE_HOST}" "$TARGET_ENV ($REMOTE_HOST)"

  echo ""
  echo "[DONE] All servers check complete -> $REPORT"
else
  # Default: single server check + health check
  check_server "${REMOTE_USER}@${REMOTE_HOST}" "$TARGET_ENV ($REMOTE_HOST)"

  echo ""
  echo "=== Health Check ==="
  health_check_loop "$REMOTE_HOST" "$SERVICE_PORT" "$PM2_APP_NAME"
fi

# Save results
{
  echo "## Monitor Report — $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Server: $REMOTE_HOST | Port: $SERVICE_PORT"
} > "$REPORT"
