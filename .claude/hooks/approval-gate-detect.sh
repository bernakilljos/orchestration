#!/usr/bin/env bash
# approval-gate-detect.sh — PreToolUse Bash matcher
# 위험 명령 감지 -> approval-gate.py request 등록 (CLAUDE.md § 7-23)
#
# 5 위험 카테고리: data_loss / security / cost / system / irreversible
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/approval-gate.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# stdin — bash 내장 (cat·jq·grep·sed 프로세스 0개)
# 2026-10-14: 종전엔 Bash 명령마다 python 을 띄웠다(실측 1회 2~4초). 이 PC 는 느려 hook 이 시간 초과로
#   끊기면 Windows 에선 bash 만 죽고 python 이 남아 좀비 51개가 최대 12일 쌓였다 (전부 인자 'cd \' —
#   grep 폴백이 JSON 의 \" 에서 명령을 잘랐다). → 위험 단어가 없으면 python 을 아예 띄우지 않는다.
read -r -d '' INPUT || true
[ -z "$INPUT" ] && exit 0

# 1차 필터 — approval-gate.py RISK_PATTERNS 의 핵심 단어 (하나도 없으면 위험 명령일 수 없다)
shopt -s nocasematch
RE_RISKWORD='drop|truncate|delete|rm[[:space:]]|git[[:space:]]+(push|reset|branch)|sudo|curl|wget|runas|chmod|batch|daily-limit|setx|reg[[:space:]]+(add|delete)|alembic|systemctl|npm[[:space:]]+publish|docker[[:space:]]+push|gh[[:space:]]+release|terraform'
[[ $INPUT =~ $RE_RISKWORD ]] || exit 0
shopt -u nocasematch

# command 추출 — 콜론 뒤 공백 유무 무관 · JSON 이스케이프(\" \\) 복원 (종전 grep 폴백은 \" 에서 잘렸다)
CMD="${INPUT#*\"command\":}"; CMD="${CMD#\"}"; CMD="${CMD# \"}"
CMD="${CMD%%\", \"*}"; CMD="${CMD%%\",\"*}"; CMD="${CMD%%\"\}*}"
CMD="${CMD//\\\"/\"}"; CMD="${CMD//\\\\/\\}"
[ -z "$CMD" ] && exit 0

GATE="${PROJECT_ROOT}/.claude/scripts/approval-gate.py"
[ -f "$GATE" ] || exit 0

# detect — JSON 출력 또는 빈 출력
PY=$(cat "${PROJECT_ROOT}/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n') || PY=python
DETECT_JSON=$("${PY:-python}" "$GATE" detect "$CMD" 2>>"$LOG" || echo "")

# JSON 비어있거나 null 이면 통과
if [ -z "$DETECT_JSON" ] || [ "$DETECT_JSON" = "null" ] || [ "$DETECT_JSON" = "{}" ]; then
  exit 0
fi

# category / description 추출
if command -v jq >/dev/null 2>&1; then
  CATEGORY=$(echo "$DETECT_JSON" | jq -r '.category // empty' 2>/dev/null)
  DESC=$(echo "$DETECT_JSON" | jq -r '.description // empty' 2>/dev/null)
else
  CATEGORY=$(echo "$DETECT_JSON" | grep -oE '"category"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  DESC=$(echo "$DETECT_JSON" | grep -oE '"description"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

[ -z "$CATEGORY" ] && exit 0

# task_id 생성 (cmd sha 앞 12자)
TASK_ID="appr-$(echo -n "$CMD$(date +%s)" | sha256sum 2>/dev/null | cut -c1-12)"
[ -z "$TASK_ID" ] || [ "$TASK_ID" = "appr-" ] && TASK_ID="appr-$(date +%s)"

# request 등록 (4 인자: task_id, command, category, detail)
"${PY:-python}" "$GATE" request "$TASK_ID" "$CMD" "$CATEGORY" "$DESC" >>"$LOG" 2>&1 || true

echo "[$(date +%F_%T)] BLOCK: $CATEGORY | task_id=$TASK_ID | cmd=$CMD" >> "$LOG"

cat >&2 <<EOF
{
  "decision": "block",
  "reason": " 위험 명령 감지 ($CATEGORY): $DESC. /approve $TASK_ID 또는 /reject $TASK_ID [reason]",
  "systemMessage": "HITL Approval Gate — task_id=$TASK_ID | category=$CATEGORY | /approve <id> 로 승인 후 진행"
}
EOF
exit 2
