#!/usr/bin/env bash
# periodic-rules-reminder.sh — UserPromptSubmit에서 10번째마다 규칙 리마인드
# 목적: 긴 대화에서 규칙 attention 가중치 유지
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
_IN="$(cat 2>/dev/null || true)"
# 2026-10-03: /loop(Cron) 프롬프트("[LOOP] ...")엔 안내문을 넣지 않는다 — 루프 한 번에 훅들이 5.5KB 를 넣어
#   하루 168회면 ~900KB, 1M 창을 이틀이면 안내문만으로 채운다(루프 세션 천장의 한 원인).
# 2026-10-05: 배경 작업 완료 알림(<task-notification>)도 사람 입력이 아니다 — 같은 길로 들어와 '중복 요청 3회+' 를 매번 냈다.
_LOOP_RE='"prompt"[[:space:]]*:[[:space:]]*"(\[LOOP\] |<task-notification>)'
[[ "${_IN:-}" =~ $_LOOP_RE ]] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
# 세션별 카운터 — 전역이면 세션이 바뀌어도 누적돼 새 세션 2번째 프롬프트가
# "10번째" 로 세어진다 (2026-09-08: 전역값 2510 이었다)
_SID="$(ls -t "$HOME/.claude/projects/"*"$(basename "$PROJECT_DIR")"*/*.jsonl 2>/dev/null | head -1 | xargs -r basename 2>/dev/null | sed 's/\.jsonl$//')"
[ -n "${_SID:-}" ] || _SID="unknown"
mkdir -p "$PROJECT_DIR/.claude/state/session-turns.d" 2>/dev/null
COUNTER_FILE="$PROJECT_DIR/.claude/state/session-turns.d/$_SID.prompts"
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
