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

# 미완 goal 조회
ACTIVE=$("$PY" "$SUP" active 2>/dev/null)
COUNT=$(echo "$ACTIVE" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null)
COUNT="${COUNT:-0}"

if [ "$COUNT" = "0" ]; then
  exit 0
fi

TS="$(date '+%Y-%m-%d %H:%M:%S')"

# next-actions.md 상단에 자동 재기록 블록 추가 (기존 블록 교체)
TMP="${NEXT_ACTIONS}.tmp.$$"
{
  echo "# 이어서 할 일 — 자동 재기록 (${TS})"
  echo ""
  echo "**사용자 지시 (2026-10-27)**: next-actions.md 저장만으로 완료 선언 X. 다음 세션 첫 응답에서 **확인 질문 없이 바로 이것부터 진행.**"
  echo ""
  echo "## 미완 Goals ($COUNT 건)"
  echo ""
  echo '```json'
  echo "$ACTIVE"
  echo '```'
  echo ""
  echo "**복구 명령 (다음 세션에서 자동 실행 예정)**:"
  echo '```bash'
  echo "python .claude/scripts/lib/supervisor.py active   # 현재 상태"
  echo "python .claude/scripts/lib/supervisor.py advance-all   # 자동 진행"
  echo '```'
  echo ""
  echo "---"
  echo ""
  # 기존 콘텐츠 중 "# 이어서 할 일 — 자동 재기록" 이전 섹션 (수동 작성 부분) 보존
  if [ -f "$NEXT_ACTIONS" ]; then
    "$PY" -c "
import sys, io
with io.open(r'''$NEXT_ACTIONS''', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
marker = '# 이어서 할 일 — 자동 재기록'
if marker in content:
    # 이전 자동 재기록 블록 제거 (--- 로 끝남)
    idx = content.find(marker)
    sep_idx = content.find('\n---\n', idx)
    if sep_idx > 0:
        content = content[sep_idx + 5:]
sys.stdout.write(content)
" 2>/dev/null
  fi
} > "$TMP" 2>/dev/null

if [ -s "$TMP" ]; then
  mv "$TMP" "$NEXT_ACTIONS"
fi

exit 0
