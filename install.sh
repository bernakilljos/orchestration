#!/bin/bash
# =====================================================
# install.sh — Orchestration Kit one-click install (Linux/Mac)
# Usage: bash install.sh [project-path]
# Example: bash install.sh /home/ec2-user/rms
#          bash install.sh .
# =====================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-.}"

echo ""
echo "=============================="
echo " Orchestration Kit Install"
echo "=============================="
echo " Install path: $TARGET"
echo "=============================="

# Check folder exists
if [ ! -d "$TARGET" ]; then
  echo "Error: Folder not found → $TARGET"
  exit 1
fi

# Backup existing .claude
if [ -d "$TARGET/.claude" ]; then
  BACKUP_NAME=".claude_backup_$(date '+%Y%m%d_%H%M%S')"
  echo "[1/5] Backing up existing .claude → $BACKUP_NAME"
  cp -r "$TARGET/.claude" "$TARGET/$BACKUP_NAME"
else
  echo "[1/5] No existing .claude → Fresh install"
fi

# Copy .claude
echo "[2/5] Installing .claude folder..."
cp -r "$SCRIPT_DIR/.claude" "$TARGET/"
cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET/CLAUDE.md"
echo "      Done"

# docs folder
echo "[3/5] Creating docs folders..."
mkdir -p "$TARGET/docs/adr"
mkdir -p "$TARGET/docs/deploy-history"
echo "      Done"

# deploy-config.env
echo "[4/5] Checking deploy config..."
if [ ! -f "$TARGET/.claude/deploy-config.env" ]; then
  cp "$TARGET/.claude/deploy-config.env.example" "$TARGET/.claude/deploy-config.env"
  echo "      deploy-config.env created → Edit server info before deploy"
else
  echo "      deploy-config.env already exists → Kept"
fi

# .gitignore
echo "[5/5] Updating .gitignore..."
GITIGNORE="$TARGET/.gitignore"
touch "$GITIGNORE"
for entry in \
  ".claude/deploy-config.env" \
  ".claude/context-cache/" \
  "docs/secret-scan.txt" \
  "docs/security-report.txt" \
  "docs/lint-result.txt" \
  "docs/build-result.txt" \
  "docs/test-result.txt" \
  "docs/changed-files.txt"; do
  grep -qF "$entry" "$GITIGNORE" || echo "$entry" >> "$GITIGNORE"
done
echo "      Done"

# Copy setup guide
if [ -f "$SCRIPT_DIR/docs/CLAUDE_SETUP_GUIDE.md" ]; then
  cp "$SCRIPT_DIR/docs/CLAUDE_SETUP_GUIDE.md" "$TARGET/docs/CLAUDE_SETUP_GUIDE.md"
  echo "      CLAUDE_SETUP_GUIDE.md -> docs/"
fi

# Copy docs/screens template (R51 — single-image workflow)
if [ -d "$SCRIPT_DIR/docs/screens/our-html" ]; then
  mkdir -p "$TARGET/docs/screens/our-html" "$TARGET/docs/screens/our-arch" "$TARGET/docs/screens/our-func"
  cp "$SCRIPT_DIR/docs/screens/our-html/_styles.css" "$TARGET/docs/screens/our-html/" 2>/dev/null || true
  echo "      docs/screens/ template ready (single-image workflow)"
fi

# Script execution permissions
chmod +x "$TARGET/.claude/scripts/"*.sh 2>/dev/null || true

# Configure claude global settings
echo ""
echo "=============================="
echo " Claude Global Settings"
echo "=============================="
CLAUDE_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_DIR"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import json, os
f = '$SETTINGS_FILE'
j = json.load(open(f)) if os.path.exists(f) else {}
j.setdefault('permissions', {})
j['permissions']['defaultMode'] = 'bypassPermissions'
j['skipDangerousModePermissionPrompt'] = True
j['autoUpdatesChannel'] = 'latest'
json.dump(j, open(f, 'w'), indent=2)
" && echo "[OK] settings.json configured" || echo "[WARN] Failed to configure settings.json"
else
  echo "[WARN] python3 not found - configure ~/.claude/settings.json manually (see docs/CLAUDE_SETUP_GUIDE.md)"
fi

# Check API keys
echo ""
echo "=============================="
echo " API Key Check"
echo "=============================="
[ -n "$ANTHROPIC_API_KEY" ] && echo "[OK] ANTHROPIC_API_KEY" || echo "[WARN] ANTHROPIC_API_KEY not set"
[ -n "$OPENAI_API_KEY" ]    && echo "[OK] OPENAI_API_KEY"    || echo "[WARN] OPENAI_API_KEY not set"
[ -n "$GEMINI_API_KEY" ]    && echo "[OK] GEMINI_API_KEY"    || echo "[WARN] GEMINI_API_KEY not set"

# CLI check
echo ""
echo "=============================="
echo " CLI Environment Check"
echo "=============================="
command -v claude  >/dev/null && echo "[OK] claude" || echo "[X]  claude  → https://docs.anthropic.com/claude-code"
command -v codex   >/dev/null && echo "[OK] codex"  || echo "[X]  codex   → npm install -g @openai/codex"
command -v gemini  >/dev/null && echo "[OK] gemini" || echo "[X]  gemini  → npm install -g @google/gemini-cli"
command -v git     >/dev/null && echo "[OK] git"    || echo "[X]  git     → https://git-scm.com"
command -v python3 >/dev/null && echo "[OK] python3 (PPT/PDF/screens 렌더링용)" || echo "[X]  python3 → 필수 (Playwright + python-pptx)"

# R51 Design tools check
echo ""
echo "=============================="
echo " Design Tools (R51)"
echo "=============================="
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import playwright" 2>/dev/null && echo "[OK] playwright (HTML→PPT/PDF/PNG)" || echo "[X]  playwright → pip install playwright && playwright install chromium"
  python3 -c "import pptx"       2>/dev/null && echo "[OK] python-pptx (PPT 조립)"        || echo "[X]  python-pptx → pip install python-pptx"
  python3 -c "import PIL"        2>/dev/null && echo "[OK] Pillow (overflow 검증)"         || echo "[X]  Pillow → pip install Pillow"
fi
echo "  /design_ppt   PPT 자동 (HTML→PPTX)"
echo "  /pdf-generate PDF 자동 (A4/Digital)"
echo "  render-screens.py  단일 PNG (docs/screens/our-html → our-arch/, our-func/)"

# Run init
echo ""
echo "=============================="
echo " Project Init"
echo "=============================="
bash "$TARGET/.claude/scripts/init.sh" "$TARGET"

# Start Claude
echo ""
echo "=============================="
echo " Starting Claude"
echo "=============================="
cd "$TARGET"
exec claude --dangerously-skip-permissions
