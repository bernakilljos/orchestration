#!/bin/bash
# HOOK-08 — AI Handoff: 멀티AI 인수인계 강제 검증 + auto chain
# 사용: hook-08-ai-handoff.sh claude-to-codex|codex-to-claude|gemini-to-claude|auto
# Sub-project guard: plugins/ 없는 sub-project 에선 silent exit (no-op)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
set +e

PHASE="${1:-claude-to-codex}"
PROJECT="${2:-$(pwd)}"
cd "$PROJECT" 2>/dev/null || true

# A2A 자율 — Stop hook 자동 호출 시 task 감지 + handoff-log
if [ "$PHASE" = "auto" ]; then
  TASK_DIR="$PROJECT/.claude/tasks"
  if [ -d "$TASK_DIR" ] && ls "$TASK_DIR"/task-*.md >/dev/null 2>&1; then
    HANDOFF_LOG="$TASK_DIR/handoff-log.md"
    LATEST="$(ls -t "$TASK_DIR"/task-*.md 2>/dev/null | head -1)"
    [ -n "$LATEST" ] && echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] [HANDOFF auto] task: $(basename "$LATEST")" >> "$HANDOFF_LOG"
  fi
  exit 0
fi

set -e

TASK_INSTR=".claude/tasks/task-instruction.md"
HANDOFF_LOG=".claude/tasks/handoff-log.md"
IMPL_REPORT="docs/implementation-report.md"
GEMINI_REPORT="docs/gemini-review.md"

case "$PHASE" in
  claude-to-codex)
    if [ ! -f "$TASK_INSTR" ]; then
      echo "[HANDOFF] ❌ $TASK_INSTR 없음 - Claude 가 작성 필요"
      exit 1
    fi
    if [ ! -f "$HANDOFF_LOG" ]; then
      echo "[HANDOFF] ❌ $HANDOFF_LOG 없음 - 빈 템플릿 생성"
      cat > "$HANDOFF_LOG" <<EOF
# Handoff Log

- from: claude
- to: codex
- at: $(date -u '+%Y-%m-%dT%H:%M:%SZ')

## Context (설계 결정 사유)


## Expected Output


## Constraints
- 수정 금지 파일:
- 코딩 규칙:
EOF
      exit 1
    fi
    # context / expected_output 비어있으면 차단
    if ! grep -qE "^## Context" "$HANDOFF_LOG" || ! grep -qE "^## Expected Output" "$HANDOFF_LOG"; then
      echo "[HANDOFF] ❌ handoff-log.md 필수 섹션 누락"
      exit 1
    fi
    echo "[HANDOFF-OK] claude → codex"
    ;;

  codex-to-claude)
    if [ ! -f "$IMPL_REPORT" ]; then
      echo "[HANDOFF] ❌ $IMPL_REPORT 없음 - Codex 가 작성 필요"
      exit 1
    fi
    # 변경 파일 목록 + 테스트 결과 확인
    grep -qiE "변경.*파일|changed.*files" "$IMPL_REPORT" || {
      echo "[HANDOFF] ❌ 변경 파일 목록 누락"; exit 1; }
    grep -qiE "PASS|FAIL|테스트" "$IMPL_REPORT" || {
      echo "[HANDOFF] ❌ 테스트 결과 누락"; exit 1; }
    echo "[HANDOFF-OK] codex → claude"
    ;;

  gemini-to-claude)
    if [ ! -f "$GEMINI_REPORT" ]; then
      echo "[HANDOFF] ❌ $GEMINI_REPORT 없음 - Gemini 검증 결과 필요"
      exit 1
    fi
    echo "[HANDOFF-OK] gemini → claude"
    ;;

  *)
    echo "[HANDOFF] Unknown phase: $PHASE"
    echo "사용: hook-08-ai-handoff.sh claude-to-codex|codex-to-claude|gemini-to-claude"
    exit 1
    ;;
esac

exit 0
