#!/usr/bin/env bash
# prevent-whitespace-png.sh
# PostToolUse hook: warn if PNG has excessive whitespace (≥5% blank edges)
#
# Usage: .claude/settings.json → PostToolUse Write (*.png files)
# Requires: PIL/Pillow (auto-install via verify-image-whitespace.py)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOGFILE="${PROJECT_ROOT}/.claude/logs/prevent-whitespace.log"
VERIFY_SCRIPT="${PROJECT_ROOT}/.claude/scripts/verify-image-whitespace.py"

mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "$LOGFILE"
}

# Parse arguments: file path passed as $1
FILEPATH="$1"
[ -n "$FILEPATH" ] || exit 0

# Only check PNG files
[[ "$FILEPATH" == *.png ]] || exit 0
[ -f "$FILEPATH" ] || exit 0

# Run verify script if exists
if [ -f "$VERIFY_SCRIPT" ]; then
    log "Checking whitespace in $FILEPATH"

    if python "$VERIFY_SCRIPT" "$FILEPATH" 2>&1 | tee -a "$LOGFILE" | grep -q "WARN\|FAIL"; then
        echo "[WARN] PNG has excessive whitespace: $FILEPATH" >&2
        echo "Recommendation: check image layout (padding, banner, content distribution)" >&2
    fi
else
    log "Verify script not found: $VERIFY_SCRIPT"
fi

exit 0
