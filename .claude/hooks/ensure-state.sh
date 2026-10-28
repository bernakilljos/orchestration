#!/usr/bin/env bash
# ensure-state.sh — SessionStart (async) · 새 PC·새 clone 에서도 상태 저장소가 바로 동작하게
#   1) orca.db 스키마 (이력 테이블 포함) — 없으면 conversations 등 INSERT 가 조용히 실패
#   2) 하드코딩 감사 캐시 (.claude/state/hardcoded-audit.json) — 6시간 throttle
# orca.db·state/ 는 gitignore 라 git pull 로 안 온다 → pull 만으로 같은 환경이 되려면 여기서 생성.
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG="$PROJECT_DIR/.claude/logs/ensure-state.log"
mkdir -p "$PROJECT_DIR/.claude/logs" "$PROJECT_DIR/.claude/state"
# python 자동 검색 - WindowsApps stub 회피 (Microsoft Store Install Manager 뜨는 문제 fix)
if [ -r "$PROJECT_DIR/.claude/hooks/find-python.sh" ]; then
  . "$PROJECT_DIR/.claude/hooks/find-python.sh"
  PY="${PYTHON:-}"
fi
[ -z "$PY" ] && PY="$(command -v python || command -v python3)"
[ -n "$PY" ] || exit 0
# 캐시 저장 - 모든 hook 이 참조
echo "$PY" > "$PROJECT_DIR/.claude/state/python-path.txt"
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# Microsoft Store Install Manager 재발 방지 (2026-10-28 사용자 반복 지시)
# Windows App Execution Alias stub (python/python3) 매 세션 삭제 — Store 업데이트/재부팅으로 복구되면 또 뜸
# $PY 가 Python314 (실제) 로 확인된 상태에서만 삭제 (안전장치)
if [[ "$PY" != *WindowsApps* ]] && [ -n "$PY" ]; then
  for stub in "$LOCALAPPDATA/Microsoft/WindowsApps/python.exe" \
              "$LOCALAPPDATA/Microsoft/WindowsApps/python3.exe" \
              "/c/Users/$USER/AppData/Local/Microsoft/WindowsApps/python.exe" \
              "/c/Users/$USER/AppData/Local/Microsoft/WindowsApps/python3.exe"; do
    [ -L "$stub" ] && rm -f "$stub" 2>/dev/null && echo "[$TS] WindowsApps stub removed: $stub" >>"$LOG"
  done
fi

( cd "$PROJECT_DIR/.claude/scripts/lib" && "$PY" -X utf8 -c "import state_db; state_db.init_schema()" ) >>"$LOG" 2>&1 && echo "[$TS] schema ok" >>"$LOG" || echo "[$TS] schema FAIL" >>"$LOG"

AUD="$PROJECT_DIR/.claude/state/hardcoded-audit.json"
if [ ! -f "$AUD" ] || [ $(( $(date +%s) - $(stat -c %Y "$AUD" 2>/dev/null || echo 0) )) -gt 21600 ]; then
  "$PY" -X utf8 "$PROJECT_DIR/.claude/scripts/audit-hardcoded.py" >>"$LOG" 2>&1 || true
fi
# 새 PC 재발 방지 검사 (DDL · state 생성기 hook 연결) — 결과는 로그에만
"$PY" -X utf8 "$PROJECT_DIR/.claude/scripts/verify-fresh-clone.py" >>"$LOG" 2>&1 || echo "[$TS] verify-fresh-clone FAIL" >>"$LOG"
exit 0
