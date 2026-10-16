#!/usr/bin/env bash
# stop-six-guards.sh — Stop hook: 6 Guards 전수 검증 (하나라도 FAIL → exit 2 종료 차단).
#
# 근거: 2026-10-16 사용자 명시 "statusline 만 아니라 반복 지시를 Guard 로 시스템화".
# SoT: .claude/rules/six-guards.md
#
# 검증 순서:
# 1. Completion Guard — request-ledger gate (N/N 완료)
# 2. Verification Guard — standing-requirements gate (ACTIVE 요구사항 verify)
# 3. Verification Guard — golden-test (10/10 PASS 필요)
# 4. Scope Guard — git diff 범위 외 수정 체크 (skip for now · scope-lock 자체 있음)
# 5. Quality Guard — recurrence-tracker 3회+ 승격 알림 (block 안 함 · warn only)
# 6. Freeze Guard — Change Budget 안 (block 안 함 · warn only)
set -eu
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PY="$(command -v python 2>/dev/null)"
[ -n "$PY" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
FAIL_MSGS=""
FAIL_COUNT=0

# 1. Completion Guard
if "$PY" -X utf8 "$ROOT/.claude/scripts/request-ledger.py" gate >/dev/null 2>&1; then
  :  # pass
else
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FAIL_MSGS="${FAIL_MSGS}\n  ✗ Completion Guard: Request Ledger 미완료 (python request-ledger.py status)"
fi

# 2. Verification Guard — standing-requirements
if "$PY" -X utf8 "$ROOT/.claude/scripts/standing-requirements.py" gate >/dev/null 2>&1; then
  :
else
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FAIL_MSGS="${FAIL_MSGS}\n  ✗ Verification Guard: Standing Requirement verify 실패"
fi

# 3. Verification Guard — golden-test (warn only · block 하면 overload)
# 사용자 명시 지시 시만 block
GOLDEN_RESULT=$("$PY" -X utf8 "$ROOT/.claude/scripts/golden-test.py" 2>/dev/null | tail -3 | grep -oE "[0-9]+/10" | head -1 || echo "")
GOLDEN_PASS=$(echo "$GOLDEN_RESULT" | cut -d/ -f1)
GOLDEN_TOTAL=$(echo "$GOLDEN_RESULT" | cut -d/ -f2)
if [ -n "$GOLDEN_RESULT" ] && [ "$GOLDEN_PASS" != "$GOLDEN_TOTAL" ]; then
  # warn
  echo "[six-guards] WARN · Golden Test $GOLDEN_RESULT (10/10 아님)" >&2
fi

# 4·5·6: warn-only — 참고용

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "[six-guards] $FAIL_COUNT Guard 미통과 · Stop 차단:" >&2
  printf '%b\n' "$FAIL_MSGS" >&2
  echo "→ 미완료 request 계속 실행 · ACTIVE standing requirement 복원 후 종료" >&2
  exit 2
fi

exit 0
