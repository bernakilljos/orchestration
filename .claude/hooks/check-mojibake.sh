#!/bin/bash
# check-mojibake.sh — Write/Edit 시 한글 깨짐 감지 + 차단
#
# 트리거: PreToolUse (Write|Edit)
# 검출:
#   - U+FFFD (REPLACEMENT CHARACTER, 깨진 문자)
#   - UTF-8 → cp949 오인 패턴 (ÂÃ 연속, íìîï 연속)
#
# 결과: 깨짐 감지 시 tool 실행 차단 + 원인 알림
#
# 성능 (2026-09-02 실측): 매 편집마다 돈다. 이전 구현은 python 을 최대 3번 띄웠고
#   (content 추출 → U+FFFD 검사 → 오인패턴 검사) 777ms 였다.
#   Windows + Privacy-i(DLP) 에서 python 기동만 400ms 라 회수 자체가 비용이다.
#   → ① bash 내장으로 '깨짐 후보 문자'가 아예 없으면 python 없이 즉시 통과
#     ② 후보가 있을 때만 python 1회로 추출·판정을 한 번에 처리
#   정상 한글/영문만 있는 대다수 편집은 python 을 0번 띄운다.

set -uo pipefail

read -r -d '' INPUT || true
[ -n "${INPUT:-}" ] || { echo '{"continue": true}'; exit 0; }

# ---- 1차 필터 (서브프로세스 0개) ----
# 깨짐 후보가 하나도 없으면 python 을 띄우지 않는다.
#
# 주의: payload 는 JSON 이라 REPLACEMENT CHARACTER 가 두 형태로 온다 —
#   (1) 원문 UTF-8 바이트 EF BF BD
#   (2) JSON 이스케이프 리터럴 (backslash + u + fffd)
# 초기 구현은 (1)만 보다가 (2)로 온 경우를 놓쳤다(실측). 둘 다 본다.
# 패턴을 파일에 리터럴로 적으면 이 훅이 자기 자신의 편집을 차단하므로 런타임 조립.
REPL_RAW=$(printf '\xef\xbf\xbd')
REPL_ESC="$(printf '%s' '\')u$(printf '%s' fffd)"
REPL_ESC_UC="$(printf '%s' '\')u$(printf '%s' FFFD)"
# JSON 은 non-ASCII 를 유니코드 이스케이프로 보낼 수 있다(json.dumps 기본값).
# 그 경우 원문자 글롭은 절대 매치하지 않는다 — 실측 확인.
BS="$(printf '%s' '\')"
U00="${BS}u00"          # latin-1 오독 대역(À~ó)의 이스케이프 접두
case "$INPUT" in
  *"$REPL_RAW"*|*"$REPL_ESC"*|*"$REPL_ESC_UC"* ) ;;
  *"$U00"* ) ;;
  *Â*|*Ã*|*à*|*á*|*â*|*ã*|*ä*|*å*|*æ*|*ç*|*è*|*é*|*ê*|*ë*|*ì*|*í*|*î*|*ï*|*ð*|*ñ*|*ò*|*ó* ) ;;
  *) echo '{"continue": true}'; exit 0 ;;
esac

# ---- 2차: python 1회로 추출 + 판정 ----
VERDICT=$(printf '%s' "$INPUT" | python -c "
import json, re, sys
try:
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
try:
    d = json.load(sys.stdin)
except Exception:
    print('ok'); sys.exit(0)
ti = d.get('tool_input', {}) or {}
txt = ti.get('content') or ti.get('new_string') or ''
if not isinstance(txt, str) or not txt:
    print('ok'); sys.exit(0)
if '�' in txt:
    print('repl'); sys.exit(0)
for p in (re.compile(r'[ÂÃ][\x80-\xBF]{2,}'), re.compile(r'[íìîïðñòó]{2,}')):
    if p.search(txt):
        print('mojibake'); sys.exit(0)
print('ok')
" 2>/dev/null || echo ok)

case "$VERDICT" in
  repl)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"한글 깨짐 감지 (U+FFFD). UTF-8 인코딩 확인 후 재시도."}}'
    ;;
  mojibake)
    printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"한글 깨짐 패턴 감지 (cp949 오인). UTF-8 로 재인코딩 후 재시도."}}'
    ;;
  *)
    echo '{"continue": true}'
    ;;
esac
exit 0
