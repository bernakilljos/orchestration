#!/bin/bash
# 꼼수 차단 — Edit 도구가 한글 라인을 영어로 변환할 때 차단
# 사용자 명시 지시 없이 한글 → 영어 변환 시도하면 PreToolUse 에서 거부.
#
# 우회: 환경변수 ALLOW_KOREAN_REMOVAL=1 설정 (사용자가 명시 동의 시)

set -e

# stdin 으로 hook input json 읽기 (PreToolUse 매개변수)
input=$(cat 2>/dev/null || echo "{}")

# 우회 옵션
if [ "${ALLOW_KOREAN_REMOVAL:-0}" = "1" ]; then
  exit 0
fi

# Edit 의 old_string 과 new_string 추출 (jq 있으면)
if command -v jq >/dev/null 2>&1; then
  tool=$(echo "$input" | jq -r '.tool_name // ""')
  if [ "$tool" != "Edit" ]; then
    exit 0
  fi
  old=$(echo "$input" | jq -r '.tool_input.old_string // ""')
  new=$(echo "$input" | jq -r '.tool_input.new_string // ""')
else
  exit 0
fi

# 한글 char 카운트 (Python 우회 - grep regex 안전성 문제 회피)
count_korean() {
  python -c "import sys,re; print(len(re.findall(r'[가-힣]', sys.argv[1])))" "$1" 2>/dev/null || echo 0
}
old_kr=$(count_korean "$old")
new_kr=$(count_korean "$new")

# 한글 글자 수 줄어들면 차단
if [ "${old_kr:-0}" -gt 0 ] && [ "${new_kr:-0}" -lt "${old_kr:-0}" ]; then
  echo "[BLOCK] 한글 보존 위반 — old 에 한글 ${old_kr}줄, new 에 ${new_kr}줄" >&2
  echo "       사용자가 명시적으로 한글 → 영어 변환을 요청하지 않은 한 거부됩니다." >&2
  echo "       우회: ALLOW_KOREAN_REMOVAL=1 환경변수 설정 후 재시도" >&2
  exit 1
fi

exit 0
