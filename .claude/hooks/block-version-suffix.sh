#!/usr/bin/env bash
# block-version-suffix.sh — PreToolUse Write hook
# 목적: 산출물 파일명에 -v2, -v3, _v2 등 버전 접미사 추가 차단
# 규칙: feedback_no_version_suffix.md / CLAUDE.md § 7-14

set -uo pipefail

# stdin 에서 tool_input 읽기
INPUT=$(cat 2>/dev/null || echo '{}')

# file_path 추출 (간단 regex 파싱)
FILE_PATH=$(echo "$INPUT" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

# 파일 경로 없으면 skip
[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH" 2>/dev/null || echo "")
[ -z "$BASENAME" ] && exit 0

# 버전 접미사 패턴 감지: -v2, -v3, _v2 등
# 단순 검색: -v[0-9], _v[0-9] 패턴
if echo "$BASENAME" | grep -i '\-v[0-9]\|_v[0-9]' > /dev/null 2>&1; then
  # 실제 산출물 확장자 확인 (docx/pptx/pdf/xlsx + 매뉴얼 md/txt/html/rst/adoc/ipynb)
  # 근거: 2026-08-12 사용자 지적 — "매뉴얼이든 뭐든 v20 까지 간다"
  if echo "$BASENAME" | grep -iE '\.(docx|pptx|pdf|xlsx|doc|ppt|md|txt|html|rst|adoc|ipynb)$' > /dev/null 2>&1; then
    cat <<'MSG'

[X] [BLOCK] 산출물 버전 접미사 감지!

  규칙: 빌드 결과물 (.docx/.pptx/.pdf 등) 에 -v2, -v3, _v2 자동 추가 금지

  금지:   report-v2.docx, slides_v3.pptx
  허용:   report.docx (원본 덮어쓰기), report.docx.bak (백업)

  방법:
  1. 파일 잠겨있으면 -> 사용자에게 알림 ("원본 닫아주세요")
  2. 파일 접근 가능하면 -> .bak 백업 후 원본 자리에 덮어쓰기
  3. 버전은 사용자 명시 요청 시만

  상세: .claude/rules/teaching-doc.md § 산출물 명명
         feedback_no_version_suffix.md

MSG
    exit 2  # block
  fi
fi

exit 0
