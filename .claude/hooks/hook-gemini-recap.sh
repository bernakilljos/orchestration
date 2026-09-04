#!/bin/bash
# hook-gemini-recap.sh — SessionEnd 시 Gemini 에게 요약 위임
#
# 트리거: SessionEnd (async, non-blocking)
# 조건: gemini-a 가용 + 세션 로그 존재
# 결과: .claude/state/recap.jsonl append
#
# 주의: Gemini 워커 없으면 조용히 skip (Claude 대행 금지)

set -uo pipefail

REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
STATE_DIR="$REPO_ROOT/.claude/state"
RECAP="$STATE_DIR/recap.jsonl"
mkdir -p "$STATE_DIR"

# stdin 파싱 (session_id 등)
INPUT=$(cat 2>/dev/null || echo '{}')
session_id=$(echo "$INPUT" | python -c "
import json, sys
try:
  sys.stdout.reconfigure(encoding='utf-8')
  sys.stdin.reconfigure(encoding='utf-8')
except: pass
try:
  d = json.load(sys.stdin)
  print(d.get('session_id', 'unknown'))
except: print('unknown')
" 2>/dev/null || echo "unknown")

# Gemini 가용성 체크
if ! command -v gemini-a >/dev/null 2>&1 && ! command -v gemini-auto >/dev/null 2>&1; then
  # Gemini 없음 -> skip (Claude 대행 금지)
  echo '{"continue": true}'
  exit 0
fi

# Quota 체크
if [ -f "$STATE_DIR/gemini-quota-exceeded" ]; then
  echo '{"continue": true}'
  exit 0
fi

# 비동기 요약 태스크 생성
ts=$(date -u +%Y%m%d-%H%M%S)
TASK_FILE="$REPO_ROOT/.claude/tasks/recap-$ts.md"
mkdir -p "$(dirname "$TASK_FILE")"

cat > "$TASK_FILE" <<EOF
---
role: gemini
type: recap
session_id: $session_id
format: detailed
output: $RECAP
created: $(date -u +%Y-%m-%dT%H:%M:%SZ)
---

# 세션 요약 요청

**대상**: 세션 $session_id 의 주요 활동-결정-결과
**형식**: 10~15줄 (detailed)
**저장**: \`$RECAP\` 에 JSON Lines 1줄 append:
\`\`\`json
{"ts":"...","session":"$session_id","type":"session_end","summary":"...","key_actions":[...],"commits":[...]}
\`\`\`

**추출 대상**:
- 주요 변경 파일
- 커밋 메시지 (git log)
- 사용자 요구 사항 핵심
- 미해결 사항

Claude 대행 금지. Gemini 가 직접 작성.
EOF

# 비동기 실행 (hook timeout 이슈 회피)
if command -v orca-dispatch >/dev/null 2>&1; then
  orca-dispatch "$TASK_FILE" gemini >/dev/null 2>&1 &
fi

echo '{"continue": true, "systemMessage": "[recap] Gemini 요약 태스크 투입됨"}'
