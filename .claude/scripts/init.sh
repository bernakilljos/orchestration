#!/bin/bash
# =====================================================
# init.sh — Project first-time setup
# Usage: bash .claude/scripts/init.sh [project-path]
# =====================================================
set -e
TARGET="${1:-.}"
cd "$TARGET"

echo ""
echo "=============================="
echo " HOOK-00 Init"
echo "=============================="

# Create required folders
mkdir -p docs/adr docs/deploy-history
mkdir -p .claude/context-cache .claude/tasks .claude/learning
echo "[OK] Folders created"

# Frontend stack detection
FE_STACK="Unknown"
if [ -f package.json ]; then
  if grep -q '"vue": "^2' package.json 2>/dev/null; then FE_STACK="Vue2"
  elif grep -q '"vue": "^3' package.json 2>/dev/null; then FE_STACK="Vue3"
  elif grep -q '"react"' package.json 2>/dev/null; then FE_STACK="React"
  elif grep -q '"next"' package.json 2>/dev/null; then FE_STACK="Next.js"
  fi
fi

# Backend stack detection
BE_STACK="Unknown"
if [ -f pom.xml ]; then BE_STACK="Spring Boot"
elif [ -f build.gradle ]; then BE_STACK="Spring Boot (Gradle)"
elif [ -f package.json ] && grep -q '"express"' package.json 2>/dev/null; then BE_STACK="Node Express"
elif [ -f requirements.txt ] || [ -f pyproject.toml ]; then BE_STACK="Python"
fi

# DB stack detection
DB_STACK="Unknown"
if grep -rql "sqlserver\|mssql" . --include="*.properties" --include="*.yml" --include="*.env" 2>/dev/null; then DB_STACK="MSSQL"
elif grep -rql "mysql" . --include="*.properties" --include="*.yml" --include="*.env" 2>/dev/null; then DB_STACK="MySQL"
elif grep -rql "oracle" . --include="*.properties" --include="*.yml" 2>/dev/null; then DB_STACK="Oracle"
elif grep -rql "postgresql" . --include="*.properties" --include="*.yml" 2>/dev/null; then DB_STACK="PostgreSQL"
fi

echo "[OK] Stack detected: FE=$FE_STACK / BE=$BE_STACK / DB=$DB_STACK"

# Save stack to task-memory.json
python3 - <<PYEOF
import json
with open('.claude/tasks/task-memory.json') as f:
    memory = json.load(f)
memory['project_stack'] = {
    'frontend': '${FE_STACK}',
    'backend': '${BE_STACK}',
    'database': '${DB_STACK}'
}
with open('.claude/tasks/task-memory.json', 'w') as f:
    json.dump(memory, f, indent=2, ensure_ascii=False)
PYEOF

# Generate file list
find . -type f \( -name "*.vue" -o -name "*.java" -o -name "*.js" -o -name "*.ts" -o -name "*.py" \) \
  | grep -v node_modules | grep -v .git | grep -v dist | grep -v target \
  | sort > docs/file-list.txt
echo "[OK] File list generated: $(wc -l < docs/file-list.txt) files"

# List large files (500+ lines)
find . -type f \( -name "*.vue" -o -name "*.java" -o -name "*.js" \) \
  | grep -v node_modules | grep -v .git \
  | while read f; do
    lines=$(wc -l < "$f" 2>/dev/null || echo 0)
    [ "$lines" -gt 500 ] && echo "$lines $f"
  done | sort -rn | head -20 > docs/large-files.txt
echo "[OK] Large files: $(wc -l < docs/large-files.txt) files"

# Copy deploy-config.env from example if missing
if [ ! -f .claude/deploy-config.env ]; then
  cp .claude/deploy-config.env.example .claude/deploy-config.env
  echo "[OK] deploy-config.env created -> Edit server info before deploy"
else
  echo "[OK] deploy-config.env already exists"
fi

# Generate project-structure.md
cat > docs/project-structure.md <<EOF
# Project Structure
## Stack
- Frontend: ${FE_STACK}
- Backend:  ${BE_STACK}
- Database: ${DB_STACK}
## File Count
$(wc -l < docs/file-list.txt) files
## Large Files (500+ lines)
$(cat docs/large-files.txt || echo "None")
## Analysis Time
$(date '+%Y-%m-%d %H:%M:%S')
EOF

# CLI check
echo ""
echo "=== CLI Environment ==="
command -v claude  >/dev/null && echo "[OK] claude" || echo "[X]  claude  -> https://docs.anthropic.com/claude-code"
command -v codex   >/dev/null && echo "[OK] codex"  || echo "[X]  codex   -> npm install -g @openai/codex"
command -v gemini  >/dev/null && echo "[OK] gemini" || echo "[X]  gemini  -> npm install -g @google/gemini-cli"
command -v git     >/dev/null && echo "[OK] git"    || echo "[X]  git     -> https://git-scm.com"

echo ""
echo "[DONE] Init complete -> See docs/project-structure.md"
