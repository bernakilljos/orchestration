#!/bin/bash
# =====================================================
# test.sh — Auto test generation and execution
# Usage: bash .claude/scripts/test.sh [component-path]
# Example: bash .claude/scripts/test.sh src/pages/TargetPage.vue
# =====================================================
set -e
source .claude/deploy-config.env 2>/dev/null || true

TARGET_FILE="${1:-}"
REPORT="docs/test-result.txt"
mkdir -p docs tests/unit 2>/dev/null || true

echo "=== SKILL-06 Test ==="

# Check test framework
if [ -f package.json ]; then
  HAS_JEST=$(grep -c '"jest"' package.json 2>/dev/null || echo 0)
  HAS_VTU=$(grep -c '"@vue/test-utils"' package.json 2>/dev/null || echo 0)

  if [ "$HAS_JEST" -eq 0 ]; then
    echo "[WARN] Jest not installed -> npm install --save-dev jest @vue/test-utils vue-jest babel-jest"
  fi
fi

# If target file specified -> generate test via Codex
if [ -n "$TARGET_FILE" ] && [ -f "$TARGET_FILE" ]; then
  COMPONENT_NAME=$(basename "$TARGET_FILE" .vue)
  SPEC_FILE="tests/unit/${COMPONENT_NAME}.spec.js"

  if [ ! -f "$SPEC_FILE" ]; then
    echo "No test file found -> Generating via Codex: $SPEC_FILE"

    if command -v codex >/dev/null; then
      codex --model gpt-4o \
        --instructions "$(cat .claude/tasks/task-instruction.md 2>/dev/null || echo 'Generate unit test for this component')" \
        --context "$(cat "$TARGET_FILE")" \
        "Generate a unit test for this component. Follow project testing conventions. Save to: $SPEC_FILE"
    else
      echo "[WARN] codex CLI not found -> Write tests manually"
    fi
  else
    echo "[OK] Using existing test file: $SPEC_FILE"
  fi
fi

# Run tests
echo ""
echo "=== Running Tests ==="

if [ -f package.json ]; then
  if npx jest --passWithNoTests 2>&1 | tee "$REPORT"; then
    echo "[OK] Frontend tests passed"
  else
    echo "[FAIL] Frontend tests failed -> See $REPORT"
    exit 1
  fi
fi

if [ -f pom.xml ]; then
  if ./mvnw test -q 2>&1 | tee -a "$REPORT"; then
    echo "[OK] Backend tests passed"
  else
    echo "[FAIL] Backend tests failed -> See $REPORT"
    exit 1
  fi
fi

# API Smoke Test
if [ -n "$REMOTE_HOST" ] && [ -n "$SERVICE_PORT" ]; then
  echo ""
  echo "=== API Smoke Test ==="
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    "http://localhost:${SERVICE_PORT}" 2>/dev/null || echo "000")
  [ "$status" != "000" ] \
    && echo "[OK] Local server response: $status" \
    || echo "[SKIP] Local server not running"
fi

echo ""
echo "[DONE] Tests complete -> See $REPORT"
