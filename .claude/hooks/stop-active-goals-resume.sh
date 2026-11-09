#!/usr/bin/env bash
# stop-active-goals-resume.sh — 미완 goal 존재 시 next-actions.md 자동 재기록
# 사용자 지시 (2026-10-27): "작업 목록을 저장하거나 다음 세션으로 넘기는 것만으로 완료라고 선언하지 마"
# 개별 task 완료 ≠ 전체 goal 완료 ≠ 전체 요청 완료 구분.
# Supervisor 미완 goal (PENDING/PLANNING/RUNNING/REPAIRING/BLOCKED) 있으면
# next-actions.md 상단에 "이어서 할 일 — 자동 재기록" 블록 생성.
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
# fallback: script 위치 기준 (.claude/hooks → 2단계 위 = 프로젝트 루트)
if [ ! -d "$PROJECT_DIR/.claude" ]; then
  PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
fi
cd "$PROJECT_DIR" || exit 0

PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0

SUP="$PROJECT_DIR/.claude/scripts/lib/supervisor.py"
[ -f "$SUP" ] || exit 0

NEXT_ACTIONS="$PROJECT_DIR/.claude/state/next-actions.md"
mkdir -p "$(dirname "$NEXT_ACTIONS")" 2>/dev/null

# 미완 goal 조회 → goals 자동 블록만 교체 (2026-11-09: 파일 통째 재작성이 수동 지시를 지우고
# supervisor 출력이 콘솔 인코딩(cp949)으로 섞여 재개 주입이 조용히 실패하던 결함 · 정본 writer 1곳)
PYTHONIOENCODING=utf-8 "$PY" -X utf8 "$SUP" active 2>/dev/null   | PYTHONIOENCODING=utf-8 "$PY" -X utf8 "$PROJECT_DIR/.claude/scripts/auto-save-next-actions.py" goals 2>/dev/null || true

exit 0
