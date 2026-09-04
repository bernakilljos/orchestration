#!/usr/bin/env bash
# Codex / Gemini 호출 후 자동 git diff + hallucination 검출
# 사용:
#   pre  <task-slug>     -> snapshot 저장
#   post <task-slug>     -> git add + diff + commit (변경 0 = hallucination)
set -e
cd "$(dirname "$0")/../../.."  # PROJECT_ROOT (plugins/exec_orch/hooks -> repo root)

MODE="${1:-}"
SLUG="${2:-unknown}"
STATE_DIR=".claude/state/codex-verify"
mkdir -p "$STATE_DIR"

if [ "$MODE" = "pre" ]; then
  git rev-parse HEAD > "$STATE_DIR/${SLUG}.pre_sha" 2>/dev/null || echo "no-git" > "$STATE_DIR/${SLUG}.pre_sha"
  exit 0
fi

if [ "$MODE" = "post" ]; then
  PRE_SHA=$(cat "$STATE_DIR/${SLUG}.pre_sha" 2>/dev/null || echo "no-git")
  git add -A 2>/dev/null || true

  STAGED=$(git diff --cached --stat 2>/dev/null | tail -1 || echo "")
  CHANGED=$(git diff --cached --numstat 2>/dev/null | awk '{s+=$1+$2} END {print s+0}')

  if [ "$CHANGED" = "0" ] || [ -z "$STAGED" ]; then
    git commit --allow-empty -m "codex: ${SLUG} [HALLUCINATION] no changes" >/dev/null 2>&1 || true
    echo "[VERIFY] [HALLUCINATION] ${SLUG}: changed=0 (codex 보고 거짓 가능성)"
    echo "halluc" > "$STATE_DIR/${SLUG}.status"
    exit 0
  fi

  git commit -m "codex: ${SLUG} [auto-verify]

Actual changes:
${STAGED}
" >/dev/null 2>&1 || true

  echo "[VERIFY] [OK] ${SLUG}: ${STAGED}"
  echo "ok" > "$STATE_DIR/${SLUG}.status"
  exit 0
fi

echo "[VERIFY] mode required: pre|post"
exit 1
