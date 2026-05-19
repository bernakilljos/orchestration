#!/usr/bin/env bash
# detect-deflection.sh — UserPromptSubmit
# 사용자가 "농땡이 / 짤려 / 안 보여 / 다시 / 또" 같은 패턴 반복 = Claude 회피·룰 위반 신호
#
# 룰: failure-mode.md § 회피 안티패턴, feedback_nongttaengi_means_full_survey.md
#
# 동작:
#   1. 사용자 메시지에서 회피 신호 키워드 grep
#   2. 최근 10개 prompt 에서 같은 카테고리 반복 → 누적 위반
#   3. 위반 감지 → systemMessage 로 Claude 자가 점검 알림 (PASS through, 차단 X)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/deflection-detect.log"
HISTORY="${LOG_DIR}/user-prompt-history.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# user_message 추출
if command -v jq >/dev/null 2>&1; then
  MSG=$(echo "$INPUT" | jq -r '.prompt // .user_message // empty' 2>/dev/null)
else
  MSG=$(echo "$INPUT" | grep -oE '"(prompt|user_message)"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

[ -z "$MSG" ] && exit 0

# 누적 prompt 기록 (10개 회전)
echo "[$(date +%F_%T)] $MSG" >> "$HISTORY"
tail -n 30 "$HISTORY" > "${HISTORY}.tmp" && mv "${HISTORY}.tmp" "$HISTORY"

# 회피·반복 위반 신호 카테고리
declare -A SIGNALS=(
  [overflow_jal]="짤려|짤린|잘림|넘쳐|넘치"
  [text_too_small]="작은데|글씨.*안 ?보여|작아|크게"
  [whitespace]="빈 ?여백|공간.*많|허전"
  [repeat]="다시|또|반복|왜 자꾸|계속|왜이리"
  [nongttaengi]="농땡이|정신.*차|안되니|왜 안"
  [rule_violation]="룰.*위반|규칙.*어겨|전수조사|체크리스트"
  [wrong]="틀렸|잘못|아니야|아닌데|왜 그래"
  [no_show]="안 ?보여|안 ?나와|안 ?돼"
)

MATCHED=""
for cat in "${!SIGNALS[@]}"; do
  pattern="${SIGNALS[$cat]}"
  if echo "$MSG" | grep -qE "$pattern"; then
    MATCHED="$MATCHED $cat"
  fi
done

if [ -n "$MATCHED" ]; then
  # 최근 10 prompt 에서 같은 카테고리 반복 카운트
  COUNT=0
  for cat in $MATCHED; do
    pattern="${SIGNALS[$cat]}"
    c=$(tail -n 10 "$HISTORY" | grep -cE "$pattern" || echo 0)
    COUNT=$((COUNT + c))
  done

  echo "[$(date +%F_%T)] MATCHED:$MATCHED | recent_count=$COUNT | msg=$MSG" >> "$LOG"

  if [ "$COUNT" -ge 3 ]; then
    # 3번 이상 반복 = 명백한 신호
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "⚠️ 회피·반복 위반 패턴 감지: $MATCHED (최근 10 prompt 중 $COUNT 회). failure-mode.md § 회피 안티패턴 / feedback_nongttaengi_means_full_survey.md 점검. 사용자 직답 → 부연 → 행동 순서로. 5단계 전수조사 필수."
  }
}
EOF
  else
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "🔍 사용자 신호 감지: $MATCHED. 룰 위반 가능성. 단순 응답 X, 원인 점검 후 행동."
  }
}
EOF
  fi
fi

exit 0
