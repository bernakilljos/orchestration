# AGENT-05 — Monitor (Server Status Monitoring)

## Role
Monitors PM2, Nginx, port, disk, and memory status after deployment.
Automatically triggers scripts/rollback.sh and scripts/notify.sh upon anomaly detection.

## Execution Method
```bash
# Health check only (immediately after deployment)
bash .claude/scripts/monitor.sh --health-only

# Single server full inspection
bash .claude/scripts/monitor.sh

# All servers batch inspection
bash .claude/scripts/monitor.sh --all
```

## Monitoring Targets (Based on deploy-config.env)

| Item | Config Key |
|------|---------|
| Server | REMOTE_HOST |
| Port | SERVICE_PORT |
| App Name | PM2_APP_NAME |

Additional servers are registered directly in the `check_server` section of monitor.sh.

## Health Check Auto-Rollback Conditions

```
3 consecutive health check failures
  → scripts/rollback.sh auto-executed
  → scripts/notify.sh "danger" "Health check failed → auto rollback"
```

## Monitoring Items

| Item | Threshold | On Exceeded |
|------|------|---------|
| Health check | HTTP 200/302 | 3 consecutive failures → rollback |
| PM2 status | online | stopped/error → alert |
| PM2 restarts | 5 or fewer | Over 5 → crash warning |
| Disk | 85% or below | Exceeded → alert |
| Memory | 90% or below | Exceeded → alert |

## Automation Integration Flow

```
hook-05-post-deploy
  → Run monitor.sh --health-only
    → Normal: Record completion
    → 3 failures: Auto-execute rollback.sh
                  Send notify.sh "danger" alert
```

## Extension Points
- Schedule regular monitoring with cron
- Auto-cleanup when disk exceeds 90%
- Auto-execute PM2 reload when memory exceeds 95%
