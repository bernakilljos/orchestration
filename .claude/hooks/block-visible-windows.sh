#!/bin/bash
# Hook: PreToolUse(Bash) — 세션이 보이는 창(CMD·PowerShell·서버 콘솔)을 띄우는 것을 **띄우기 전에** 막는다 (예방).
#
# 2026-10-14 사용자: "다른 섹션에서 테스트했으면 닫아 · 예방을 하라고". 세션들이 검증하며
#   bat 을 돌렸고, bat **안의** start 줄이 서버 콘솔 창을 열어 둔 채 남겼다.
# 판정 정본: .claude/hooks/tool/block_visible_windows.py (tool-dispatch.py 가 in-process 로 부른다).
#   이 파일은 settings 에 직접 걸 때 쓰는 껍데기다 — 판정을 여기 다시 쓰지 않는다
#   (2026-10-25 사이클 881: 두 벌이던 때 637 은 한쪽만 고쳐졌고, 881 의 '읽기 명령 인자 오탐' 도 두 벌 다 있었다).
# 성능: 무관 명령은 bash 내장만으로 즉시 종료 (프로세스 0개).

read -r -d '' INPUT || true

# 1차 필터 — 창을 열 수 있는 단어가 없으면 즉시 통과
case "$INPUT" in
  *start*|*START*|*Start*|*'cmd /k'*|*'cmd //k'*|*.bat*|*.BAT*|*.cmd*|*.ps1*) ;;
  *) exit 0 ;;
esac
case "$INPUT" in *ALLOW_VISIBLE_WINDOW=1*) exit 0 ;; esac

HOOKS="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python || command -v python3)"
[ -n "$PY" ] || exit 0
printf '%s' "$INPUT" | PYTHONPATH="$HOOKS/prompt" "$PY" -X utf8 "$HOOKS/tool/block_visible_windows.py"
exit $?
