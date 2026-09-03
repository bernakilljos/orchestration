#!/usr/bin/env bash
# exec_scheduler plugin — Task Scheduler / cron 등록 wrapper
# Windows: schtasks - Linux: crontab
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

if [ "$#" -lt 2 ]; then
  echo "usage: register-task.sh <task-name> <wrapper-bat-path> [--interval HOUR|DAY|MINUTE] [--every N]"
  exit 2
fi

NAME="$1"
WRAPPER="$2"
INTERVAL="HOURLY"
EVERY="1"

while [ $# -gt 0 ]; do
  case "$1" in
    --interval) INTERVAL="$2"; shift 2 ;;
    --every)    EVERY="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if command -v schtasks >/dev/null 2>&1; then
  # Windows
  schtasks /Create /TN "$NAME" /TR "$WRAPPER" /SC "$INTERVAL" /MO "$EVERY" /F
  echo "[exec_scheduler] Task Scheduler 등록: $NAME"
elif command -v crontab >/dev/null 2>&1; then
  # Linux/Mac
  (crontab -l 2>/dev/null; echo "*/$EVERY * * * * $WRAPPER # $NAME") | crontab -
  echo "[exec_scheduler] cron 등록: $NAME"
else
  echo "[exec_scheduler] schtasks/crontab 없음 — 수동 등록 필요"
  exit 1
fi
