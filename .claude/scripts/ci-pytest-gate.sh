#!/usr/bin/env bash
# ci-pytest-gate.sh — CI 에서 pytest 종료 코드를 구분해 실패를 그대로 전파 (R346 · 2026-11-20).
# 종전 test-matrix.yml: `pytest ... 2>/dev/null || echo "No tests found"` → 시험 실패·수집 0건·사용 오류가 모두 success
#   (실측: 'Run pytest' 1초 = 없는 경로 plugins/*/tests 로 rc 4 인데 success).
# pytest 공식 종료 코드: 0 통과 · 1 실패 · 2 중단 · 3 내부 오류 · 4 사용 오류 · 5 수집 0건 (docs.pytest.org Exit codes).
# usage: ci-pytest-gate.sh <pytest 인자...>   · PYTEST_CMD 로 실행 명령 대체 (결함 주입 시험용)
set -u
${PYTEST_CMD:-python -m pytest} "$@"
rc=$?
case "$rc" in
  0) echo "[ci-pytest-gate] 통과 (rc 0)" ;;
  1) echo "::error::[ci-pytest-gate] 시험 실패 (rc 1)" ;;
  2) echo "::error::[ci-pytest-gate] 실행 중단 (rc 2)" ;;
  3) echo "::error::[ci-pytest-gate] pytest 내부 오류 (rc 3)" ;;
  4) echo "::error::[ci-pytest-gate] 사용 오류 — 경로·옵션 확인 (rc 4)" ;;
  5) echo "::error::[ci-pytest-gate] 수집된 시험 0건 — 통과로 보지 않음 (rc 5)" ;;
  *) echo "::error::[ci-pytest-gate] 알 수 없는 종료 코드 $rc" ;;
esac
exit "$rc"
