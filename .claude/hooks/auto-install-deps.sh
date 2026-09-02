#!/usr/bin/env bash
# [차단] 킬스위치 - 파일 있으면 아무것도 안 하고 종료
if [ -f "$HOME/.claude/NO-SCHTASKS" ]; then exit 0; fi
# auto-install-deps.sh — Zero-touch dependency installation.
# Runs at SessionStart. Detects missing tools (playwright python, core MCP servers)
# and installs them in the background. NEVER prompts the user.
#
# Idempotent: each item checked individually; only installs what's missing.
# All work logged to .claude/logs/auto-install-deps.log
#
# Aligns with CLAUDE.md § Zero-touch automation: alerts only for the 5 critical
# categories; package installs are routine and proceed silently.

set -uo pipefail

# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG="$PROJECT_DIR/.claude/logs/auto-install-deps.log"
mkdir -p "$PROJECT_DIR/.claude/logs" 2>/dev/null
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# Throttle: don't re-run within 1 hour
MARK="$PROJECT_DIR/.claude/state/auto-install-deps.last"
if [ -f "$MARK" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$MARK" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 3600 ] && exit 0
fi
mkdir -p "$PROJECT_DIR/.claude/state" 2>/dev/null
date +%s > "$MARK"

# ---- 1) Playwright Python package + Chromium browser ----
PYBIN=""
for cand in python python3 py; do
  if command -v "$cand" >/dev/null 2>&1; then
    PYBIN="$cand"; break
  fi
done

if [ -n "$PYBIN" ]; then
  if ! "$PYBIN" -c "import playwright" >/dev/null 2>&1; then
    echo "[$TS] pip install playwright pillow PyMuPDF python-docx" >> "$LOG"
    nohup "$PYBIN" -m pip install --quiet --user playwright pillow PyMuPDF python-docx \
      >> "$LOG" 2>&1 &
    disown 2>/dev/null || true
  fi
  # Chromium driver — only if playwright imports successfully
  if "$PYBIN" -c "import playwright" >/dev/null 2>&1; then
    if ! "$PYBIN" -c "import playwright; from pathlib import Path; import sys; sys.exit(0 if any(Path(p).rglob('chrome.exe') or Path(p).rglob('chrome') for p in [str(Path.home() / 'AppData/Local/ms-playwright'), '/opt/ms-playwright', str(Path.home() / '.cache/ms-playwright')] if Path(p).exists()) else 1)" 2>/dev/null; then
      echo "[$TS] playwright install chromium" >> "$LOG"
      nohup "$PYBIN" -m playwright install chromium >> "$LOG" 2>&1 &
      disown 2>/dev/null || true
    fi
  fi
fi

# ---- 2) Core MCP servers (claude CLI required) ----
if command -v claude >/dev/null 2>&1; then
  MCP_LIST="$(claude mcp list 2>&1 || echo '')"

  # name : install command (cmd /c npx for Windows shell-cross-compat)
  CORE_MCP=(
    "playwright|claude mcp add playwright -s user -- cmd /c npx -y @playwright/mcp"
    "sequential-thinking|claude mcp add sequential-thinking -s user -- cmd /c npx -y @modelcontextprotocol/server-sequential-thinking"
    "fetch|claude mcp add fetch -s user -- cmd /c npx -y @modelcontextprotocol/server-fetch"
    "context7|claude mcp add context7 -s user -- cmd /c npx -y @upstash/context7-mcp"
  )

  for entry in "${CORE_MCP[@]}"; do
    NAME="${entry%%|*}"
    CMD="${entry#*|}"
    if echo "$MCP_LIST" | grep -qE "^${NAME}[[:space:]]"; then
      continue
    fi
    echo "[$TS] installing MCP: $NAME" >> "$LOG"
    nohup bash -c "$CMD" >> "$LOG" 2>&1 &
    disown 2>/dev/null || true
  done
fi

exit 0
