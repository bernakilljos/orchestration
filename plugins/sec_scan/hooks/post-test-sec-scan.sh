#!/usr/bin/env bash
# sec_scan Hook — test_gen 완료 후 자동 호출
# AI-Native 파이프라인 2단계
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/sec-scan.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

FILE_PATH="${1:-}"
[ -z "$FILE_PATH" ] && exit 0
[ -f "$PROJECT_ROOT/$FILE_PATH" ] || [ -f "$FILE_PATH" ] || exit 0

echo "[$(date +%F_%T)] sec_scan start: $FILE_PATH" >> "$LOG"

# 도구 자동 설치 (한 번만)
INSTALL_FLAG="${PROJECT_ROOT}/.claude/state/.sec-tools-installed"
if [ ! -f "$INSTALL_FLAG" ]; then
  pip install semgrep bandit 2>>"$LOG" >/dev/null || true
  touch "$INSTALL_FLAG"
fi

ISSUES=0
RESULT_DIR="${PROJECT_ROOT}/.claude/state"
mkdir -p "$RESULT_DIR"

# semgrep (모든 언어)
if command -v semgrep >/dev/null 2>&1; then
  semgrep --config=auto --json --output="${RESULT_DIR}/semgrep-${FILE_PATH//\//_}.json" \
    "$PROJECT_ROOT/$FILE_PATH" >>"$LOG" 2>&1 || ISSUES=$((ISSUES+1))
fi

# bandit (Python only)
case "$FILE_PATH" in
  *.py)
    if command -v bandit >/dev/null 2>&1; then
      bandit -f json -o "${RESULT_DIR}/bandit-${FILE_PATH//\//_}.json" -ll \
        "$PROJECT_ROOT/$FILE_PATH" >>"$LOG" 2>&1 || ISSUES=$((ISSUES+1))
    fi
    ;;
esac

echo "[$(date +%F_%T)] sec_scan done: $ISSUES issue files" >> "$LOG"

# 다음 단계 (doc_auto)
CHAIN="${PROJECT_ROOT}/.claude/scripts/ai-native-chain.sh"
if [ -x "$CHAIN" ] && [ "$ISSUES" -lt 2 ]; then
  "$CHAIN" doc_auto "$FILE_PATH" >> "$LOG" 2>&1 &
fi

exit 0
