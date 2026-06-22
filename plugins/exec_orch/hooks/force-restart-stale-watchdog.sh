#!/usr/bin/env bash
# force-restart-stale-watchdog.sh — One-shot cleanup for stale (cmd-window) watchdog.
#
# Background: prior versions of watchdog-start.bat used `start /min cmd /c` which
# leaves a minimized cmd window in the taskbar. After upgrading to the silent
# launcher (pythonw + VBS hidden), the existing watchdog process still holds the
# PID file, so watchdog-start.bat keeps skipping (sees PID alive) and the visible
# cmd window persists.
#
# This hook kills any cmd.exe whose command line contains "watchdog.py" plus any
# python.exe running watchdog.py, then re-invokes watchdog-start.bat which will
# launch the new silent version. Runs exactly once per machine (marker file).
#
# Marker: .claude/state/watchdog-silent-migrated.flag

set -uo pipefail

[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
MARK="$PROJECT_DIR/.claude/state/watchdog-silent-migrated.flag"
LOG="$PROJECT_DIR/.claude/logs/watchdog-migration.log"
mkdir -p "$PROJECT_DIR/.claude/state" "$PROJECT_DIR/.claude/logs" 2>/dev/null

[ -f "$MARK" ] && exit 0

TS="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$TS] migrating watchdog to silent mode" >> "$LOG"

# Windows path — kill any cmd.exe / python.exe carrying watchdog.py
if command -v wmic >/dev/null 2>&1 || command -v taskkill >/dev/null 2>&1; then
  # Find by command line via WMIC
  if command -v wmic >/dev/null 2>&1; then
    wmic process where "CommandLine like '%watchdog.py%' and (Name='cmd.exe' or Name='python.exe' or Name='pythonw.exe' or Name='conhost.exe')" call terminate >> "$LOG" 2>&1 || true
  fi
fi

# Remove stale PID file so next invocation actually starts fresh
rm -f "$PROJECT_DIR/.claude/state/watchdog.pid" 2>/dev/null || true

# Re-launch via the new silent batch
WD_BAT="$PROJECT_DIR/.claude/scripts/watchdog-start.bat"
if [ -f "$WD_BAT" ]; then
  # Convert POSIX path -> Windows path if needed
  WIN_BAT="$(echo "$WD_BAT" | sed 's|^/c/|C:/|; s|/|\\|g')"
  # Hidden launch via VBS one-liner so this hook itself doesn't flash a cmd window
  cat > "$PROJECT_DIR/.claude/state/_wd_relaunch.vbs" <<VBS
Set s = CreateObject("WScript.Shell")
s.Run "cmd /c """ & "$WIN_BAT" & """", 0, False
VBS
  if command -v wscript >/dev/null 2>&1; then
    wscript //nologo "$(echo "$PROJECT_DIR/.claude/state/_wd_relaunch.vbs" | sed 's|^/c/|C:/|; s|/|\\|g')" >> "$LOG" 2>&1 || true
  fi
  rm -f "$PROJECT_DIR/.claude/state/_wd_relaunch.vbs" 2>/dev/null || true
fi

touch "$MARK"
echo "[$TS] migration complete" >> "$LOG"
exit 0
