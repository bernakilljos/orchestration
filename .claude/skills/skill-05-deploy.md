# SKILL-05 — Deploy (Deployment Automation)

## Purpose
Automatically deploy to EC2 environment after implementation and verification are complete.

## Environment Definition

```bash
# Load from .env or config (no hardcoding)
source .claude/deploy-config.env

# deploy-config.env example (file not committed to Git)
# TARGET_ENV=dev|stg|prod
# REMOTE_HOST=your-server.example.com
# REMOTE_USER=ec2-user
# APP_PATH=/home/ec2-user/app
# PM2_APP_NAME=my-app
# BUILD_CMD=npm run build
# SERVICE_PORT=6060
```

## Deployment Flow

```
Build verification passed
  → [HOOK-04] pre-deploy: final check before deployment
  → Execute build (frontend)
  → Transfer files via rsync or scp
  → Restart server via SSH (PM2)
  → Health check
  → [HOOK-05] post-deploy: record deployment results
```

## Frontend Deployment (Node.js 빌드 — Vue/React/Svelte 등)

```bash
#!/bin/bash
set -e
source .claude/deploy-config.env

echo "=== Build Start ==="
npm run build

echo "=== File Transfer ==="
rsync -avz --delete dist/ \
  ${REMOTE_USER}@${REMOTE_HOST}:${APP_PATH}/dist/

echo "=== Nginx Restart ==="
ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo nginx -t && sudo systemctl reload nginx"

echo "=== Health Check ==="
sleep 3
curl -f http://${REMOTE_HOST}:${SERVICE_PORT} \
  && echo "Deployment successful" \
  || echo "Health check failed"
```

## Backend Deployment (Spring Boot)

```bash
#!/bin/bash
set -e
source .claude/deploy-config.env

echo "=== Build ==="
./mvnw clean package -DskipTests

echo "=== File Transfer ==="
scp target/*.jar \
  ${REMOTE_USER}@${REMOTE_HOST}:${APP_PATH}/

echo "=== Service Restart (PM2) ==="
ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "pm2 restart ${PM2_APP_NAME} || pm2 start ${APP_PATH}/*.jar --name ${PM2_APP_NAME}"

echo "=== Health Check ==="
sleep 5
curl -f http://${REMOTE_HOST}:${SERVICE_PORT}/actuator/health \
  && echo "Backend deployment successful" \
  || echo "Health check failed"
```

## Jenkins Integration (CI/CD)

```bash
# Trigger Jenkins pipeline
ssh ${REMOTE_USER}@${JENKINS_HOST} \
  "curl -X POST http://localhost:8080/job/${JOB_NAME}/build \
   --user ${JENKINS_USER}:${JENKINS_TOKEN}"

# Wait for build result
sleep 10
curl -s http://${JENKINS_HOST}:8080/job/${JOB_NAME}/lastBuild/api/json \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['result'])"
```

## Rollback

```bash
#!/bin/bash
source .claude/deploy-config.env

echo "=== Rollback Execution ==="
ssh ${REMOTE_USER}@${REMOTE_HOST} \
  "pm2 stop ${PM2_APP_NAME} && \
   cp ${APP_PATH}/backup/*.jar ${APP_PATH}/ && \
   pm2 restart ${PM2_APP_NAME}"
```

## Extension Points
- Environment branching: demo / upg / prod
- Slack/Teams notification integration
- Auto-record deployment history in docs/deploy-history.md
