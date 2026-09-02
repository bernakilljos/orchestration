#!/usr/bin/env bash
# SessionStart hook — 최근 세션 요약을 stdout(systemMessage) 로 주입
# Claude Code 는 hook stdout 을 systemMessage 로 사용 → 새 세션이 이전 컨텍스트 자동 인지
# 근거: 히스토리 DB 관리 정책 (2026-09-02)
set -eu
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG="$PROJECT_ROOT/.claude/logs/conversation-save.log"
mkdir -p "$PROJECT_ROOT/.claude/logs"

# 최근 3 세션 요약 로드 · stdout 으로 출력 (systemMessage)
CONTEXT="$(python -X utf8 "$PROJECT_ROOT/.claude/scripts/lib/conversation_logger.py" load 3 2>>"$LOG" || true)"

if [ -n "${CONTEXT:-}" ]; then
  echo "$CONTEXT"
fi

exit 0
