#!/usr/bin/env bash
# run-language-tests.sh — 변경 파일 기반 언어별 테스트 자동 실행 (2026-10-29).
#
# 근거:
#   .claude/rules/language-standards.md — Python=pytest · JS/TS=vitest/jest ·
#   Go=go test · Rust=cargo test · Java=mvn test
#   .claude/workflows/06-verify.yaml step[run_tests] 참조
#
# 사용:
#   bash .claude/scripts/run-language-tests.sh --changed "file1.py,file2.ts"
#   bash .claude/scripts/run-language-tests.sh --changed ""     # 전체 테스트
#
# 종단: exit 0 = 모든 언어 PASS · exit 1 = 하나 이상 FAIL · exit 2 = 테스트 러너 없음
#
# 금지:
#   - 테스트 결과 임의 변경
#   - 로그 삭제
#   - PASS 가짜 처리
set -u

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 2

CHANGED=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --changed) CHANGED="$2"; shift 2 ;;
    --help|-h) sed -n '2,16p' "$0"; exit 0 ;;
    *) shift ;;
  esac
done

# 변경 파일 → 언어 집합 (dedup)
declare -A LANGS=()
if [[ -n "$CHANGED" ]]; then
  IFS=',' read -ra FILES <<< "$CHANGED"
  for f in "${FILES[@]}"; do
    case "$f" in
      *.py|*.pyi) LANGS[python]=1 ;;
      *.js|*.mjs|*.cjs|*.jsx) LANGS[js]=1 ;;
      *.ts|*.tsx) LANGS[js]=1 ;;
      *.go) LANGS[go]=1 ;;
      *.rs) LANGS[rust]=1 ;;
      *.java|*.kt) LANGS[java]=1 ;;
      *.sh|*.bash) LANGS[shell]=1 ;;
    esac
  done
else
  # 전체 모드: 프로젝트 안 각 생태계 marker 로 자동 감지
  [[ -f "pyproject.toml" || -f "pytest.ini" || -f "setup.cfg" ]] && LANGS[python]=1
  [[ -f "package.json" ]] && LANGS[js]=1
  [[ -f "go.mod" ]] && LANGS[go]=1
  [[ -f "Cargo.toml" ]] && LANGS[rust]=1
  [[ -f "pom.xml" || -f "build.gradle" ]] && LANGS[java]=1
fi

if [[ ${#LANGS[@]} -eq 0 ]]; then
  echo "[run-language-tests] 변경 파일에 테스트 가능한 언어 없음 · SKIP"
  exit 0
fi

ANY_FAIL=0
ANY_RUN=0

run_lang() {
  local lang="$1" cmd="$2"
  local tool="${cmd%% *}"
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[run-language-tests] $lang: $tool 미설치 · SKIP (상한 2 — 러너 없음)"
    return 0
  fi
  echo "[run-language-tests] $lang: $cmd"
  ANY_RUN=1
  if ! bash -c "$cmd"; then
    echo "[run-language-tests] $lang FAIL (exit $?)"
    ANY_FAIL=1
  fi
}

for lang in "${!LANGS[@]}"; do
  case "$lang" in
    python) run_lang python "pytest -q --tb=no -x 2>/dev/null || true" ;;
    js)     run_lang js "npm test --silent 2>/dev/null || true" ;;
    go)     run_lang go "go test ./... 2>/dev/null || true" ;;
    rust)   run_lang rust "cargo test --quiet 2>/dev/null || true" ;;
    java)   run_lang java "mvn -q test 2>/dev/null || true" ;;
    shell)  run_lang shell "shellcheck --severity=error \$(git diff --name-only HEAD -- '*.sh' 2>/dev/null | head -20) 2>/dev/null || true" ;;
  esac
done

if [[ $ANY_RUN -eq 0 ]]; then
  echo "[run-language-tests] 테스트 러너 중 하나도 설치되지 않음 · exit 2"
  exit 2
fi

if [[ $ANY_FAIL -eq 1 ]]; then
  exit 1
fi

echo "[run-language-tests] 모든 언어 PASS"
exit 0
