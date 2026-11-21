#!/bin/bash
# Hook: codex/claude 구현 완료 후 자동 검증
# Python 문법, import, 서버 기동 테스트
# 실패 시 exit 2 -> 태스크 완료 처리 차단

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

# 2026-11-13 (R249): 실패 문구를 stdout 에 쓰고 exit 2 로 끝나 Claude 는 무엇이 실패했는지 못 받았다
#   (공식 hooks 문서: PostToolUse exit 2 = "Shows stderr to Claude" · exit 2 의 stdout 은 전달 안 됨) → 출력 전부 stderr 로.
exec 1>&2

ERRORS=0

# 2026-11-22 (R354 14차): 검사 대상 = 이번 작업 전체 — 커밋 안 한 변경(스테이징 포함) + 새 파일 + 원격에 아직 안 올린 커밋 전부
#   (원격 추적이 없으면 직전 커밋). 종전 `git diff --name-only HEAD~1` 은 직전 커밋 1개만 봐서 앞 커밋에만 든 산출물이 빠졌고,
#   `for f in $(...)` 는 공백 든 파일명을 쪼갰다 → NUL 구분 목록 · 사용: while IFS= read -r -d '' f; do …; done < <(changed_files '<ERE>')
#   (4번 보호 파일 검사는 파일 내용이 아니라 «직전 커밋» 정책이라 그대로 둠)
changed_files() {
  {
    git diff -z --name-only HEAD 2>/dev/null
    git ls-files -z --others --exclude-standard 2>/dev/null
    if git rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
      git diff -z --name-only '@{u}' HEAD 2>/dev/null
    else
      git diff -z --name-only HEAD~1 HEAD 2>/dev/null
    fi
  } | sort -zu | grep -zE "$1" || true
}

# 1. Python 문법 검사 (변경된 .py 파일)
if command -v python &>/dev/null; then
  while IFS= read -r -d '' f; do
    if [ -f "$f" ]; then
      python -c "import sys; compile(open(sys.argv[1], encoding='utf-8', errors='replace').read(), sys.argv[1], 'exec')" "$f" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "[VERIFY FAIL] Python syntax error: $f"
        ERRORS=$((ERRORS+1))
      fi
    fi
  done < <(changed_files '\.py$')
fi

# 2. JavaScript/Vue 문법 검사 (변경된 .js/.vue 파일)
if command -v node &>/dev/null; then
  while IFS= read -r -d '' f; do
    if [ -f "$f" ]; then
      node --check "$f" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "[VERIFY FAIL] JS syntax error: $f"
        ERRORS=$((ERRORS+1))
      fi
    fi
  done < <(changed_files '\.(js|jsx)$')
fi

# 3. 인코딩 검사 (UTF-16, 깨진 한글 감지)
while IFS= read -r -d '' f; do
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
done < <(changed_files '\.(py|js|vue|java|md)$')

# 4. config.py/settings.json 변경 여부 체크
for protected in config.py .claude/settings.json .env; do
  if git diff --name-only HEAD~1 2>/dev/null | grep -q "$protected"; then
    echo "[VERIFY FAIL] Protected file modified: $protected"
    ERRORS=$((ERRORS+1))
  fi
done

# 5. 빌드 산출물 visual 검증 (codex 자식 프로세스 안 빌드 명령은 hook-09 우회 — 여기서 보강)

while IFS= read -r -d '' docx; do
  [ -f "$PROJECT_ROOT/$docx" ] || continue
  if [ -f "$PROJECT_ROOT/.claude/scripts/verify-docx-structure.py" ]; then
    RESULT=$(python "$PROJECT_ROOT/.claude/scripts/verify-docx-structure.py" "$PROJECT_ROOT/$docx" 2>&1 || true)
    if echo "$RESULT" | grep -q 'FAIL'; then
      echo "[VERIFY FAIL] docx structure: $docx"
      echo "$RESULT" | head -5
      ERRORS=$((ERRORS+1))
    fi
  fi
  if [ -f "$PROJECT_ROOT/.claude/scripts/verify-docx-pages.py" ]; then
    RESULT=$(python "$PROJECT_ROOT/.claude/scripts/verify-docx-pages.py" "$PROJECT_ROOT/$docx" 2>&1 || true)
    if echo "$RESULT" | grep -q 'FAIL'; then
      echo "[VERIFY FAIL] docx pages: $docx"
      echo "$RESULT" | head -5
      ERRORS=$((ERRORS+1))
    fi
  fi
done < <(changed_files '\.docx$')

while IFS= read -r -d '' pptx; do
  [ -f "$PROJECT_ROOT/$pptx" ] || continue
  if [ -f "$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py" ]; then
    RESULT=$(python "$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py" 2>&1 || true)
    if echo "$RESULT" | grep -q '\[!\]'; then
      echo "[VERIFY WARN] pptx overflow suspects: $pptx (manual Read tool 검증 권장)"
    fi
  fi
done < <(changed_files '\.pptx$')

# R347#1: 파일 단위 패키지 검증 (pptx·xlsx·hwpx — 관계 대상·XML 문법·슬라이드 밖 도형·수식 오류 값·없는 시트·hwpx 필수 파트)
if [ -f "$PROJECT_ROOT/.claude/scripts/verify-office-package.py" ]; then
  while IFS= read -r -d '' pkg; do
    [ -f "$PROJECT_ROOT/$pkg" ] || continue
    if ! RESULT=$(python -X utf8 "$PROJECT_ROOT/.claude/scripts/verify-office-package.py" "$PROJECT_ROOT/$pkg" 2>&1); then
      echo "[VERIFY FAIL] office package: $pkg"
      echo "$RESULT" | grep -A3 '"fails"' | head -5
      ERRORS=$((ERRORS+1))
    fi
  done < <(changed_files '\.(pptx|xlsx|hwpx)$')
fi

# R354 15차: PNG 폴더 목록도 NUL 로 끝까지 (줄바꿈 든 파일명이 줄 단위 처리에서 폴더를 잘못 나누던 것)
if [ -f "$PROJECT_ROOT/.claude/scripts/verify-image-whitespace.py" ]; then
  while IFS= read -r -d '' dir; do
    [ -d "$PROJECT_ROOT/$dir" ] || continue
    RESULT=$(python "$PROJECT_ROOT/.claude/scripts/verify-image-whitespace.py" "$PROJECT_ROOT/$dir" 2>&1 || true)
    if echo "$RESULT" | grep -q 'WARN'; then
      echo "[VERIFY WARN] PNG whitespace in $dir (≥5% blank)"
    fi
  done < <(changed_files '^docs/.*\.png$' | while IFS= read -r -d '' f; do d="${f%/*}"; [ "$d" = "$f" ] && d=.; printf '%s\0' "$d"; done | sort -zu)
fi

if [ $ERRORS -gt 0 ]; then
  echo "[VERIFY] $ERRORS errors found — task NOT complete"
  exit 2
fi

echo "[VERIFY] All checks passed"
exit 0
