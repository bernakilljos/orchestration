#!/bin/bash
# Hook: PreToolUse — Bash 명령어에서 start 로 보이는 CMD 창 띄우기 차단
#
# 성능: 매 Bash 호출마다 돈다. Windows + Privacy-i(DLP) 환경에서 프로세스 생성이
#   300~400ms 라 grep/sed/echo 파이프를 쓰면 그것만으로 1.5초가 걸린다(실측 2026-09-02).
#   bash 내장(read · [[ ]] · ${})만 사용해 서브프로세스를 0개로 유지한다.
#
# 정확성 (2026-09-02 수정): 이전 버전은 두 가지 이유로 한 번도 차단하지 못했다.
#   1) '"command":"' (콜론 뒤 공백 없음) 만 찾았으나 실제 payload 는 '"command": "' 이다.
#   2) [[ =~ ]] 안에 정규식을 직접 쓰면 백슬래시 이스케이프가 소실된다 — 변수에 담아야 한다.
#   판정 대상은 JSON 원문이고, 그 안에서 따옴표는 \" 로 이스케이프돼 있다.

read -r -d '' INPUT

# 값비싼 정규식 전에 내장 글롭으로 1차 필터 (대부분의 명령은 여기서 빠진다)
case "$INPUT" in
  *start*cmd*|*START*CMD*|*Start*Cmd*) ;;
  *) exit 0 ;;
esac

shopt -s nocasematch
# start \"...\" cmd  — JSON 이스케이프된 따옴표를 포함한 형태
RE='start[[:space:]]+\\"[^\]*\\"[[:space:]]+cmd'
if [[ "$INPUT" =~ $RE ]]; then
  echo "BLOCKED: 'start' 명령어로 보이는 CMD 창을 띄우려 합니다. run_in_background 를 사용하세요." >&2
  # PreToolUse 차단 규약: exit 2 = 차단 + stderr 를 Claude 에 전달.
  # exit 1 은 '비차단 에러' 로 취급돼 무시된다 — 이전 버전은 1 이라 차단되지 않았다.
  exit 2
fi
exit 0
