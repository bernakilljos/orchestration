#!/bin/bash
# Hook: PostToolUse — HTML 템플릿에 영어 UI 텍스트 감지
# 코드(class, id, attribute)는 무시, 사용자에게 보이는 텍스트만 체크

INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | head -1 | sed 's/"file_path":"//;s/"$//')

# HTML 템플릿만 체크
if ! echo "$FILEPATH" | grep -q "templates/.*\.html$"; then
  exit 0
fi

# 영어 UI 텍스트 패턴 (사용자에게 보이는 것만)
ENGLISH_PATTERNS="Dashboard|Total Assets|Invested|Settings|Loading|No data|Submit|Cancel|Save|Delete|Search|Filter|Community|Bookmark|Wishlist|Hot Deals|Coupons|Compare|Alerts|Goal|Trend"

if grep -qP ">($ENGLISH_PATTERNS)<" "$FILEPATH" 2>/dev/null; then
  FOUND=$(grep -oP ">($ENGLISH_PATTERNS)<" "$FILEPATH" | head -5)
  echo "WARNING: 영어 UI 텍스트 발견 — 한국어로 변경 필요: $FOUND" >&2
  echo "한국어 전용 플랫폼입니다. 영어 UI 텍스트를 한국어로 바꿔주세요." >&2
  # 경고만, 차단하지 않음 (exit 0)
fi

exit 0
