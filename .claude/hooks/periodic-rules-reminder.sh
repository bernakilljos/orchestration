#!/usr/bin/env bash
# periodic-rules-reminder.sh — UserPromptSubmit에서 10번째마다 규칙 리마인드
# 목적: 긴 대화에서 규칙 attention 가중치 유지
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
COUNTER_FILE="$PROJECT_DIR/.claude/state/.prompt-counter"
mkdir -p "$PROJECT_DIR/.claude/state" 2>/dev/null

# 카운터 증가
COUNT=0
[ -f "$COUNTER_FILE" ] && COUNT=$(cat "$COUNTER_FILE" 2>/dev/null | tr -d '[:space:]')
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# 10번째마다 리마인드
if [ $((COUNT % 10)) -eq 0 ]; then
  cat <<'MSG'

 [규칙 리마인드 — 10번째 프롬프트]
0. **대상 확정 우선** — 첫 응답 첫 줄에 "대상: <path>" 명시. kit/설정/target/글로벌 4갈래. 확정 전 grep-Read-Edit X. (direction-first.md)
1. git commit -> guide.txt+CLAUDE.md+settings.json 같이
2. 도메인별 X -> 공통 도구 보강
3. 사용자 카테고리만 -> 알아서 세부 채움
4. 물어보지 말고 실행 (Zero-touch)
5. sync + auto-stats 자동

MSG
fi

exit 0
