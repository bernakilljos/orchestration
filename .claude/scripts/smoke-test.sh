#!/usr/bin/env bash
# Smoke test — 핵심 도구 자동 점검
set +e
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

PASS=0
FAIL=0

run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  [OK] $name"; PASS=$((PASS+1))
  else
    echo "  [X] $name"; FAIL=$((FAIL+1))
  fi
}

echo "[smoke-test] 핵심 도구 점검"
run_test "classify-task" python .claude/scripts/classify-task.py "코드 800줄"
run_test "auto-dispatch" python .claude/scripts/auto-dispatch.py "테스트"
run_test "recall-memory" python .claude/scripts/recall-memory.py "이미지"
run_test "rag-recall (build skip)" python .claude/scripts/rag-recall.py "이미지" --top 1
run_test "detect-system" python .claude/scripts/detect-system.py
run_test "log-decision" python .claude/scripts/log-decision.py "test"
run_test "log-activation" python .claude/scripts/log-activation.py hook smoke-test
run_test "track-determinism" python .claude/scripts/track-determinism.py "p" "r"
run_test "verify-image-whitespace" python .claude/scripts/verify-image-whitespace.py docs/screens/arch-kor
run_test "cost-dashboard" python .claude/scripts/cost-dashboard.py
run_test "update-claude-md" python .claude/scripts/update-claude-md.py
run_test "validate-plugin-schema" python .claude/scripts/validate-plugin-schema.py

echo ""
echo "[smoke-test] 결과: PASS=$PASS FAIL=$FAIL"
exit $FAIL
