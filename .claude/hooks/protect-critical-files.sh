#!/bin/bash
# Hook: PreToolUse — Edit|Write 차단
# config.py, settings.json, main.py 등 핵심 파일 보호
# codex/gemini가 실수로 수정/삭제하는 것 방지
#
# 성능 (2026-09-02 실측): 매 편집마다 돈다. cat + grep + cut + sed 파이프로
#   1245ms 였다 (Windows + Privacy-i DLP 에서 프로세스 생성 300~400ms).
#   bash 내장만 써서 서브프로세스를 0개로 만든다.
#
# 정확성 (2026-09-02 수정 — 중대): 이전 버전은
#     grep -o '"file_path":"[^"]*"'
#   로 값을 뽑았는데, 실제 hook payload 는 '"file_path": "..."' (콜론 뒤 공백) 이다.
#   그래서 FILE 이 **항상 빈 문자열**이었고 바로 아래 `[ -z "$FILE" ] && exit 0` 에
#   걸려서 나갔다 — config.py / .env / main.py 보호가 **한 번도 동작하지 않았다**.
#   (검증: config.py 편집 시 rc=0 통과. 수정 후 rc=2 차단.)

read -r -d '' INPUT || true

# ---- file_path 추출: 콜론 뒤 공백 유무 무관, 서브프로세스 0개 ----
case "$INPUT" in
  *'"file_path"'*) ;;
  *) exit 0 ;;
esac
FILE="${INPUT#*\"file_path\":}"
FILE="${FILE#\"}"
FILE="${FILE# \"}"
FILE="${FILE%%\"*}"
[ -n "$FILE" ] || exit 0

# ---- 경로 정규화: JSON 의 \\ 와 OS 의 \ 를 모두 / 로 (내장 치환) ----
NORM="${FILE//\\\\//}"   # \\ -> /
NORM="${NORM//\\//}"     # \  -> /
while [ "$NORM" != "${NORM//\/\//\/}" ]; do NORM="${NORM//\/\///}"; done

# ---- 예외: .claude/settings*.json 은 Claude 본인이 관리 ----
# (codex/gemini 는 외부 프로세스라 이 훅을 거치지 않으므로 워커 보호엔 영향 없음)
case "$NORM" in
  */.claude/settings.json|*/.claude/settings.local.json|\
  .claude/settings.json|.claude/settings.local.json)
    exit 0 ;;
esac

BASENAME="${NORM##*/}"

# ---- 보호 대상 ----
# basename 완전일치로만 판정한다. 이전 구현은 경로 부분일치(*pattern*)도 봐서
# 'deploy-config.env' 같은 패턴이 무관한 경로를 잡을 위험이 있었다.
case "$BASENAME" in
  config.py|settings.json|main.py|.env|.env.local|deploy-config.env)
    echo "BLOCKED: $BASENAME is a protected file. Do not modify." >&2
    exit 2 ;;
esac

exit 0
