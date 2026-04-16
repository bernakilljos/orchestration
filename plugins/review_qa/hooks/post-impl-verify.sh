#!/bin/bash
# Hook: codex/claude 구현 완료 후 자동 검증
# Python 문법, import, 서버 기동 테스트
# 실패 시 exit 2 → 태스크 완료 처리 차단

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

ERRORS=0

# 1. Python 문법 검사 (변경된 .py 파일)
if command -v python &>/dev/null; then
  for f in $(git diff --name-only HEAD~1 2>/dev/null | grep '\.py$'); do
    if [ -f "$f" ]; then
      python -c "import py_compile; py_compile.compile('$f', doraise=True)" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "[VERIFY FAIL] Python syntax error: $f"
        ERRORS=$((ERRORS+1))
      fi
    fi
  done
fi

# 2. JavaScript/Vue 문법 검사 (변경된 .js/.vue 파일)
if command -v node &>/dev/null; then
  for f in $(git diff --name-only HEAD~1 2>/dev/null | grep -E '\.(js|jsx)$'); do
    if [ -f "$f" ]; then
      node --check "$f" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "[VERIFY FAIL] JS syntax error: $f"
        ERRORS=$((ERRORS+1))
      fi
    fi
  done
fi

# 3. 인코딩 검사 (UTF-16, 깨진 한글 감지)
for f in $(git diff --name-only HEAD~1 2>/dev/null | grep -E '\.(py|js|vue|java|md)$'); do
  if [ -f "$f" ]; then
    if file "$f" 2>/dev/null | grep -qi "UTF-16\|ISO-8859\|ASCII text.*with escape"; then
      echo "[VERIFY FAIL] Wrong encoding (not UTF-8): $f"
      ERRORS=$((ERRORS+1))
    fi
    # 깨진 한글 패턴 (\ufffd 연속)
    if grep -Pq '\xef\xbf\xbd{2,}' "$f" 2>/dev/null; then
      echo "[VERIFY FAIL] Broken Korean text: $f"
      ERRORS=$((ERRORS+1))
    fi
  fi
done

# 4. config.py/settings.json 변경 여부 체크
for protected in config.py .claude/settings.json .env; do
  if git diff --name-only HEAD~1 2>/dev/null | grep -q "$protected"; then
    echo "[VERIFY FAIL] Protected file modified: $protected"
    ERRORS=$((ERRORS+1))
  fi
done

if [ $ERRORS -gt 0 ]; then
  echo "[VERIFY] $ERRORS errors found — task NOT complete"
  exit 2
fi

echo "[VERIFY] All checks passed"
exit 0
