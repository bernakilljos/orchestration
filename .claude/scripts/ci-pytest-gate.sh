#!/usr/bin/env bash
# ci-pytest-gate.sh — CI 에서 pytest 종료 코드를 구분해 실패를 그대로 전파 (R346 · 2026-11-20).
# 종전 test-matrix.yml: `pytest ... 2>/dev/null || echo "No tests found"` → 시험 실패·수집 0건·사용 오류가 모두 success
#   (실측: 'Run pytest' 1초 = 없는 경로 plugins/*/tests 로 rc 4 인데 success).
# pytest 공식 종료 코드: 0 통과 · 1 실패 · 2 중단 · 3 내부 오류 · 4 사용 오류 · 5 수집 0건 (docs.pytest.org Exit codes).
# usage: ci-pytest-gate.sh <pytest 인자...>   · PYTEST_CMD 로 실행 명령 대체 (결함 주입 시험용)
set -u
# 2026-11-20 (R346 후속): 실패 시험 이름을 CI 주석(::error::)으로도 낸다 — Actions 로그는 인증이 있어야 읽히지만
#   주석은 공개 check-runs API 로 보여, 로컬에서 재현 안 되는 러너 전용 실패를 진단할 수 있다 (최대 20건 · 출력은 그대로 화면에도).
OUT="${TMPDIR:-${TEMP:-/tmp}}/ci-pytest-gate.$$.log"
set -o pipefail
${PYTEST_CMD:-python -m pytest} "$@" 2>&1 | tee "$OUT"
rc=$?
set +o pipefail
# R346 후속 5: -a = 로그에 NUL 등이 섞여도 텍스트로 읽음 (없으면 grep 이 줄 대신 "Binary file … matches" 만 냄 · Windows 러너 실측)
grep -aE '^(FAILED|ERROR) ' "$OUT" 2>/dev/null | head -20 | while IFS= read -r line; do
  echo "::error title=pytest::${line}"
done
rm -f "$OUT" 2>/dev/null
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
