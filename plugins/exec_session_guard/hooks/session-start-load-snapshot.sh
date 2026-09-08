#!/usr/bin/env bash
# session-start-load-snapshot.sh — 새 세션에 이전 세션 문맥을 넘긴다.
# stdout 은 Claude Code 가 systemMessage 로 주입한다.
# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
SNAP="$PROJECT_DIR/.claude/context-cache/session-snapshot.md"

[ -f "$SNAP" ] || exit 0

MTIME="$(stat -c %Y "$SNAP" 2>/dev/null || stat -f %m "$SNAP" 2>/dev/null || echo 0)"
AGE_MIN=$(( ( $(date +%s) - ${MTIME:-0} ) / 60 ))

# 본문에 적힌 저장 시각 (헤더) — mtime 만 갱신되고 본문이 낡는 사고를 잡기 위해 함께 보여준다
HEADER_TS="$(head -1 "$SNAP" | sed 's/^#\+ *//')"

echo "=== 이전 세션 스냅샷 (${AGE_MIN}분 전 · ${HEADER_TS}) ==="
if [ "$AGE_MIN" -gt 1440 ]; then
  echo "[주의] 24시간 넘은 스냅샷 — 현재 상태와 다를 수 있으니 실측 후 사용."
fi
echo ""
# 컨텍스트 절약: 앞 120줄만
head -120 "$SNAP"
echo ""
echo "=== 스냅샷 끝 — 새로 시작하지 말고 위 상태에서 이어서 진행 ==="
exit 0
