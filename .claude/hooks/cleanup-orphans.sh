#!/usr/bin/env bash
# cleanup-orphans.sh — 세션 종료 시 뒷처리
# - 오래된 lock 파일 (30분 이상 · 기록된 pid 가 종료된 것만) 제거
# - heartbeat 끊긴 codex-auto/gemini-auto/claude-auto cmd 창 후보 기록 (종료 X)
# - 좀비 Python 프로세스 리포트 (자동 종료는 하지 않음 — main.py 서버 보호)
# Windows Git Bash 호환

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_DIR" || exit 0

LOG=".claude/context-cache/guard.log"
TS="$(date '+%Y-%m-%d %H:%M:%S')"
EVENT="${1:-SessionEnd}"

log_line() { echo "[$TS] [cleanup-$EVENT] $*" >> "$LOG" 2>/dev/null; }

# ─────────────────────────────────────────────
# 1. 오래된 lock 파일 제거 (30분 이상 갱신 없음)
# ─────────────────────────────────────────────
if [ -d ".claude/tasks/locks" ]; then
  REMOVED=0
  KEPT=0
  while IFS= read -r -d '' lock; do
    if [ -f "$lock" ]; then
      # 2026-11-04 감사: 30분 경과만으로 지우지 않는다 — 기록된 pid 가 종료된 lock 만 삭제 (file-locking-policy.md)
      LPID=$(grep -o '"pid"[^0-9]*[0-9]*' "$lock" 2>/dev/null | grep -o '[0-9]*$')
      if [ -n "$LPID" ] && ! tasklist //FI "PID eq $LPID" 2>/dev/null | grep -q " $LPID " && ! kill -0 "$LPID" 2>/dev/null; then
        rm -f "$lock" 2>/dev/null && REMOVED=$((REMOVED + 1))
      else
        KEPT=$((KEPT + 1))
      fi
    fi
  done < <(find .claude/tasks/locks -name "*.lock" -type f -mmin +30 -print0 2>/dev/null)
  [ "$REMOVED" -gt 0 ] && log_line "removed $REMOVED stale lock file(s) (pid 종료 확인)"
  [ "$KEPT" -gt 0 ] && log_line "kept $KEPT old lock file(s) (pid 실행 중 또는 기록 없음)"
fi

# ─────────────────────────────────────────────
# 2. heartbeat 끊긴 auto.bat cmd 창 종료 (heartbeat 갱신이 5분 이상 없으면)
# ─────────────────────────────────────────────
if [ -f ".claude/orca-heartbeat" ]; then
  HB_AGE=$(( $(date +%s) - $(stat -c %Y .claude/orca-heartbeat 2>/dev/null || echo 0) ))
  if [ "$HB_AGE" -gt 300 ]; then
    # heartbeat 5분 이상 안 갱신 -> 대상 cmd 창을 기록만 한다 (2026-11-04 감사: heartbeat·명령줄 패턴만으로는
    # 어느 작업이 띄운 창인지 증명 못 함 → 다른 세션·작업 창까지 죽일 수 있어 자동 종료 X · 사람이 확인 후 정리)
    FOUND=$(powershell -NoProfile -Command "
      Get-WmiObject Win32_Process -Filter \"Name='cmd.exe'\" 2>\$null |
        Where-Object { \$_.CommandLine -match '(codex-auto|gemini-auto|claude-auto)\.bat' } |
        ForEach-Object { 'pid=' + \$_.ProcessId }
    " 2>/dev/null | tr -d '\r' | tr '\n' ' ')
    [ -n "${FOUND// /}" ] && log_line "heartbeat stale ${HB_AGE}s · 워커 cmd 창 후보 (소유 미확인 · 종료 안 함): $FOUND"
  fi
fi

# ─────────────────────────────────────────────
# 3. 좀비 Python 프로세스 리포트 (1GB 이상, 1시간 이상 실행)
#    자동 종료는 하지 않음 — main.py/dev 서버 보호
# ─────────────────────────────────────────────
BIG_PY=$(powershell -NoProfile -Command "
  Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { \$_.WorkingSet -gt 1GB } |
    ForEach-Object {
      \$runtime = (New-TimeSpan -Start \$_.StartTime -End (Get-Date)).TotalMinutes;
      if (\$runtime -gt 60) {
        \$mb = [math]::Round(\$_.WorkingSet / 1MB, 0);
        Write-Output \"PID=\$(\$_.Id) MEM=\$(\$mb)MB RUNTIME=\$([math]::Round(\$runtime))min\"
      }
    }
" 2>/dev/null | head -5)
if [ -n "$BIG_PY" ]; then
  log_line "heavy Python processes detected (not auto-killed — manual review needed):"
  while IFS= read -r line; do
    [ -n "$line" ] && log_line "  $line"
  done <<< "$BIG_PY"
fi

# ─────────────────────────────────────────────
# 4. .bak / .safe_bak / .bak_YYYYMMDD_* 파일 — 후보 수만 기록 (삭제 X)
#    git 에 없는 백업 (DB 백업·sandbox 증거) 도 같은 확장자라 git history 로 대체되지 않는다
#    .git/ 디렉터리와 node_modules 는 제외
# ─────────────────────────────────────────────
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # 2026-11-04 감사: 확장자만으로 지우면 git 에 없는 백업 (DB 백업 orca.db.bak.* · .repair-sandbox 증거) 까지 사라짐
  # → 삭제하지 않고 후보 수만 기록 (정리는 사람이 확인 후 · 3일+ 임시는 cleanup-pollution 정책)
  BAK_FOUND=0
  # 2026-11-05 V1.1 D: 후보 경로 목록 기록 · 증거·미완료 작업 폴더는 후보에서 제외 (cleanup-pollution 과 같은 보호 범위)
  CANDIDATES=".claude/state/cleanup-candidates.txt"
  : > "$CANDIDATES" 2>/dev/null
  while IFS= read -r -d '' bak; do
    BAK_FOUND=$((BAK_FOUND + 1))
    printf '%s\n' "$bak" >> "$CANDIDATES" 2>/dev/null
  done < <(find . \
    -path ./.git -prune -o \
    -path ./node_modules -prune -o \
    -path ./venv -prune -o \
    -path ./.venv -prune -o \
    -path ./.repair-sandbox -prune -o \
    -path ./.claude/tasks -prune -o \
    -path '*/integrity-baseline' -prune -o \
    \( -name "*.bak" -o -name "*.safe_bak" -o -name "*.bak_*" -o -name "*.bak.*" -o -name "*.orig" -o -name "*.tmp" \) \
    -type f -print0 2>/dev/null)
  [ "$BAK_FOUND" -gt 0 ] && log_line "정리 후보 $BAK_FOUND 개 → $CANDIDATES (자동 삭제 안 함)"
fi

exit 0
