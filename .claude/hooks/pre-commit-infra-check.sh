#!/usr/bin/env bash
# pre-commit-infra-check.sh — git commit 시 plugins/hooks/scripts 변경인데
# guide.txt-setup-CLAUDE.md 미변경이면 commit 차단
#
# 등록: PreToolUse Bash matcher 에서 git commit 감지 시 실행
# 또는: .git/hooks/pre-commit 에 직접 등록

set -uo pipefail

# stdin 에서 tool_input 읽기 (PreToolUse hook 용)
INPUT=$(cat 2>/dev/null || echo '{}')
CMD=$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//;s/"$//' 2>/dev/null || echo "")

# git commit 명령이 아니면 skip
echo "$CMD" | grep -qE 'git\s+commit' || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 0

# staged 파일 목록
STAGED=$(git diff --cached --name-only 2>/dev/null)

# plugins/hooks/scripts 변경 여부 (grep -c 는 0건이어도 '0' 을 찍는다 — 예전 `|| echo 0` 이 '0 0' 을 만들어 [ -eq ] 가 깨지고 늘 통과했다, 2026-10-16)
INFRA=$(echo "$STAGED" | grep -cE '^(plugins/|\.claude/hooks/|\.claude/scripts/|setup/)')

if [ "$INFRA" -eq 0 ]; then
  exit 0  # 인프라 변경 없으면 pass
fi

# guide.txt 또는 CLAUDE.md 포함 여부
DOCS=$(echo "$STAGED" | grep -cE '^(guide\.txt|CLAUDE\.md|setup/BUILD\.md)')

if [ "$DOCS" -eq 0 ]; then
  cat >&2 <<'MSG'

[X] [BLOCK] plugins/hooks/scripts 변경 감지 — guide.txt-CLAUDE.md 미포함!

  배포용 솔루션 규칙: 기능 변경과 문서 갱신은 같은 커밋에.

  다음 파일 중 하나 이상 같이 stage 하세요:
    - guide.txt (§6-§12-§17)
    - CLAUDE.md (상태 라인)
    - setup/BUILD.md (모듈 설명)

  bugfix 라도 guide.txt 해당 절에 한 줄(무엇이 왜 바뀌었나) 을 적고 같이 stage 한다 — --no-verify 금지.

MSG
  exit 2  # block
fi

exit 0
