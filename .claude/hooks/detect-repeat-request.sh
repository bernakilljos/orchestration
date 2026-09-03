#!/usr/bin/env bash
# detect-repeat-request.sh — UserPromptSubmit hook
# 목적: 사용자가 같은 지시 반복 감지 -> loop 자동 발동 제안
# 근거: 2026-08-12 사용자 지적 — "사용자가 계속 말하다가 중복요청이면 loop 를 하세요"
set -e

INPUT="$(cat)"
if command -v jq >/dev/null 2>&1; then
  PROMPT="$(echo "$INPUT" | jq -r '.prompt // ""' 2>/dev/null | head -c 500)"
else
  PROMPT="$(echo "$INPUT" | grep -oE '"prompt"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/' | head -c 500)"
fi
[ -z "$PROMPT" ] && exit 0

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
HIST="$PROJECT/.claude/state/prompt-history"
mkdir -p "$(dirname "$HIST")" 2>/dev/null

# 최근 10개 프롬프트 유지 (원소당 한 줄, 특수문자 escape)
current_line="$(echo "$PROMPT" | tr '\n' ' ' | tr -s ' ' | head -c 300)"

# 유사도 계산 — 키워드 3+ 겹치면 중복
similarity_score=0
if [ -f "$HIST" ]; then
  # 현재 프롬프트에서 키워드 (2자+) 추출
  current_kw="$(echo "$current_line" | grep -oE '[가-힣a-zA-Z][가-힣a-zA-Z0-9_-]+' | sort -u | head -10)"
  # 최근 5개 프롬프트와 비교
  tail -5 "$HIST" 2>/dev/null | while IFS= read -r past; do
    past_kw="$(echo "$past" | grep -oE '[가-힣a-zA-Z][가-힣a-zA-Z0-9_-]+' | sort -u)"
    common="$(comm -12 <(echo "$current_kw") <(echo "$past_kw" | sort -u) 2>/dev/null | wc -l | tr -d '[:space:]')"
    if [ "$common" -ge 3 ] 2>/dev/null; then
      echo "$common"
    fi
  done | head -1 > "$PROJECT/.claude/state/.repeat-score" 2>/dev/null
  similarity_score="$(cat "$PROJECT/.claude/state/.repeat-score" 2>/dev/null | tr -d '[:space:]')"
  [ -z "$similarity_score" ] && similarity_score=0
fi

# 히스토리 추가
echo "$current_line" >> "$HIST"
# 최근 10개만 유지
tail -10 "$HIST" > "$HIST.tmp" 2>/dev/null && mv "$HIST.tmp" "$HIST" 2>/dev/null

# 유사도 3+ 감지 시 systemMessage
if [ "$similarity_score" -ge 3 ] 2>/dev/null; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[중복 요청 감지 — 유사도 $similarity_score 키워드]\\n최근 프롬프트와 반복 패턴. 재발 지적 가능성 높음.\\n\\n★ 대응:\\n  1) 지금까지 대응이 부족했는지 인정\\n  2) /loop 자동 발동 검토 (반복 작업 자동화)\\n  3) 감지-강제 시스템 (hook-rule-memory) 이 놓친 부분 실측 후 등재\\n  4) 매번 같은 지적 = 시스템 결함 신호 (사용자 인지 부하 X)\\n\\n관련 룰: .claude/rules/consistency.md § 기준 일관성\\n         .claude/rules/failure-mode.md § 회피 안티패턴"}}
EOF
fi
exit 0
