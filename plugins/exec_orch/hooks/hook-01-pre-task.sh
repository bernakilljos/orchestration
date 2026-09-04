#!/bin/bash
# HOOK-01 — Pre-Task: 태스크 시작 전 등록 + 파일 충돌 검사
set -e

PROJECT="${1:-$(pwd)}"
TASKS_DIR="$PROJECT/.claude/tasks"
CURRENT="$TASKS_DIR/current-tasks.json"

mkdir -p "$TASKS_DIR"

# current-tasks.json 없으면 빈 템플릿 생성
if [ ! -f "$CURRENT" ]; then
  echo '{"tasks":[]}' > "$CURRENT"
  echo "[HOOK-01] current-tasks.json 생성"
fi

# locked_files 충돌 검사 (jq 있으면 정확, 없으면 grep fallback)
TASK_INSTR="$TASKS_DIR/task-instruction.md"
if [ -f "$TASK_INSTR" ]; then
  TARGET_FILES=$(grep -E "^- target: " "$TASK_INSTR" 2>/dev/null | sed 's/^- target: //' || true)
  if [ -n "$TARGET_FILES" ]; then
    if command -v jq >/dev/null 2>&1; then
      LOCKED=$(jq -r '.tasks[]?.locked_files[]?' "$CURRENT" 2>/dev/null || true)
      while IFS= read -r tgt; do
        [ -z "$tgt" ] && continue
        if echo "$LOCKED" | grep -Fxq "$tgt" 2>/dev/null; then
          echo "[HOOK-01] [X] 파일 잠금 충돌: $tgt"
          exit 1
        fi
      done <<< "$TARGET_FILES"
    fi
  fi

  # 12 프롬프팅 기법 template 검증 (Role + Negative + Context + Few-shot + CoT 최소 4개)
  MISSING_TECH=""
  grep -qE "^## 1\) Role|^## Role" "$TASK_INSTR" || MISSING_TECH="$MISSING_TECH role"
  grep -qE "^## .*Negative|DO NOT:" "$TASK_INSTR" || MISSING_TECH="$MISSING_TECH negative"
  grep -qE "^## .*Context|Project root:" "$TASK_INSTR" || MISSING_TECH="$MISSING_TECH context"
  grep -qE "Acceptance|Few-shot|INPUT:.*OUTPUT:" "$TASK_INSTR" || MISSING_TECH="$MISSING_TECH few-shot"
  if [ -n "$MISSING_TECH" ]; then
    echo "[HOOK-01] [WARN] task-instruction.md 12 기법 누락:$MISSING_TECH"
    echo "[HOOK-01]   -> plugins/exec_orch/codex/task-instruction-template.md 참고"
    echo "[HOOK-01]   -> skill: plugins/exec_orch/skills/prompt-techniques.md"
  fi
fi

echo "[HOOK-01] OK"
exit 0
