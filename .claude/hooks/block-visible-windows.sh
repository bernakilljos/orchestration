#!/bin/bash
# Hook: PreToolUse(Bash) — 세션이 보이는 창(CMD·PowerShell·서버 콘솔)을 띄우는 것을 **띄우기 전에** 막는다 (예방).
#
# 2026-10-14 사용자: "다른 섹션에서 테스트했으면 닫아 · 예방을 하라고". 세션들이 검증하며
#   bat 을 돌렸고, bat **안의** start 줄이 서버 콘솔 창을 열어 둔 채 남겼다.
#   종전 판은 명령어 글자만 봐서 bat 안을 못 봤다.
# 판정 (프로젝트 무관):
#   ① 명령 자체: start (/b·/min 없이) · cmd /k · Start-Process (-WindowStyle Hidden·-NoNewWindow 없이)
#   ② 명령이 실행하는 .bat/.cmd/.ps1 파일 안에 ①이 있으면 (파일:줄 을 알려 준다)
# 대응: exit 2 차단 + 창 없이 띄우는 방법 안내. 사용자가 창을 원할 때만 ALLOW_VISIBLE_WINDOW=1 로 우회.
# 성능: 무관 명령은 bash 내장만으로 즉시 종료 (프로세스 0개 · A1.RMS-UPG 0902 패턴).
# 정확성 (2026-09-02 · A1): payload 는 '"command": "' (콜론 뒤 공백) · 정규식은 변수에 담아야 이스케이프가 산다.

read -r -d '' INPUT || true

# 1차 필터 — 창을 열 수 있는 단어가 없으면 즉시 통과
case "$INPUT" in
  *start*|*START*|*Start*|*'cmd /k'*|*'cmd //k'*|*.bat*|*.BAT*|*.cmd*|*.ps1*) ;;
  *) exit 0 ;;
esac
case "$INPUT" in *ALLOW_VISIBLE_WINDOW=1*) exit 0 ;; esac

# command 값 추출 (bash 내장만)
CMD="${INPUT#*\"command\":}"; CMD="${CMD#\"}"; CMD="${CMD# \"}"
CMD="${CMD%%\", \"*}"; CMD="${CMD%%\",\"*}"; CMD="${CMD%%\"\}*}"
CMD="${CMD//\\\\/\\}"   # JSON 의 \\ → \
CMD="${CMD//\\\"/\"}"   # JSON 의 \" → "

shopt -s nocasematch
RE_COMMENT='^[[:space:]]*(rem[[:space:]]|::|#)'
RE_START='(^|[[:space:]&|(])start[[:space:]]'
RE_HIDDEN_START='[[:space:]]/(b|min)([[:space:]]|$)'
RE_SUBCMD_START='(run|next|npm|yarn|pnpm)[[:space:]]+start([^[:alnum:]_-]|$)'
RE_PROG='(cmd|powershell|pwsh|python|py[[:space:]]|\.exe|\.bat|\.cmd|%PY%|"%)'
RE_CMDK='cmd(\.exe)?[[:space:]]+//?k([[:space:]]|$)'
RE_SP='Start-Process'
RE_SP_HIDDEN='(-WindowStyle[[:space:]]+Hidden|-NoNewWindow)'

# 창 여는 줄인가 — /b·/min·Hidden·NoNewWindow 가 있으면 창 없음
_opens_window() {
  local l="$1"
  [[ $l =~ $RE_COMMENT ]] && return 1
  # `npm run start`·`next start` 는 cmd 의 start 가 아니라 하위 명령이다 — 빼고 본다
  #   (2026-10-17: 637 에서 python 이식판만 고쳐, cd /c/... 로 이 원본에 넘어온 명령은 start-3000.bat 의 Hidden 줄로 계속 막혔다)
  local bare="$l"
  while [[ $bare =~ $RE_SUBCMD_START ]]; do bare="${bare/"${BASH_REMATCH[0]}"/ }"; done
  if [[ $bare =~ $RE_START ]] && [[ ! $bare =~ $RE_HIDDEN_START ]] && [[ $bare =~ $RE_PROG ]]; then return 0; fi
  [[ $l =~ $RE_CMDK ]] && return 0
  if [[ $l =~ $RE_SP ]] && [[ ! $l =~ $RE_SP_HIDDEN ]]; then return 0; fi
  return 1
}

REASON=""
# ① 명령 자체
if _opens_window "$CMD"; then REASON="명령이 보이는 창을 연다: ${CMD:0:120}"; fi

# ② 명령이 실행하는 스크립트 파일 안 (cd "DIR" && … 의 DIR 기준으로 상대 경로 해석)
if [ -z "$REASON" ]; then
  BASE="${CLAUDE_PROJECT_DIR:-$PWD}"
  RE_CDQ='cd[[:space:]]+"([^"]+)"'
  RE_CD='cd[[:space:]]+([^[:space:]&;]+)'
  if [[ $CMD =~ $RE_CDQ ]]; then BASE="${BASH_REMATCH[1]}"; elif [[ $CMD =~ $RE_CD ]]; then BASE="${BASH_REMATCH[1]}"; fi
  RE_FILE='([A-Za-z]:[\\/][^"'"'"'[:space:]]*|[^"'"'"'[:space:]]*)\.(bat|cmd|ps1)'
  REST="$CMD"
  while [[ $REST =~ $RE_FILE ]]; do
    F="${BASH_REMATCH[0]}"; REST="${REST#*"$F"}"
    F="${F//\\//}"
    case "$F" in [A-Za-z]:/*|/*) P="$F" ;; *) P="$BASE/$F" ;; esac
    [ -f "$P" ] || continue
    n=0
    while IFS= read -r line || [ -n "$line" ]; do
      n=$((n+1))
      line="${line%$'\r'}"
      if _opens_window "$line"; then REASON="${F##*/}:$n 이 보이는 창을 연다 → ${line:0:100}"; break; fi
    done < "$P"
    [ -n "$REASON" ] && break
  done
fi

if [ -n "$REASON" ]; then
  {
    echo "BLOCKED(창 예방): $REASON"
    echo "  → 테스트·검증은 창 없이: run_in_background 로 직접 실행 (예: python run.py …) · 프로젝트에 숨김 모드가 있으면 그것 · start 를 쓰면 /b"
    echo "  → 테스트로 띄운 프로세스는 끝나면 닫는다 (원래 떠 있던 서버는 원래 방식으로 되돌린다)."
    echo "  → 사용자가 창을 원하면 명령 앞에 ALLOW_VISIBLE_WINDOW=1"
  } >&2
  exit 2   # PreToolUse 차단 규약: 2 = block (1 은 무시됨)
fi
exit 0
