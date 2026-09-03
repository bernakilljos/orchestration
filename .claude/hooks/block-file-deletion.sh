#!/usr/bin/env bash
# block-file-deletion.sh — PreToolUse Bash hook
# 목적: plugins/ 또는 .claude/scripts/ 내 파일 삭제 차단 (명분 필수)
# 규칙: feedback_no_delete_without_justification.md

set -uo pipefail

# stdin 에서 tool_input 읽기
INPUT=$(cat 2>/dev/null || echo '{}')

# command 추출 (간단 regex 파싱)
CMD=$(echo "$INPUT" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)

# 명령어 없으면 skip
[ -z "$CMD" ] && exit 0

# --force-delete 플래그로 사용자 명시 확인
HAS_FORCE=false
if echo "$CMD" | grep -q '\-\-force-delete'; then
  HAS_FORCE=true
fi

# plugins/ 디렉토리 삭제 감지 (rm -rf plugins/ 또는 rm -r plugins/ 등)
if echo "$CMD" | grep -E 'rm\s+.*(-r|-f|--recursive|--force).*plugins/|rm\s+.*plugins/.*(-r|-f|--recursive|--force)' > /dev/null 2>&1; then
  if [ "$HAS_FORCE" = false ]; then
    cat <<'MSG'

[X] [BLOCK] plugins/ 파일 삭제 명령 감지!

  규칙: "명분 없이는 지우지 마" (feedback_no_delete_without_justification.md)

  orchestration_v1 은 template kit. 기존 파일은 명분 없이 삭제 금지.

  허용하는 명분 (3가지 중 하나):
  1. 사용자 명시:        "X 파일 지워줘"
  2. 분석-검증:         md5sum-diff-grep 결과로 확정
  3. git deprecated:    commit message + replacement merged

  우회 방법: rm --force-delete ...

  상세: feedback_no_delete_without_justification.md

MSG
    exit 2
  fi
fi

# .claude/scripts/ 내 파일 삭제 감지
if echo "$CMD" | grep -E 'rm\s+.*(-r|-f|--recursive|--force).*\.claude/scripts/|rm\s+.*\.claude/scripts/.*(-r|-f|--recursive|--force)' > /dev/null 2>&1; then
  if [ "$HAS_FORCE" = false ]; then
    cat <<'MSG'

[X] [BLOCK] .claude/scripts/ 파일 삭제 명령 감지!

  규칙: .claude 체계 파일은 명분 없이 삭제 금지

  허용하는 명분 (3가지 중 하나):
  1. 사용자 명시
  2. 분석-검증 (md5sum-diff)
  3. git deprecated + replacement merged

  우회 방법: rm --force-delete ...

  상세: .claude/rules/cleanup-policy.md

MSG
    exit 2
  fi
fi

exit 0
