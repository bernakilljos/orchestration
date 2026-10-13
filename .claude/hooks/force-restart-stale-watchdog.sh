#!/usr/bin/env bash
# [차단] 킬스위치 — 파일 있으면 아무것도 안 하고 종료
if [ -f "$HOME/.claude/NO-SCHTASKS" ]; then exit 0; fi
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

# Kill stale watchdog processes via PowerShell (UTF-8 native, no mojibake).
# Matches cmd.exe / python.exe / pythonw.exe / conhost.exe whose command line
# contains "watchdog.py".
if command -v powershell >/dev/null 2>&1; then
  # Only kill cmd.exe / python.exe (console variants) carrying watchdog.py.
  # pythonw.exe (silent variant) is what WE spawn — never touch it.
  # Skip the current PID file's process too (defence-in-depth).
  CURRENT_PID="$(cat "$PROJECT_DIR/.claude/state/watchdog.pid" 2>/dev/null | tr -d '\r\n ' || echo 0)"
  KILLED="$(powershell -NoProfile -NonInteractive -Command "
    \$skip = [int]'${CURRENT_PID:-0}'
    \$out = New-Object System.Collections.ArrayList
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
      \$_.CommandLine -and \$_.CommandLine -match 'watchdog\.py' -and
      \$_.Name -in @('cmd.exe','python.exe','conhost.exe') -and
      \$_.ProcessId -ne \$skip
    } | ForEach-Object {
      try {
        Stop-Process -Id \$_.ProcessId -Force -ErrorAction Stop
        [void]\$out.Add(\"PID=\$(\$_.ProcessId) NAME=\$(\$_.Name)\")
      } catch {}
    }
    if (\$out.Count -eq 0) { 'no stale watchdog process found (pythonw silent OK)' } else { \$out -join '; ' }
  " 2>/dev/null | tr -d '\r')"
  echo "[$TS] kill scan: $KILLED" >> "$LOG"
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
