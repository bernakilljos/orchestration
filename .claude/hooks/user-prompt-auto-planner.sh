#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 메시지 받자마자 5단계 plan + MoE 자동 분류 강제 발동.
# 1) Trigger 키워드 감지 → 5단계 의무 systemMessage 주입
# 2) classify-task.py 자동 호출 → 최적 AI 결정 → Claude 에 가이드 주입
# 사용자 액션 0 (Zero-touch). Codex/Gemini 자동 dispatch 가이드 포함.
set -e
INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  PROMPT="$(echo "$INPUT" | jq -r '.prompt // ""' 2>/dev/null | head -c 1000)"
else
  PROMPT="$(echo "$INPUT" | grep -oE '"prompt"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/' | head -c 1000)"
fi

# trigger 키워드 — 작업 지시·결함 지적·점검 요청 (한글 트리거 포함)
TRIGGER_RE='해줘|고쳐줘|확인|점검|왜|뭐야|되니|되네|안돼|안되|작네|크네|짤려|짤린|짤림|잘림|여백|여전|넘쳐|안보|글씨|보여야|잘되|잘됨|잘하|부족|틀렸|틀린|발동|농땡이|전수조사|정신|회피|딴말|무시|또|놓쳤|fix|build|verify|check|review|test|update|add|change|왜이리'

if echo "$PROMPT" | grep -qE "$TRIGGER_RE"; then
  # MoE 자동 분류 — 사용자 메시지 → 최적 AI 결정
  PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
  CLASSIFIER="$PROJECT_ROOT/.claude/scripts/classify-task.py"
  AI="claude"
  REASON="기본"
  if [ -f "$CLASSIFIER" ]; then
    CLASSIFY_RESULT="$(PYTHONIOENCODING=utf-8 LANG=en_US.UTF-8 echo "$PROMPT" | PYTHONIOENCODING=utf-8 python "$CLASSIFIER" 2>/dev/null || echo '{}')"
    AI_PARSED="$(echo "$CLASSIFY_RESULT" | grep -oE '"ai"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([a-z]*\)"$/\1/')"
    [ -n "$AI_PARSED" ] && AI="$AI_PARSED"
    REASON_PARSED="$(echo "$CLASSIFY_RESULT" | grep -oE '"reason"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/')"
    [ -n "$REASON_PARSED" ] && REASON="$REASON_PARSED"
  fi

  case "$AI" in
    codex)   GUIDE="[MoE 자동] codex 위임 권장 ($REASON). 자동 dispatch: python .claude/scripts/auto-dispatch.py" ;;
    gemini)  GUIDE="[MoE 자동] Gemini Flash 권장 ($REASON). gemini-auto 워커 활용" ;;
    haiku)   GUIDE="[MoE 자동] Haiku 권장 ($REASON). haiku-auto 워커 활용" ;;
    *)       GUIDE="[MoE 자동] Claude 직접 처리 ($REASON)" ;;
  esac

  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[auto-planner ENFORCED]\n사용자 메시지에 작업 지시·결함 지적·점검 키워드 감지. 5단계 의무 발동:\n1) 전수조사 — 인접 시스템·전역까지 모든 위치 훑기 (단일 후보로 결론 X)\n2) 분석 — diff/md5sum/본문으로 내용 검증 (파일명만 보고 단정 X)\n3) 실행 — 발견한 문제를 코드로 수정\n4) 확인 — 자동 검증 (verify-image-fit / verify-docx-pages / verify-docx-structure / verify-ppt-overflow) 발동·PASS 확인\n5) 보고 — 표·목록으로 결과 + 남은 결정사항\n\n금기:\n- 부분 처리 (한 파일만 보고 답변)\n- 검증 X 하고 완료 보고\n- 사용자에게 결정 떠넘기기 (크리티컬 5가지 외)\n- 회피·딴말 (직접 답 → 부연 → 행동)\n- 매번 사용자 지시 기다림 (auto-planner 자동 발동)\n\n자동 발동 트리거: auto-planner.md skill\n\n${GUIDE}"}}
EOF
fi

exit 0
