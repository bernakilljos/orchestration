#!/usr/bin/env bash
# statusline — 매 turn 상태바에 대상(scope) 상시 표시
# 근거: .claude/rules/direction-first.md · feedback_confirm_target_first.md
# 목적: Claude·사용자 모두 매 turn 마다 "지금 어느 대상 손대는지" 확인
# 하드코딩 X — CLAUDE.md § 7-A1 · 컴퓨터마다 경로 다름
# 판정 기준: **스크립트 자체 위치** (BASH_SOURCE) — CLAUDE_PROJECT_DIR 환경변수 override 방지
set -e

# 스크립트 위치 = 실제 kit/target 폴더 (CLAUDE_PROJECT_DIR 무관)
SCRIPT_LOC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || echo "")"
# .claude/statusline.sh 위치 → 상위 폴더가 실제 프로젝트 root
CWD="$(cd "$SCRIPT_LOC/.." 2>/dev/null && pwd 2>/dev/null || echo "${CLAUDE_PROJECT_DIR:-$PWD}")"
BASE="$(basename "$CWD" 2>/dev/null || echo "")"

# 대상 판정 (4갈래) — 하드코딩 X, marker 파일·상대 위치 기반
scope=""

# 글로벌 ~/.claude 판정 (HOME/USERPROFILE 환경변수 사용)
HOME_CLAUDE="${HOME:-$USERPROFILE}/.claude"
case "$CWD" in
  "$HOME_CLAUDE"|"$HOME_CLAUDE/"*)
    scope="[GLOBAL] ~/.claude"
    ;;
esac

# kit 자체 판정 — .claude/.is-kit-root marker 파일 (kit 만 있음, sync-team 제외)
# 근거: .claude-plugin/plugin.json 은 install 시 target 에도 복사됨 → 판정 오류. .is-kit-root 만 kit 전용
if [ -z "$scope" ] && [ -f "$CWD/.claude/.is-kit-root" ]; then
  scope="[KIT] $BASE (감사·리팩터)"
fi

# setup/templates 판정 (상대 경로 · basename+parent 조합)
if [ -z "$scope" ]; then
  PARENT="$(basename "$(dirname "$CWD")" 2>/dev/null || echo "")"
  GPARENT="$(basename "$(dirname "$(dirname "$CWD")")" 2>/dev/null || echo "")"
  if [ "$BASE" = "templates" ] && [ "$PARENT" = "setup" ] && [ -f "$GPARENT/.claude-plugin/plugin.json" 2>/dev/null ] || \
     [ "$BASE" = "templates" ] && [ "$PARENT" = "setup" ]; then
    scope="[SETUP] 배포용 template"
  fi
fi

# target 판정 — kit marker 는 없지만 CLAUDE.md 또는 .claude/ 있음
if [ -z "$scope" ]; then
  if [ -f "$CWD/CLAUDE.md" ] || [ -d "$CWD/.claude" ]; then
    scope="[TARGET] install 대상 실운영: $BASE"
  else
    scope="[?] 미판정 — 대상 확정 필요"
  fi
fi

# 사용자 지정 override (.claude/state/current-target 파일)
OVERRIDE_FILE="$CWD/.claude/state/current-target"
if [ -f "$OVERRIDE_FILE" ]; then
  ov=$(cat "$OVERRIDE_FILE" 2>/dev/null | head -1 | tr -d '\r\n')
  [ -n "$ov" ] && scope="[OVERRIDE] $ov"
fi

# 카운터
CTR_FILE="$CWD/.claude/state/.prompt-counter"
ctr=$([ -f "$CTR_FILE" ] && cat "$CTR_FILE" 2>/dev/null | tr -d '[:space:]' || echo 0)

# 상태바 한 줄 (Claude Code statusLine 규격)
echo "$scope · turn#$ctr · $(basename "$CWD")"
