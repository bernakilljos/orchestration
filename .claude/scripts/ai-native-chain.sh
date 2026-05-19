#!/usr/bin/env bash
# AI-Native 파이프라인 체인 스크립트
# test_gen → sec_scan → doc_auto 순차 호출
#
# Usage:
#   ai-native-chain.sh <stage> <file_path>
#
# Stages:
#   test_gen — pytest/jest 테스트 자동 생성
#   sec_scan — semgrep + gitleaks + bandit
#   doc_auto — README/CHANGELOG 자동 갱신
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/ai-native-chain.log"

STAGE="${1:-}"
FILE_PATH="${2:-}"

[ -z "$STAGE" ] && { echo "usage: ai-native-chain.sh <stage> <file>"; exit 1; }
[ -z "$FILE_PATH" ] && exit 0

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# skip 확장자
case "$FILE_PATH" in
  *.md|*.json|*.yaml|*.yml|*.png|*.jpg|*.pptx|*.docx|*.pdf|*.lock)
    echo "[$(date +%F_%T)] skip ($STAGE): $FILE_PATH (non-code)" >> "$LOG"
    exit 0
    ;;
esac

# 테스트 파일 자체 skip
case "$FILE_PATH" in
  */tests/*|*/__tests__/*|*test_*.py|*.test.*|*.spec.*)
    echo "[$(date +%F_%T)] skip ($STAGE): $FILE_PATH (test file)" >> "$LOG"
    # 테스트 파일 변경 시도 sec_scan / doc_auto 는 진행
    case "$STAGE" in
      test_gen) exit 0 ;;
    esac
    ;;
esac

echo "[$(date +%F_%T)] ===== chain start: $STAGE on $FILE_PATH =====" >> "$LOG"

run_stage() {
  local stage="$1"
  local file="$2"
  local script=""

  case "$stage" in
    test_gen)
      script="${PROJECT_ROOT}/plugins/test_gen/hooks/post-edit-test-gen.sh"
      # test_gen 은 stdin JSON 받는 hook 이므로 직접 fake input
      if [ -x "$script" ]; then
        echo "{\"tool_input\":{\"file_path\":\"$file\"}}" | bash "$script" >> "$LOG" 2>&1 || true
      fi
      # test_gen 완료 후 sec_scan 호출
      "$0" sec_scan "$file" &
      ;;
    sec_scan)
      script="${PROJECT_ROOT}/plugins/sec_scan/hooks/post-test-sec-scan.sh"
      if [ -x "$script" ]; then
        bash "$script" "$file" >> "$LOG" 2>&1
        local rc=$?
        if [ "$rc" -ne 0 ]; then
          echo "[$(date +%F_%T)] sec_scan FAIL — skip doc_auto" >> "$LOG"
          return $rc
        fi
      fi
      # sec_scan PASS → doc_auto
      "$0" doc_auto "$file" &
      ;;
    doc_auto)
      script="${PROJECT_ROOT}/plugins/doc_auto/hooks/post-sec-doc.sh"
      if [ -x "$script" ]; then
        bash "$script" "$file" >> "$LOG" 2>&1 || true
      fi
      # 파이프라인 마지막. 다음 단계 X
      ;;
    *)
      echo "[$(date +%F_%T)] unknown stage: $stage" >> "$LOG"
      return 1
      ;;
  esac
}

run_stage "$STAGE" "$FILE_PATH"
echo "[$(date +%F_%T)] ===== chain done: $STAGE =====" >> "$LOG"
exit 0
