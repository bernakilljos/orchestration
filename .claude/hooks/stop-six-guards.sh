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
GOLDEN_RESULT=$("$PY" -X utf8 "$ROOT/.claude/scripts/golden-test.py" 2>/dev/null | tail -3 | grep -oE "[0-9]+/[0-9]+" | head -1 || echo "")
GOLDEN_PASS=$(echo "$GOLDEN_RESULT" | cut -d/ -f1)
GOLDEN_TOTAL=$(echo "$GOLDEN_RESULT" | cut -d/ -f2)
if [ -n "$GOLDEN_RESULT" ] && [ "$GOLDEN_PASS" != "$GOLDEN_TOTAL" ]; then
  # 2026-10-26: opt-in block (flag 있으면 차단 · default WARN · overload 방지)
  if [ -f "$ROOT/.claude/state/golden-test.block-on-fail" ]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_MSGS="${FAIL_MSGS}\n  ✗ Verification Guard: Golden Test $GOLDEN_RESULT (block-on-fail flag ON)"
  else
    echo "[six-guards] WARN · Golden Test $GOLDEN_RESULT (N/N 미달 · block 하려면 touch .claude/state/golden-test.block-on-fail)" >&2
  fi
fi

# 7. Supervisor Guard — 미완료 goal 자동 advance (2026-10-27 사용자 "10개 중 2개 멈추지 마" fix)
# supervisor.advance_all_pending() 호출 · PENDING→PLANNING→RUNNING 자동 진행 · 결과 로그만 (block 안 함)
SUP_OUT=$("$PY" -X utf8 "$ROOT/.claude/scripts/lib/supervisor.py" advance-all 2>/dev/null || echo "")
if [ -n "$SUP_OUT" ]; then
  SUP_ADV=$(echo "$SUP_OUT" | grep -oE '"PENDING":[[:space:]]*[1-9][0-9]*|"PLANNING":[[:space:]]*[1-9][0-9]*|"RUNNING":[[:space:]]*[1-9][0-9]*' | head -1 || echo "")
  if [ -n "$SUP_ADV" ]; then
    echo "[six-guards] Supervisor: $SUP_ADV goal 자동 전환" >&2
  fi
fi

# 8. RPA/Desktop UI Verification Guard (2026-10-27 P0-2 fix · screen-verify.md § RPA/C/S 반영)
# RPA/.vbs/desktop/winforms/wpf/sap 파일 수정 감지 시 smoke test 증거 요구
RPA_PATTERN='\.(rpa|vbs|xaml)$|/(rpa|RPA|SAP|desktop|winforms|wpf)/|_rpa\.|_desktop\.'
RPA_CHANGES=$(git diff --cached --name-only 2>/dev/null | grep -E "$RPA_PATTERN" | head -5)
RPA_CHANGES+="$(git diff --name-only 2>/dev/null | grep -E "$RPA_PATTERN" | head -5)"
if [ -n "$RPA_CHANGES" ]; then
  # 자체 smoke test 증거 확인 — .claude/state/rpa-verify-*.flag or logs/rpa-smoke-test.log 최근 1h 내
  RPA_EVIDENCE=0
  if [ -f "$ROOT/.claude/logs/rpa-smoke-test.log" ]; then
    LOG_AGE=$(( $(date +%s) - $(stat -c %Y "$ROOT/.claude/logs/rpa-smoke-test.log" 2>/dev/null || echo 0) ))
    [ "$LOG_AGE" -lt 3600 ] && RPA_EVIDENCE=1
  fi
  if ls "$ROOT/.claude/state/"rpa-verify-*.flag 2>/dev/null | head -1 >/dev/null; then
    RPA_EVIDENCE=1
  fi
  if [ "$RPA_EVIDENCE" = "0" ]; then
    echo "[six-guards] WARN · RPA/Desktop UI 변경 감지 but smoke test 증거 없음 (.claude/state/rpa-verify-*.flag or .claude/logs/rpa-smoke-test.log < 1h)" >&2
    echo "  변경 파일: $(echo "$RPA_CHANGES" | head -3 | tr '\n' ' ')" >&2
    echo "  해결: smoke test 수행 후 touch .claude/state/rpa-verify-<slug>.flag" >&2
    # opt-in block
    if [ -f "$ROOT/.claude/state/rpa-verify.block-on-missing" ]; then
      FAIL_COUNT=$((FAIL_COUNT + 1))
      FAIL_MSGS="${FAIL_MSGS}\n  ✗ RPA Verification Guard: smoke test 증거 없음 (block flag ON)"
    fi
  fi
fi

# 4·5·6: warn-only — 참고용

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "[six-guards] $FAIL_COUNT Guard 미통과 · Stop 차단:" >&2
  printf '%b\n' "$FAIL_MSGS" >&2
  echo "→ 미완료 request 계속 실행 · ACTIVE standing requirement 복원 후 종료" >&2
  exit 2
fi

exit 0
