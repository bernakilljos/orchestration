#!/bin/bash
# =====================================================
# rollback.sh — Auto rollback
# Usage: bash .claude/scripts/rollback.sh [backup-name]
# Example: bash .claude/scripts/rollback.sh dist_20260330_143000
# If no backup name given, restores the most recent backup
# =====================================================
set -e
source .claude/deploy-config.env

TARGET_BACKUP="${1:-}"

echo ""
echo "=============================="
echo " SKILL-07 Rollback"
echo " Server: $REMOTE_HOST"
echo "=============================="

# Check current service status
echo "[1/5] Checking current status..."
ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "pm2 status ${PM2_APP_NAME} 2>/dev/null | head -5 || echo 'No PM2'"

# Check backup list
echo "[2/5] Checking backups..."
BACKUP_LIST=$(ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "ls -t ${APP_PATH}/backup/ 2>/dev/null | head -5" || echo "")

if [ -z "$BACKUP_LIST" ]; then
  echo "[BLOCK] No backups found → Rollback not possible"
  bash .claude/scripts/notify.sh "danger" "Rollback failed: No backups ($REMOTE_HOST)"
  exit 1
fi

# Determine target backup
if [ -z "$TARGET_BACKUP" ]; then
  TARGET_BACKUP=$(echo "$BACKUP_LIST" | head -1)
  echo "Restoring from most recent backup: $TARGET_BACKUP"
else
  echo "Restoring from specified backup: $TARGET_BACKUP"
fi

# Emergency backup of current version (before rollback)
echo "[3/5] Emergency backup of current version..."
ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "[ -d ${APP_PATH}/dist ] && \
   cp -r ${APP_PATH}/dist ${APP_PATH}/backup/dist_pre_rollback_$(date '+%Y%m%d_%H%M%S') 2>/dev/null || true"

# Execute rollback
echo "[4/5] Executing rollback..."
if echo "$TARGET_BACKUP" | grep -q "dist_"; then
  # Frontend rollback
  ssh ${REMOTE_USER}@${REMOTE_HOST} \
    "rm -rf ${APP_PATH}/dist && \
     cp -r ${APP_PATH}/backup/${TARGET_BACKUP} ${APP_PATH}/dist && \
     sudo nginx -t && sudo systemctl reload nginx && \
     echo 'Frontend rollback complete'"
else
  # Backend jar rollback
  ssh ${REMOTE_USER}@${REMOTE_HOST} \
    "pm2 stop ${PM2_APP_NAME} 2>/dev/null || true && \
     mv ${APP_PATH}/*.jar ${APP_PATH}/backup/rollback_from_$(date '+%Y%m%d_%H%M%S').jar 2>/dev/null || true && \
     cp ${APP_PATH}/backup/${TARGET_BACKUP} ${APP_PATH}/ && \
     pm2 restart ${PM2_APP_NAME} 2>/dev/null || \
     pm2 start ${APP_PATH}/*.jar --name ${PM2_APP_NAME} && \
     echo 'Backend rollback complete'"
fi

# Health check
echo "[5/5] Health check..."
sleep 5
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://${REMOTE_HOST}:${SERVICE_PORT}" 2>/dev/null || echo "000")

if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then
  echo "[OK] Rollback success → Service healthy [$STATUS]"
  MSG="Auto rollback complete ($TARGET_ENV) → Restored: $TARGET_BACKUP"
  bash .claude/scripts/notify.sh "warning" "$MSG"
else
  echo "[FAIL] Service still failing after rollback [$STATUS] → Manual check required"
  bash .claude/scripts/notify.sh "danger" "Service still failing after rollback [$STATUS] ($REMOTE_HOST) → Manual check required"
  exit 1
fi

# Record rollback history
cat >> docs/deploy-history/history.md <<EOF

## Rollback — $(date '+%Y-%m-%d %H:%M:%S')
- Env    : ${TARGET_ENV}
- Server : ${REMOTE_HOST}
- Restored version: ${TARGET_BACKUP}
- Health check: $STATUS
EOF

echo ""
echo "[DONE] Rollback complete"
