#!/usr/bin/env bash
# UserPromptSubmit hook — 사용자 메시지 받자마자 5단계 plan + MoE 자동 분류 강제 발동.
# 1) Trigger 키워드 감지 -> 5단계 의무 systemMessage 주입
# 2) classify-task.py 자동 호출 -> 최적 AI 결정 -> Claude 에 가이드 주입
# 사용자 액션 0 (Zero-touch). Codex/Gemini 자동 dispatch 가이드 포함.
set -e
INPUT="$(cat)"

# prompt 추출. (A.RMS/A1 세션 개선본 역병합 2026-10-06)
#
# 2026-09-02 수정 (중대): jq 없는 환경(이 PC)의 fallback 이 두 가지로 깨져 있었다 —
#   ① sed 's/.*:"\(.*\)"/\1/' 가 키 이름을 남겨 결과가  "prompt": "..."  가 됐다.
#   ② JSON 은 한글을 \uXXXX 로 이스케이프해 보낸다. 그러면 아래 한글 TRIGGER_RE
#      (해줘|고쳐줘|점검 ...) 가 **원리적으로 절대 매치하지 않는다**.
#   결과: UserPromptSubmit 훅이 매 메시지마다 돌면서도 트리거를 한 번도 잡지 못했다.
#   → jq 유무와 무관하게 python 으로 파싱한다(이스케이프 자동 복원). python 은
#     이 프로젝트 훅 다수가 이미 의존하므로 새 의존성이 아니다.
PROMPT="$(printf '%s' "$INPUT" | PYTHONIOENCODING=utf-8 python -c "
import json, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
p = d.get('prompt') or ''
if not isinstance(p, str):
    p = str(p)
sys.stdout.write(p[:1000])
" 2>/dev/null || true)"


_m() { local re="$1"; [[ $PROMPT =~ $re ]]; }   # echo|grep fork 대신 bash 내장 (1006)

# trigger 키워드 — 작업 지시-결함 지적-점검 요청 (한글 트리거 포함)
TRIGGER_RE='해줘|고쳐줘|확인|점검|왜|뭐야|되니|되네|안돼|안되|작네|크네|짤려|짤린|짤림|잘림|잘리|짤리|여백|여전|넘쳐|안보|글씨|보여야|잘되|잘됨|잘하|부족|틀렸|틀린|발동|농땡이|전수조사|정신|회피|딴말|무시|또|놓쳤|fix|build|verify|check|review|test|update|add|change|왜이리|방지|보완|이미지|메모리|성능'

if _m "$TRIGGER_RE"; then
  # MoE 자동 분류 — 사용자 메시지 -> 최적 AI 결정
  PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
  CLASSIFIER="$PROJECT_ROOT/.claude/scripts/classify-task.py"
  AI="claude"
  REASON="기본"
  # 2026-10-06: 분류·키워드회상·RAG python 3개를 순차 실행(8.6s · 3초 timeout 초과)하던 것을 병렬로.
  #   프롬프트는 환경변수로 전달 (예전 RAG 는 bash -c "echo '$PROMPT'" 라 ' 하나로 깨지고 주입 가능했다)
  _TMP="$(mktemp -d 2>/dev/null || echo "${TMPDIR:-/tmp}/ap.$$")"; mkdir -p "$_TMP"
  RECALL_SCRIPT="$PROJECT_ROOT/.claude/scripts/recall-memory.py"
  RAG_SCRIPT="$PROJECT_ROOT/.claude/scripts/rag-recall.py"
  export AP_PROMPT="$PROMPT" PYTHONIOENCODING=utf-8
  [ -f "$CLASSIFIER" ]    && { printf '%s' "$AP_PROMPT" | python "$CLASSIFIER" > "$_TMP/cls" 2>/dev/null; } &
  [ -f "$RECALL_SCRIPT" ] && { printf '%s' "$AP_PROMPT" | python "$RECALL_SCRIPT" > "$_TMP/rec" 2>/dev/null; } &
  # RAG(의미 검색)는 동기 경로에서 뺀다 — 실측 1006: rag-recall.py 1회 17.5s (chromadb·임베딩 매번 로드)
  #   + Windows 에서 timeout 5 가 python 을 못 죽여 hook 전체가 3초 timeout 으로 폐기됐다 (RAG 결과는 0회 전달).
  #   → 백그라운드로 돌려 결과를 캐시에 쓰고, 다음 프롬프트에서 그 캐시를 읽는다 (창 없음 · 동시 1개).
  RAG_CACHE="$PROJECT_ROOT/.claude/state/rag-last.json"
  RAG_LOCK="$PROJECT_ROOT/.claude/state/rag-running"
  if [ -f "$RAG_SCRIPT" ] && [ ! -f "$RAG_LOCK" ]; then
    ( : > "$RAG_LOCK"; printf '%s' "$AP_PROMPT" | python "$RAG_SCRIPT" --top 3 > "$RAG_CACHE.tmp" 2>/dev/null         && mv -f "$RAG_CACHE.tmp" "$RAG_CACHE"; rm -f "$RAG_LOCK" ) >/dev/null 2>&1 &
    disown 2>/dev/null || true
  fi
  [ -f "$RAG_CACHE" ] && cp -f "$RAG_CACHE" "$_TMP/rag" 2>/dev/null
  wait
  CLASSIFY_RESULT="$(cat "$_TMP/cls" 2>/dev/null || echo '{}')"
  RECALL_JSON="$(cat "$_TMP/rec" 2>/dev/null || echo '[]')"
  RAG_JSON="$(cat "$_TMP/rag" 2>/dev/null || echo '[]')"
  rm -f "$_TMP/cls" "$_TMP/rec" "$_TMP/rag"; rmdir "$_TMP" 2>/dev/null
  if [ -n "$CLASSIFY_RESULT" ] && [ "$CLASSIFY_RESULT" != "{}" ]; then
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

  # Subagent 자동 가이드 — 큰 탐색/리뷰 키워드 감지 -> Task tool 권장
  SUBAGENT_GUIDE=""
  if _m '전수조사|전체.*탐색|전체.*검색|모든.*파일|모든.*폴더|코드베이스|whole.?code|grep.*all'; then
    SUBAGENT_GUIDE="\n\n[Subagent 자동] '큰 코드베이스 탐색' 감지 -> Task tool 로 Explore subagent 자동 호출 권장 (메인 컨텍스트 격리)"
  elif _m '리뷰|review|코드 검토|PR 검토'; then
    SUBAGENT_GUIDE="\n\n[Subagent 자동] '코드 리뷰' 감지 -> Task tool 로 code-reviewer subagent 자동 호출 권장"
  fi

  # Activation 로그 (background)
  LOG_ACT="$PROJECT_ROOT/.claude/scripts/log-activation.py"
  if [ -f "$LOG_ACT" ]; then
    (PYTHONIOENCODING=utf-8 python "$LOG_ACT" hook user-prompt-auto-planner "$PROMPT" --result success >/dev/null 2>&1) &
  fi

  # Memory 자동 recall — 키워드 (3-tier) + RAG 의미 검색 (위에서 병렬 실행한 결과 사용)
  MEMORY_GUIDE=""
  MEM_LINES="$(echo "$RECALL_JSON" | grep -oE '"description"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*: *"\(.*\)"$/- (kw) \1/' | head -3)"
  RAG_LINES="$(echo "$RAG_JSON" | grep -oE '"preview"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*: *"\(.*\)"$/- (rag) \1/' | head -2)"
  COMBINED="$(printf '%s\n%s' "$MEM_LINES" "$RAG_LINES" | sed '/^$/d')"
  if [ -n "$COMBINED" ]; then
    MEMORY_GUIDE="\n\n[Memory 자동 recall — kw=키워드 / rag=의미] 관련 학습 (재발 방지):\n$(echo "$COMBINED" | sed 's/$/\\n/' | tr -d '\n')"
  fi

  # Observability — decision log (alarm 은 별도 systemMessage 로 분리 가능. 일단 log만)
  LOG_SCRIPT="$PROJECT_ROOT/.claude/scripts/log-decision.py"
  ALARM_GUIDE=""
  if [ -f "$LOG_SCRIPT" ]; then
    MEM_COUNT="$(echo "$RECALL_JSON" | grep -c '"file"' || echo 0)"
    # 비동기 log (alarm 검출은 별도 query 도구 추가 가능)
    (echo "$PROMPT" | PYTHONIOENCODING=utf-8 python "$LOG_SCRIPT" --ai "$AI" --mem-hits "$MEM_COUNT" >/dev/null 2>&1) &
  fi

  # auto-compact 마커 체크 — 임계치 도달 시 NEXT TURN 첫 동작으로 /compact 강제
  # 2026-10-06: «auto-compact ENFORCED — Claude 가 /compact 자체 실행» 안내 제거.
  #   ① Claude 는 /compact·/clear 를 실행할 수 없다(사용자 입력창 전용) — 지킬 수 없는 지시였다.
  #   ② 마커는 «25턴마다» 생겨 토큰과 무관했다. 실측(compact 29건): 소요가 토큰에 비례하지 않아
  #      조기 compact 는 이득이 없다. 토큰 기준 안내는 inject-compact-reminder.sh 가 담당 (/clear 권장).
  COMPACT_GUIDE=""

  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[대상 확정 REQUIRED — 0순위]\n★ 첫 응답 첫 줄 형식 (매 지시 필수): 대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정\n★ 4갈래 후보:\n  1) ${PROJECT_ROOT} (kit 자체 감사-룰-hook)\n  2) ${PROJECT_ROOT}/setup/templates/ (install 배포용 template)\n  3) install 대상 실운영 프로젝트 (경로 물어봐 — 사용자가 '실운영'-'하드코딩 실측'-'재발 방지 헌장'-비즈니스 지표명 언급 시)\n  4) ~/.claude/ (글로벌 설정)\n★ 대상 확정 전 grep-Read-Edit-Bash 착수 = 룰 위반. 자동 후보 나열도 X 하고 kit 뒤지기 시작 = 재발.\n상세: .claude/rules/direction-first.md - feedback_confirm_target_first.md\n\n[auto-planner ENFORCED]\n사용자 메시지에 작업 지시-결함 지적-점검 키워드 감지. 5단계 의무 발동:\n1) 전수조사 — 인접 시스템-전역까지 모든 위치 훑기 (단일 후보로 결론 X)\n2) 분석 — diff/md5sum/본문으로 내용 검증 (파일명만 보고 단정 X)\n3) 실행 — 발견한 문제를 코드로 수정\n4) 확인 — 자동 검증 (verify-image-fit / verify-docx-pages / verify-docx-structure / verify-ppt-overflow) 발동-PASS 확인\n5) 보고 — 표-목록으로 결과 + 남은 결정사항\n\n금기:\n- 대상 확정 없이 실행 착수 (0순위 위반)\n- 부분 처리 (한 파일만 보고 답변)\n- 검증 X 하고 완료 보고\n- 사용자에게 결정 떠넘기기 (크리티컬 5가지 외)\n- 회피-딴말 (직접 답 -> 부연 -> 행동)\n- 매번 사용자 지시 기다림 (auto-planner 자동 발동)\n\n자동 발동 트리거: auto-planner.md skill\n\n${GUIDE}${SUBAGENT_GUIDE}${MEMORY_GUIDE}${ALARM_GUIDE}${COMPACT_GUIDE}"}}
EOF
fi

exit 0
