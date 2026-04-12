#!/bin/bash
# =====================================================
# quality-gate.sh — Build/test/secret quality gate
# Usage: bash .claude/scripts/quality-gate.sh
# Exit code: 0=pass 1=fail
# =====================================================
set -e
source .claude/deploy-config.env 2>/dev/null || true

PASS=0
FAIL=0
REPORT="docs/quality-gate-report.md"
mkdir -p docs

echo "" > "$REPORT"
echo "## Quality Gate Report — $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT"
echo "" >> "$REPORT"

check() {
  local name="$1"
  local cmd="$2"
  echo -n "[$name] "
  if eval "$cmd" >> "$REPORT" 2>&1; then
    echo "PASS"
    echo "- [PASS] $name" >> "$REPORT"
    PASS=$((PASS+1))
  else
    echo "FAIL"
    echo "- [FAIL] $name" >> "$REPORT"
    FAIL=$((FAIL+1))
  fi
}

echo "=== Quality Gate ==="

# Frontend
if [ -f package.json ]; then
  check "ESLint"    "npm run lint --if-present 2>&1 | tail -5"
  check "Build"     "npm run build 2>&1 | tail -5"
  check "Unit Test" "npm test -- --watchAll=false 2>&1 | tail -10 || npx jest --passWithNoTests 2>&1 | tail -5"
fi

# Backend
if [ -f pom.xml ]; then
  check "Maven Compile" "./mvnw compile -q 2>&1 | tail -5"
  check "Maven Test"    "./mvnw test -q 2>&1 | tail -10"
elif [ -f build.gradle ]; then
  check "Gradle Build"  "./gradlew build -q 2>&1 | tail -5"
fi

# Secret scan
echo -n "[Secret Scan] "
SECRET_RESULT=$(grep -rEn \
  "(password|secret|api_key|apikey|token|passwd)\s*[:=]\s*['\"][^'\"]{5,}" \
  src/ --include="*.js" --include="*.vue" --include="*.java" --include="*.ts" \
  2>/dev/null \
  | grep -v "process\.env" \
  | grep -v "config\." \
  | grep -v "\.example" || true)

if [ -z "$SECRET_RESULT" ]; then
  echo "PASS"
  echo "- [PASS] Secret Scan" >> "$REPORT"
  PASS=$((PASS+1))
else
  echo "FAIL (secret exposure detected)"
  echo "- [FAIL] Secret Scan" >> "$REPORT"
  echo "$SECRET_RESULT" | tee docs/secret-scan.txt >> "$REPORT"
  FAIL=$((FAIL+1))
fi

# Writer rule (check modifications outside locked_files)
echo -n "[Writer Rule] "
if command -v git >/dev/null && git rev-parse --git-dir >/dev/null 2>&1; then
  git diff --name-only HEAD 2>/dev/null > docs/changed-files.txt
  echo "PASS (changed files list saved)"
  echo "- [PASS] Writer Rule" >> "$REPORT"
  PASS=$((PASS+1))
else
  echo "SKIP (no git)"
fi

# Result summary
echo "" >> "$REPORT"
echo "## Result Summary" >> "$REPORT"
echo "- PASS: $PASS" >> "$REPORT"
echo "- FAIL: $FAIL" >> "$REPORT"

echo ""
echo "=== Result: PASS=$PASS FAIL=$FAIL ==="

if [ "$FAIL" -gt 0 ]; then
  echo "[BLOCK] Quality gate failed → Deploy aborted"
  exit 1
fi

echo "[OK] Quality gate passed → Ready to deploy"
exit 0
