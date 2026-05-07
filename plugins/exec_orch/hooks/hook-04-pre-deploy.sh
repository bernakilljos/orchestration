#!/bin/bash
# HOOK-04 — Pre-Deploy: 배포 전 게이트 (빌드·시크릿·리뷰 검사)
set -e

PROJECT="${1:-$(pwd)}"
cd "$PROJECT"

EXIT_CODE=0

# 1. 빌드 결과 확인
if [ -f "docs/build-result.txt" ]; then
  if grep -iE "error|failed" "docs/build-result.txt" >/dev/null 2>&1; then
    echo "[BLOCK] Build errors found in docs/build-result.txt"
    EXIT_CODE=1
  else
    echo "[OK] Build passed"
  fi
else
  echo "[WARN] docs/build-result.txt 없음 - 빌드 검사 skip"
fi

# 2. 시크릿 스캔 결과 확인 (filtered 파일이 비어있어야 OK)
if [ -f "docs/secret-scan-filtered.txt" ]; then
  if [ -s "docs/secret-scan-filtered.txt" ]; then
    echo "[BLOCK] Secret exposed (docs/secret-scan-filtered.txt 비어있지 않음)"
    EXIT_CODE=1
  else
    echo "[OK] No secrets"
  fi
else
  echo "[WARN] docs/secret-scan-filtered.txt 없음 - 시크릿 검사 skip"
fi

# 3. 리뷰 결정 확인
if [ -f "docs/review-decision.md" ]; then
  echo "[OK] Review done"
else
  echo "[WARN] No review - deploying anyway"
fi

# 4. Env 기반 배포 권한 (deploy-config.env 의 TARGET_ENV)
if [ -f ".claude/deploy-config.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .claude/deploy-config.env 2>/dev/null || true
  set +a
  case "${TARGET_ENV:-}" in
    demo) echo "[OK] DEMO - auto deploy allowed" ;;
    prod) echo "[GATE] PROD - 명시적 승인 필요 (수동 검증)" ;;
    *)    echo "[INFO] TARGET_ENV='${TARGET_ENV:-unset}'" ;;
  esac
fi

exit $EXIT_CODE
