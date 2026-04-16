# HOOK-06 — Notify (Slack/Teams notification)

## Purpose
Send immediate notification to Slack or Teams on deploy, failure, rollback, or anomaly.

## Usage (Windows)
```bat
rem Basic usage
.claude\scripts\notify.bat good    "Deploy success"
.claude\scripts\notify.bat warning "Auto rollback executed"
.claude\scripts\notify.bat danger  "Secret exposed - immediate check required"
```

## Color Codes

| Color | Meaning | Slack Color |
|-------|---------|-------------|
| good | Success/Normal | Green |
| warning | Warning/Caution | Yellow |
| danger | Failure/Emergency | Red |

## Configuration

In `.claude\deploy-config.env`:

```
NOTIFY_TYPE=slack           # slack | teams | both | none
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/XXX
NOTIFY_MENTION=@username    # mention on emergency
```

## Auto-call by situation

| Situation | Called from | Color |
|-----------|-------------|-------|
| Deploy success | deploy.bat | good |
| Deploy failure | deploy.bat | danger |
| Auto rollback | rollback.bat | warning |
| Health check fail | monitor.bat | danger |
| Secret exposed | quality-gate.bat | danger |
| Task complete | hook-03-post-review | good |

## Disable notifications

```
NOTIFY_TYPE=none   (in deploy-config.env)
```

## Extension Points
- Add KakaoWork, Jandi, Naver Works webhooks (modify notify.bat)
- Filter by notification level
- Daily deploy summary (schedule with Windows Task Scheduler)
