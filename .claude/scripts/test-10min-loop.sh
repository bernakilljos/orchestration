#!/usr/bin/env bash
# Test orca-10min-loop.py in dry-run mode

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT_PATH="$PROJECT_ROOT/.claude/scripts/orca-10min-loop.py"
LOG_FILE="$PROJECT_ROOT/.claude/logs/test-10min-loop.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "[TEST] Starting orca-10min-loop.py in dry-run mode..."
echo "[TEST] Script: $SCRIPT_PATH"
echo "[TEST] Log: $LOG_FILE"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[ERROR] Script not found: $SCRIPT_PATH"
    exit 1
fi

# Run with dry-run
PY=$(cat "$PROJECT_ROOT/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n') || PY=python
"${PY:-python}" "$SCRIPT_PATH" --dry-run 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "[✓] Test PASSED - dry-run completed successfully"
    tail -5 "$LOG_FILE"
    exit 0
else
    echo ""
    echo "[✗] Test FAILED - see logs above"
    exit 1
fi
