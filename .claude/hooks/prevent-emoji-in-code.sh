#!/usr/bin/env bash
# prevent-emoji-in-code.sh
# Pre-commit hook: warn/block emojis in code files (.md, .py, .sh, .json, .yaml)
#
# Emoji range: U+1F300~U+1F9FF (Miscellaneous Symbols and Pictographs + Emoticons + etc.)
#
# Usage: .claude/settings.json → PreToolUse Write/Edit
# Mode: WARN by default (log to stderr), BLOCK if ENFORCE_EMOJI_BAN=1

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOGFILE="${PROJECT_ROOT}/.claude/logs/prevent-emoji.log"
ENFORCE="${ENFORCE_EMOJI_BAN:-0}"

mkdir -p "$(dirname "$LOGFILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "$LOGFILE"
}

# Parse arguments: file path passed as $1
FILEPATH="$1"
[ -n "$FILEPATH" ] || exit 0

# Skip non-code files
case "$FILEPATH" in
    *.md|*.py|*.sh|*.json|*.yaml|*.yml|*.toml|*.xml) ;;
    *) exit 0 ;;
esac

[ -f "$FILEPATH" ] || exit 0

# Check for emoji (simplified: look for common emoji byte patterns)
# UTF-8 emoji typically: F0 9F XX XX (4-byte sequences)
if grep -P '\x{1F3}..|\x{1F4}..|\x{1F5}..|\x{1F6}..|\x{1F7}..|\x{1F8}..|\x{1F9}..' "$FILEPATH" > /dev/null 2>&1; then
    EMOJI_LINES=$(grep -Pn '\x{1F3}..|\x{1F4}..|\x{1F5}..|\x{1F6}..|\x{1F7}..|\x{1F8}..|\x{1F9}..' "$FILEPATH" 2>/dev/null || true)

    if [ -n "$EMOJI_LINES" ]; then
        log "WARN: Emoji detected in $FILEPATH"
        log "$EMOJI_LINES"

        if [ "$ENFORCE" = "1" ]; then
            echo "[WARN] Emoji in code file (ENFORCE mode): $FILEPATH" >&2
            echo "$EMOJI_LINES" >&2
            exit 1
        else
            echo "[WARN] Emoji detected in: $FILEPATH (set ENFORCE_EMOJI_BAN=1 to block)" >&2
            echo "$EMOJI_LINES" >&2
        fi
    fi
fi

exit 0
