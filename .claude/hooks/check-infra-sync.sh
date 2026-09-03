#!/usr/bin/env bash
# check-infra-sync.sh — Stop hook: plugins/hooks/scripts 변경 시 guide.txt-setup 갱신 여부 점검
# 목적: "매번 개선 시 install/setup/guide.txt 전수조사" 메모리 자동 강제
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR" || exit 0

# 이번 세션에서 수정된 파일 (staged + unstaged + untracked)
CHANGED=$(git diff --name-only HEAD 2>/dev/null; git diff --cached --name-only 2>/dev/null)

# plugins / hooks / scripts 변경 여부
INFRA_CHANGED=false
echo "$CHANGED" | grep -qE '^(plugins/|\.claude/hooks/|\.claude/scripts/)' && INFRA_CHANGED=true

if [ "$INFRA_CHANGED" = "false" ]; then
  exit 0  # 인프라 변경 없으면 skip
fi

# guide.txt / setup / CLAUDE.md 도 변경됐는지
GUIDE_UPDATED=false
echo "$CHANGED" | grep -qE '^(guide\.txt|setup/|CLAUDE\.md)' && GUIDE_UPDATED=true

if [ "$GUIDE_UPDATED" = "false" ]; then
  cat <<'MSG'

[WARN] [check-infra-sync] plugins/hooks/scripts 변경 감지 — guide.txt-setup 미갱신!

  배포용 솔루션 규칙: 기능 추가마다 install-setup-guide.txt 함께 갱신 필수.
  다음 세션에서 반드시 갱신:
  1. guide.txt § 6-12-17
  2. setup/modules/01-core.bat sanity check
  3. CLAUDE.md 상태 라인

MSG
fi

exit 0
