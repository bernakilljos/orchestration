# SKILL-07 — Rollback (Automatic Rollback)

## Purpose
Automatically restore to the previous version when deployment fails or health check fails.
Rollback is the only operation that can be automatically executed without Team Lead approval.

## Execution Method
```bash
# Auto-rollback to the most recent backup
bash .claude/scripts/rollback.sh

# Rollback to a specific backup version
bash .claude/scripts/rollback.sh dist_20260330_143000
```

## Auto-Trigger Conditions

| Condition | Auto-Execution |
|-----------|---------------|
| 3 consecutive health check failures | Auto-execute |
| Build failure | Auto-execute |
| Secret exposure detected | Immediately auto-execute |
| PM2 crash loop | Auto-execute |
| Team Lead manual instruction | Execute immediately |

## Rollback Flow

```
rollback.sh execution
  → [1] Check current service status
  → [2] Check backup list
  → [3] Emergency backup of current version (preserve before rollback)
  → [4] Restore previous version + Nginx reload or PM2 restart
  → [5] Verify health check
  → [6] Send notify.sh "warning" notification
  → [7] Record history in deploy-history/history.md
```

## Backup Retention Policy

```
Create backup per deployment: dist_YYYYMMDD_HHMMSS
Retain maximum 5 (auto-delete oldest)
Current version also preserved as emergency backup before rollback
```

## Git Code Rollback

```bash
# Revert last commit
git revert HEAD --no-edit
git push origin develop
```

## Secret Exposure Emergency Handling

```bash
# 1. Immediately remove the file from Git
git rm --cached [exposed-file]
git commit -m "security: remove secret exposure file"

# 2. Immediately rollback the deployed version as well
bash .claude/scripts/rollback.sh
```

## Extension Points
- Linked with agent-05-monitor: auto-trigger on health check failure
- Linked with hook-06-notify: immediate notification on rollback occurrence
- On rollback failure → notify.sh "danger" request manual inspection
