#!/bin/bash
# Hook: PostToolUse — HTML 템플릿에 영어 UI 텍스트 감지
# 코드(class, id, attribute)는 무시, 사용자에게 보이는 텍스트만 체크
#
# 성능 (2026-09-02): 매 Edit/Write 마다 돈다. 대상(templates/*.html)이 아니면
#   서브프로세스 0개로 즉시 종료한다. 이 프로젝트에는 templates/*.html 이 0개라
#   실질적으로 항상 즉시 종료 경로다.
#
# 정확성 (2026-09-02 수정): 이전 버전은 '"file_path":"' (콜론 뒤 공백 없음) 만
#   찾았으나 실제 payload 는 '"file_path": "' 이다 — FILEPATH 가 항상 빈 문자열이라
#   검사가 한 번도 돌지 않았다.

read -r -d '' INPUT

# 1차 필터: 내장 글롭. templates 경로가 없으면 즉시 종료.
case "$INPUT" in
  *templates*) ;;
  *) exit 0 ;;
esac

# file_path 추출 — 콜론 뒤 공백 유무 무관
FILEPATH="${INPUT#*\"file_path\":}"
FILEPATH="${FILEPATH#\"}"
FILEPATH="${FILEPATH# \"}"
FILEPATH="${FILEPATH%%\"*}"


case "$FILEPATH" in
  *templates*.html) ;;
  *) exit 0 ;;
esac
[ -f "$FILEPATH" ] || exit 0

ENGLISH_PATTERNS="Dashboard|Total Assets|Invested|Settings|Loading|No data|Submit|Cancel|Save|Delete|Search|Filter|Community|Bookmark|Wishlist|Hot Deals|Coupons|Compare|Alerts|Goal|Trend"

FOUND=$(grep -oE ">($ENGLISH_PATTERNS)<" "$FILEPATH" 2>/dev/null | head -5)
if [ -n "$FOUND" ]; then
  echo "WARNING: 영어 UI 텍스트 발견 — 한국어로 변경 필요: $FOUND" >&2
  echo "한국어 전용 플랫폼입니다. 영어 UI 텍스트를 한국어로 바꿔주세요." >&2
fi
exit 0
