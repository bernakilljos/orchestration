#!/bin/bash
# Hook: codex/claude 구현 완료 후 자동 검증
# Python 문법, import, 서버 기동 테스트
# 실패 시 exit 2 -> 태스크 완료 처리 차단

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

# 2026-11-13 (R249): 실패 문구를 stdout 에 쓰고 exit 2 로 끝나 Claude 는 무엇이 실패했는지 못 받았다
#   (공식 hooks 문서: PostToolUse exit 2 = "Shows stderr to Claude" · exit 2 의 stdout 은 전달 안 됨) → 출력 전부 stderr 로.
exec 1>&2

ERRORS=0

# R357 (2026-11-23): Edit 마다 작업 중 변경 파일 전체를 다시 검사했다 (실측 1회 3.7초 · 100초에 프로세스 22개).
#   검사 결과는 «변경 파일 집합과 그 내용» 으로 정해지므로, 이번에 고친 파일이 검사 대상 종류가 아니면 직전 결과와 같다
#   → 그때는 바로 끝낸다. 경로는 입력 JSON 에서 bash 내장 정규식으로만 읽는다 (프로세스 0개) · 경로를 못 읽으면 종전대로 전체 검사.
if [ ! -t 0 ]; then
  HOOK_INPUT="$(cat 2>/dev/null || true)"
  if [[ "$HOOK_INPUT" =~ \"file_path\"[[:space:]]*:[[:space:]]*\"([^\"]*)\" ]]; then
    EDITED="${BASH_REMATCH[1]}"
    shopt -s nocasematch
    if [[ ! "$EDITED" =~ \.(py|js|jsx|vue|java|md|docx|pptx|xlsx|hwpx|png)$ && ! "$EDITED" =~ (config\.py|settings\.json|\.env)$ ]]; then
      exit 0
    fi
    shopt -u nocasematch
  fi
fi

# 2026-11-22 (R354 14차): 검사 대상 = 이번 작업 전체 — 커밋 안 한 변경(스테이징 포함) + 새 파일 + 원격에 아직 안 올린 커밋 전부
#   (원격 추적이 없으면 직전 커밋). 종전 `git diff --name-only HEAD~1` 은 직전 커밋 1개만 봐서 앞 커밋에만 든 산출물이 빠졌고,
#   `for f in $(...)` 는 공백 든 파일명을 쪼갰다 → NUL 구분 목록 · 사용: while IFS= read -r -d '' f; do …; done < <(changed_files '<ERE>')
#   (4번 보호 파일 검사는 파일 내용이 아니라 «직전 커밋» 정책이라 그대로 둠)
#   R357: 검사 구간 7곳이 부를 때마다 git 3~4개·sort·grep 을 새로 띄웠다 → 목록은 처음 한 번만 구하고 (같은 명령·같은 정렬)
#   구간별 거르기는 bash 내장 정규식 (프로세스 0개 · 대소문자 구분·확장 정규식 = 종전 grep -zE 와 같음)
_ALL_CHANGED=()
_load_changed() {   # 본 셸에서 한 번 — changed_files 는 < <(…) 하위 셸에서 불려 거기서 채운 값은 남지 않는다
  local _f
  while IFS= read -r -d '' _f; do _ALL_CHANGED+=("$_f"); done < <({
    git diff -z --name-only HEAD 2>/dev/null
    git ls-files -z --others --exclude-standard 2>/dev/null
    if git rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
      git diff -z --name-only '@{u}' HEAD 2>/dev/null
    else
      git diff -z --name-only HEAD~1 HEAD 2>/dev/null
    fi
  } | sort -zu)
}
changed_files() {
  local _f
  for _f in "${_ALL_CHANGED[@]}"; do
    [[ "$_f" =~ $1 ]] && printf '%s\0' "$_f"
  done
  return 0
}

_load_changed

# 1. Python 문법 검사 (변경된 .py 파일)
#    R357: 파일마다 python 을 띄우던 것 → 한 번에 컴파일 (판정·문구·순서 동일 · 실패 파일 이름만 NUL 로 돌려받음)
if command -v python &>/dev/null; then
  PYF=()
  while IFS= read -r -d '' f; do
    [ -f "$f" ] && PYF+=("$f")
  done < <(changed_files '\.py$')
  if [ ${#PYF[@]} -gt 0 ]; then
    while IFS= read -r -d '' f; do
      echo "[VERIFY FAIL] Python syntax error: $f"
      ERRORS=$((ERRORS+1))
    done < <(python -c "
import sys
for p in sys.argv[1:]:
    try:
        compile(open(p, encoding='utf-8', errors='replace').read(), p, 'exec')
    except Exception:
        sys.stdout.write(p + chr(0))
" "${PYF[@]}" 2>/dev/null)
  fi
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
#    R357: 파일마다 file·grep 2개씩 띄우던 것 → file 1번 · grep 1번에 모든 파일 (같은 도구·같은 패턴 · 파일 순서대로 같은 문구)
ENCF=()
while IFS= read -r -d '' f; do
  [ -f "$f" ] && ENCF+=("$f")
done < <(changed_files '\.(py|js|vue|java|md)$')
if [ ${#ENCF[@]} -gt 0 ]; then
  declare -A BAD_ENC=() BAD_KO=()
  while IFS= read -r -d '' name && IFS= read -r desc; do
    shopt -s nocasematch   # 종전 grep -qi "UTF-16\|ISO-8859\|ASCII text.*with escape" 와 같은 판정 (프로세스 0개)
    if [[ "$desc" =~ UTF-16|ISO-8859|ASCII\ text.*with\ escape ]]; then BAD_ENC["$name"]=1; fi
    shopt -u nocasematch
  done < <(file -0 -- "${ENCF[@]}" 2>/dev/null)
  # 깨진 한글 패턴 (\ufffd 연속)
  while IFS= read -r -d '' name; do
    BAD_KO["$name"]=1
  done < <(grep -lZP '\xef\xbf\xbd{2,}' -- "${ENCF[@]}" 2>/dev/null)
  for f in "${ENCF[@]}"; do
    if [ -n "${BAD_ENC[$f]:-}" ]; then
      echo "[VERIFY FAIL] Wrong encoding (not UTF-8): $f"
      ERRORS=$((ERRORS+1))
    fi
    if [ -n "${BAD_KO[$f]:-}" ]; then
      echo "[VERIFY FAIL] Broken Korean text: $f"
      ERRORS=$((ERRORS+1))
    fi
  done
fi

# 4. config.py/settings.json 변경 여부 체크
_PROT_DIFF="$(git diff --name-only HEAD~1 2>/dev/null)"   # R357: 보호 파일마다 같은 git diff 를 3번 → 1번
for protected in config.py .claude/settings.json .env; do
  if printf '%s\n' "$_PROT_DIFF" | grep -q "$protected"; then
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
