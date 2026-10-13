#!/usr/bin/env bash
# prevent-version-suffix.sh
# Pre-commit hook: block files with -v2, -v3, _final, _new, _alt suffixes
#
# Pattern: filename ends with -v\d+, _final, _new, _alt (before extension)
# Rationale: .bak backup + overwrite original (feedback_no_version_suffix.md)
#
# Usage: .claude/settings.json → PreToolUse Edit/Write
# Exception: User explicitly set ALLOW_VERSION_SUFFIX=1

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOGFILE="${PROJECT_ROOT}/.claude/logs/prevent-version-suffix.log"
ALLOW="${ALLOW_VERSION_SUFFIX:-0}"

mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "$LOGFILE"
}

# Parse arguments: file path passed as $1
FILEPATH="$1"
[ -n "$FILEPATH" ] || exit 0

FILENAME=$(basename "$FILEPATH")

# Check for version suffix patterns (before extension)
# E.g., report-v2.docx, doc_final.md, config_new.json
if [[ "$FILENAME" =~ -v[0-9]+\. ]] || [[ "$FILENAME" =~ _(v[0-9]+|final|new|alt)\. ]]; then
    log "BLOCKED: Version suffix detected in $FILEPATH"

    if [ "$ALLOW" = "1" ]; then
        log "ALLOW_VERSION_SUFFIX=1 — proceeding"
        exit 0
    fi

    echo "[ERROR] File has version suffix (violates feedback_no_version_suffix.md):" >&2
    echo "  File: $FILENAME" >&2
    echo "  Solution: use original name + .bak backup" >&2
    echo "  To override: export ALLOW_VERSION_SUFFIX=1" >&2
    exit 1
fi

log "OK: No version suffix in $FILENAME"
exit 0
