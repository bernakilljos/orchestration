#!/usr/bin/env bash
# 오염 파일 자동 정리 — Windows redirect 잔재 + nested 폴더 + 3일+ 임시
# 호출: SessionStart hook 또는 cron 또는 수동
# 로그: .claude/logs/cleanup-pollution.log
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
LOG="$LOG_DIR/cleanup-pollution.log"
mkdir -p "$LOG_DIR"

NOW="$(date '+%Y-%m-%d %H:%M:%S')"
REMOVED=0

log() {
  echo "[$NOW] $1" >> "$LOG"
  REMOVED=$((REMOVED + 1))
}

# 1. nul/NUL 파일 (Windows `2>nul` 잔재) — 즉시 삭제
for f in "$PROJECT_ROOT/nul" "$PROJECT_ROOT/NUL"; do
  if [ -f "$f" ]; then
    rm -f "$f" && log "nul redirect: $f"
  fi
done
# 하위 디렉토리도 (maxdepth 4)
find "$PROJECT_ROOT" -maxdepth 4 -type f \( -name "nul" -o -name "NUL" \) 2>/dev/null | while read -r f; do
  rm -f "$f" && log "nul redirect: $f"
done

# 2. nested .claude/.claude/ (PROJECT_ROOT 계산 버그 잔재) — 즉시
if [ -d "$PROJECT_ROOT/.claude/.claude" ]; then
  rm -rf "$PROJECT_ROOT/.claude/.claude" && log "nested .claude/.claude/"
fi

# 2b. 하위 폴더에 생긴 .claude/ — 훅·statusline 이 cd 한 폴더(pwd)를 루트로 착각해 만든 잔재(10-26 nextjs/src/app/pet 등 9곳).
#     아래 이름의 파일만 든 폴더만 지운다 — 다른 파일이 있으면 그대로 두고 로그만.
find "$PROJECT_ROOT" -mindepth 2 -maxdepth 7 -type d -name .claude   -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "$PROJECT_ROOT/.claude/*" 2>/dev/null | while read -r d; do
  other=$(find "$d" -type f ! -name token-usage.jsonl ! -name audit-bat-lines.stamp ! -name statusline-stdin.json ! -name current-tasks.json 2>/dev/null | head -1)
  if [ -z "$other" ]; then
    find "$d" -depth -delete 2>/dev/null && log "stray .claude/: ${d#$PROJECT_ROOT/}"
  else
    log "stray .claude/ 남김(다른 파일 있음): ${d#$PROJECT_ROOT/}"
  fi
done

# 3. 3일+ 임시 파일 (*.bak / *.orig / *.tmp / *.swp / *~)
DAYS=3
find "$PROJECT_ROOT" -maxdepth 5 -type f \
  \( -name "*.bak" -o -name "*.orig" -o -name "*.tmp" -o -name "*.swp" -o -name "*~" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/.repair-sandbox/*" -not -path "*/.claude/tasks/*" -not -path "*/integrity-baseline/*" \
  -mtime +$DAYS 2>/dev/null | while read -r f; do
  # 2026-11-04 감사: sandbox 증거·미완료 작업·무결성 기준선 안의 파일은 확장자가 같아도 보존
  rm -f "$f" && log "3일+ 임시: $f"
done

# 4. docs/screens/_*.log 3일+ (작업 완료 후 잔재)
find "$PROJECT_ROOT/docs/screens" -maxdepth 1 -type f -name "_*.log" -mtime +$DAYS 2>/dev/null | while read -r f; do
  rm -f "$f" && log "screens log 3일+: $f"
done

# 5. .claude/logs/*.log 14일+ (장기 보존)
find "$PROJECT_ROOT/.claude/logs" -maxdepth 2 -type f -name "*.log" -mtime +14 2>/dev/null | while read -r f; do
  rm -f "$f" && log "logs 14일+: $f"
done

# 6. .claude/tasks/done/ 30일+ 완료 task
find "$PROJECT_ROOT/.claude/tasks/done" -maxdepth 2 -type f -mtime +30 2>/dev/null | while read -r f; do
  rm -f "$f" && log "done task 30일+: $f"
done

# 7. claude tool result 임시파일 (사용자 cache 안) 7일+
PROJ_SLUG=$(printf '%s' "$(cygpath -w "$PROJECT_ROOT" 2>/dev/null || echo "$PROJECT_ROOT")" | sed 's/[^A-Za-z0-9]/-/g')   # 프로젝트 위치로 동적 계산
TOOL_RESULTS="$HOME/.claude/projects/$PROJ_SLUG/tool-results"
if [ -d "$TOOL_RESULTS" ]; then
  find "$TOOL_RESULTS" -maxdepth 2 -type f -mtime +7 2>/dev/null | while read -r f; do
    rm -f "$f"
  done
fi

# 8. [신규] 3일+ 미완료 task·lock·state tmp 요약 (미완료 작업은 보존 · 죽은 pid 의 lock 만 삭제)
STALE_SUMMARY="$PROJECT_ROOT/.claude/state/cleanup-summary-$(date +%Y%m%d).md"
STALE_FOUND=0
STALE_HEADER_WRITTEN=0
write_stale_header() {
  if [ "$STALE_HEADER_WRITTEN" = "0" ]; then
    {
      echo "# 쓰레기 데이터 정리 요약 ($(date +%Y-%m-%d))"
      echo ""
      echo "3일+ 지난 미완료 task·lock·tmp 파일 요약 · 미완료 작업은 보존 (자동 삭제 X) · 종료된 pid 의 lock 만 삭제."
      echo "복원 필요 시 이 파일 참고 (30일 보존)."
      echo ""
      echo "| 경로 | 크기 | 수정일 | 첫 줄 |"
      echo "|---|---|---|---|"
    } > "$STALE_SUMMARY"
    STALE_HEADER_WRITTEN=1
  fi
}
# 대상: pending·in_progress·locks·state 안 *.tmp·*.lock-test
# 2026-11-04 감사 P0: 미완료 작업(pending·in_progress)은 3일 지났다는 것만으로 지우지 않는다 — 요약에 후보로만 남긴다.
# lock 은 기록된 pid 가 더 이상 없을 때만 지운다 (file-locking-policy.md · pid 없거나 살아 있으면 보존).
_pid_alive() {
  [ -n "$1" ] || return 0
  tasklist //FI "PID eq $1" 2>/dev/null | grep -q " $1 " && return 0
  kill -0 "$1" 2>/dev/null
}
for sub in "tasks/pending" "tasks/in_progress" "tasks/locks"; do
  # process substitution: 헤더 플래그·건수가 서브셸에 갇혀 두 번째 폴더가 요약을 덮어쓰던 것 방지
  while read -r f; do
    write_stale_header
    SIZE=$(stat -c "%s" "$f" 2>/dev/null || echo "?")
    MTIME=$(stat -c "%y" "$f" 2>/dev/null | cut -d'.' -f1 || echo "?")
    FIRST=$(head -1 "$f" 2>/dev/null | tr '\n' ' ' | cut -c1-80 || echo "")
    REL="${f#$PROJECT_ROOT/}"
    ACTION="보존 (미완료 작업 · 자동 삭제 안 함)"
    if [ "$sub" = "tasks/locks" ]; then
      LPID=$(grep -o '"pid"[^0-9]*[0-9]*' "$f" 2>/dev/null | grep -o '[0-9]*$' || true)   # pid 없으면 빈 값 (set -e 종료 방지)
      if [ -n "$LPID" ] && ! _pid_alive "$LPID"; then
        rm -f "$f" && ACTION="삭제 (pid $LPID 종료됨)" && log "stale lock (pid $LPID dead): $f"
      else
        ACTION="보존 (pid ${LPID:-없음} · 소유자 확인 불가 또는 실행 중)"
      fi
    fi
    echo "| \`$REL\` | ${SIZE}B | $MTIME | ${FIRST//|/\\|} · $ACTION |" >> "$STALE_SUMMARY"
    STALE_FOUND=$((STALE_FOUND+1))
  done < <(find "$PROJECT_ROOT/.claude/$sub" -maxdepth 2 -type f -mtime +3 2>/dev/null)
done
# state 안 *.tmp·*.lock-test (3일+)
find "$PROJECT_ROOT/.claude/state" -maxdepth 2 -type f \( -name "*.tmp" -o -name "*.lock-test" \) -mtime +3 2>/dev/null | while read -r f; do
  rm -f "$f" && log "state tmp 3d+: $f"
done
# cleanup-summary-*.md 자체 30일+ 삭제 (요약 파일 retention)
find "$PROJECT_ROOT/.claude/state" -maxdepth 1 -type f -name "cleanup-summary-*.md" -mtime +30 2>/dev/null | while read -r f; do
  rm -f "$f" && log "cleanup-summary 30d+: $f"
done
[ "$STALE_FOUND" -gt 0 ] && echo "[cleanup-pollution] 3일+ 미완료·lock 후보 $STALE_FOUND 건 요약 저장: ${STALE_SUMMARY#$PROJECT_ROOT/}" >&2

# 9. 빈 디렉토리 정리 (carve-out: docs/screens, plugins, .claude 보존)
# 임시 폴더만 (.claude/tasks/*/temp/ 등)
find "$PROJECT_ROOT/.claude/tasks" -maxdepth 3 -type d -empty 2>/dev/null | while read -r d; do
  rmdir "$d" 2>/dev/null && log "empty task dir: $d"
done

# 결과
if [ $REMOVED -gt 0 ]; then
  echo "[cleanup-pollution] 정리: $REMOVED 항목 ($NOW)" >&2
fi
exit 0
