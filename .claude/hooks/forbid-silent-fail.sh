#!/usr/bin/env bash
# forbid-silent-fail.sh
# Pre-commit hook: block commits containing silent fail patterns (except...pass)
#
# Pattern: except[^:]*:\s*pass (bare pass in except block = swallows errors)
#
# Usage: .claude/settings.json → PreToolUse hook
# Trigger: File edit/write to *.py, *.sh (pre-commit)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PATTERN='except[^:]*:\s*pass'
LOGFILE="${PROJECT_ROOT}/.claude/logs/forbid-silent-fail.log"

# Ensure log dir
mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

# Skip if not in git repo or .claude/hooks/ doesn't exist
[ -d "${PROJECT_ROOT}/.git" ] || exit 0
[ -d "${PROJECT_ROOT}/.claude" ] || exit 0

log "=== Forbid Silent Fail Audit (pre-commit) ==="

# Scan staged files in git
STAGED_FILES=$(git -C "$PROJECT_ROOT" diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")

if [ -z "$STAGED_FILES" ]; then
    log "No staged files to check"
    exit 0
fi

VIOLATIONS=0
VIOLATION_LIST=""

while IFS= read -r file; do
    # Skip non-Python/Shell files
    case "$file" in
        *.py|*.sh) ;;
        *) continue ;;
    esac

    filepath="${PROJECT_ROOT}/${file}"
    [ -f "$filepath" ] || continue

    # Check for pattern in staged content
    if git -C "$PROJECT_ROOT" show ":0:${file}" 2>/dev/null | grep -En "$PATTERN" > /tmp/silent_fail_check.tmp 2>&1; then
        while IFS= read -r match_line; do
            log "VIOLATION: $file — $match_line"
            VIOLATION_LIST="${VIOLATION_LIST}$file:${match_line}\n"
            ((VIOLATIONS++))
        done < /tmp/silent_fail_check.tmp
    fi
done <<< "$STAGED_FILES"

rm -f /tmp/silent_fail_check.tmp

if [ $VIOLATIONS -gt 0 ]; then
    log "BLOCKED: $VIOLATIONS silent fail pattern(s) detected"
    log "Fix: replace 'except...: pass' with exception handling or re-raise"
    printf "\n%b\n" "$VIOLATION_LIST" >&2
    exit 1
fi

log "OK: No silent fail patterns"
exit 0
