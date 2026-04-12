#!/bin/bash
# =====================================================
# deploy.sh — EC2 automated deployment
# Usage: bash .claude/scripts/deploy.sh [--env demo|upg|prod] [--confirmed]
# =====================================================
set -e
source .claude/deploy-config.env

CONFIRMED=false
ENV_OVERRIDE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV_OVERRIDE="$2"; shift 2 ;;
    --confirmed) CONFIRMED=true; shift ;;
    *) shift ;;
  esac
done

[ -n "$ENV_OVERRIDE" ] && TARGET_ENV="$ENV_OVERRIDE"

echo ""
echo "=============================="
echo " SKILL-05 Deploy"
echo " Env   : $TARGET_ENV"
echo " Server: $REMOTE_HOST"
echo "=============================="

# Protect prod environment
if [ "$TARGET_ENV" = "prod" ] && [ "$CONFIRMED" != "true" ]; then
  echo "[BLOCK] PROD environment → --confirmed flag required"
  echo "  → bash .claude/scripts/deploy.sh --env prod --confirmed"
  exit 1
fi

# Run quality gate first
echo "[1/6] Quality gate check..."
bash .claude/scripts/quality-gate.sh || {
  echo "[BLOCK] Quality gate failed → Deploy aborted"
  bash .claude/scripts/notify.sh "danger" "Deploy blocked: Quality gate failed ($TARGET_ENV)"
  exit 1
}

# Verify server connectivity
echo "[2/6] Checking server connectivity..."
ssh -o ConnectTimeout=10 ${REMOTE_USER}@${REMOTE_HOST} "echo OK" || {
  echo "[BLOCK] Server connection failed: $REMOTE_HOST"
  exit 1
}

# Create backup
echo "[3/6] Backing up current version..."
BACKUP_NAME="backup_$(date '+%Y%m%d_%H%M%S')"
ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "mkdir -p ${APP_PATH}/backup && \
   [ -d ${APP_PATH}/dist ] && cp -r ${APP_PATH}/dist ${APP_PATH}/backup/dist_${BACKUP_NAME} 2>/dev/null || true && \
   ls -t ${APP_PATH}/backup/ | tail -n +6 | xargs -I{} rm -rf ${APP_PATH}/backup/{} 2>/dev/null || true && \
   echo 'Backup complete: dist_${BACKUP_NAME}'"

# Build
echo "[4/6] Running build..."
if [ -f package.json ]; then
  eval "$BUILD_CMD" 2>&1 | tail -10
elif [ -f pom.xml ]; then
  ./mvnw clean package -DskipTests -q
fi

# File transfer
echo "[5/6] Transferring files..."
if [ -d dist ]; then
  rsync -avz --delete dist/ ${REMOTE_USER}@${REMOTE_HOST}:${APP_PATH}/dist/ \
    --exclude='.git' 2>&1 | tail -5
  ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo nginx -t && sudo systemctl reload nginx"
elif ls target/*.jar 2>/dev/null | head -1 | grep -q jar; then
  JAR=$(ls target/*.jar | grep -v sources | head -1)
  ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${APP_PATH}/backup && \
    mv ${APP_PATH}/*.jar ${APP_PATH}/backup/${BACKUP_NAME}.jar 2>/dev/null || true"
  scp "$JAR" ${REMOTE_USER}@${REMOTE_HOST}:${APP_PATH}/
  ssh ${REMOTE_USER}@${REMOTE_HOST} \
    "pm2 restart ${PM2_APP_NAME} 2>/dev/null || \
     pm2 start ${APP_PATH}/*.jar --name ${PM2_APP_NAME}"
fi

# Health check
echo "[6/6] Health check..."
bash .claude/scripts/monitor.sh --health-only || {
  echo "[FAIL] Health check failed → Running auto rollback"
  bash .claude/scripts/rollback.sh
  bash .claude/scripts/notify.sh "danger" "Deploy failed → Auto rollback executed ($TARGET_ENV / $REMOTE_HOST)"
  exit 1
}

# Record deploy history
cat >> docs/deploy-history/history.md <<EOF

## Deploy Success — $(date '+%Y-%m-%d %H:%M:%S')
- Env   : ${TARGET_ENV}
- Server: ${REMOTE_HOST}:${SERVICE_PORT}
- Build : $(ls dist/ 2>/dev/null | wc -l || echo 0) files
EOF

# Completion notification
bash .claude/scripts/notify.sh "good" "Deploy success ($TARGET_ENV) → http://${REMOTE_HOST}:${SERVICE_PORT}"

echo ""
echo "[DONE] Deploy success: http://${REMOTE_HOST}:${SERVICE_PORT}"
