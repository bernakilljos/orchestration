#!/usr/bin/env bash
# score_task.sh — bash wrapper for score_task.py
# Usage: score_task.sh [--auto | <task-file> <result-file>]

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$PROJECT_ROOT/plugins/eval_quality/scripts/score_task.py"

if [ ! -f "$SCRIPT" ]; then
  echo "[score_task] missing: $SCRIPT" >&2
  exit 2
fi

case "${1:-}" in
  --auto)
    python "$SCRIPT" --auto
    ;;
  "")
    echo "Usage: $0 [--auto | <task-file> <result-file>]" >&2
    exit 64
    ;;
  *)
    if [ "$#" -lt 2 ]; then
      echo "Usage: $0 <task-file> <result-file>" >&2
      exit 64
    fi
    python "$SCRIPT" --task "$1" --result "$2"
    ;;
esac
