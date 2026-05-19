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

# 도구 자동 설치 (통합 스크립트 — 멱등)
INSTALL_SCRIPT="${PROJECT_ROOT}/.claude/scripts/install-sec-tools.sh"
[ -x "$INSTALL_SCRIPT" ] && bash "$INSTALL_SCRIPT" >/dev/null 2>&1 || true

ISSUES=0
RESULT_DIR="${PROJECT_ROOT}/.claude/state"
TOOLS_DIR="${RESULT_DIR}/tools"
mkdir -p "$RESULT_DIR"

# semgrep — CLI 호출 (Windows: python -m semgrep, 다른 OS: semgrep)
SEMGREP_CMD=""
if command -v semgrep >/dev/null 2>&1; then
  SEMGREP_CMD="semgrep"
elif python -m semgrep --version >/dev/null 2>&1; then
  SEMGREP_CMD="python -m semgrep"
fi
if [ -n "$SEMGREP_CMD" ]; then
  $SEMGREP_CMD --config=auto --json --output="${RESULT_DIR}/semgrep-${FILE_PATH//\//_}.json" \
    "$PROJECT_ROOT/$FILE_PATH" >>"$LOG" 2>&1 || ISSUES=$((ISSUES+1))
fi

# bandit — Python only (CLI 또는 module)
case "$FILE_PATH" in
  *.py)
    BANDIT_CMD=""
    if command -v bandit >/dev/null 2>&1; then
      BANDIT_CMD="bandit"
    elif python -m bandit --version >/dev/null 2>&1; then
      BANDIT_CMD="python -m bandit"
    fi
    if [ -n "$BANDIT_CMD" ]; then
      $BANDIT_CMD -f json -o "${RESULT_DIR}/bandit-${FILE_PATH//\//_}.json" -ll \
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
