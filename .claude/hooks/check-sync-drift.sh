#!/usr/bin/env bash
# SessionStart hook — sync-workflow rule 강제 자동 점검
# plugins/ ↔ .claude/ drift / orphan 백그라운드 로그
# 실패해도 차단 안 함 (informational only)
set +e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
LOG_FILE="$LOG_DIR/sync-drift.log"
SYNC_SCRIPT="$PROJECT_ROOT/.claude/scripts/sync-plugins.sh"

[ -f "$SYNC_SCRIPT" ] || exit 0
mkdir -p "$LOG_DIR" 2>/dev/null

# 2026-11-03: $RESULT (Windows 경로의 \a·\p · 줄바꿈 원문) 를 JSON 문자열에 그대로 끼워 'Invalid \escape' 가 났다.
#   JSON 인코더 (python json.dumps) 로 전체 내용을 인코딩 · python 이 없으면 sed 로 같은 escape (내용 생략 X).
emit_system_message() {
  local py
  py=$(cat "$PROJECT_ROOT/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n')
  if MSG="$1" "${py:-python}" -X utf8 -c 'import json,os,sys; sys.stdout.write(json.dumps({"systemMessage": os.environ["MSG"]}, ensure_ascii=False) + "\n")' 2>/dev/null; then
    return 0
  fi
  printf '{"systemMessage": "%s"}\n' "$(printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' -e 's/\r//g' | sed -e ':a;N;$!ba;s/\n/\\n/g')"
}

TS="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
RESULT="$(bash "$SYNC_SCRIPT" --check 2>&1 | tail -10)"

# drift 또는 orphan 감지 시 systemMessage (informational)
if echo "$RESULT" | grep -qE "drift.*[1-9]|orphan.*[1-9]"; then
  emit_system_message "[sync-drift] plugins/ <-> .claude/ 드리프트-orphan 감지 — bash .claude/scripts/sync-plugins.sh 권장:
$RESULT"
  echo "[$TS] DRIFT|ORPHAN detected" >> "$LOG_FILE"
  echo "$RESULT" >> "$LOG_FILE"
else
  echo "[$TS] clean" >> "$LOG_FILE"
fi
exit 0
