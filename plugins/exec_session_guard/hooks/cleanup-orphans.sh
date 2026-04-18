#!/usr/bin/env bash
# cleanup-orphans.sh — 세션 종료 시 뒷처리
# - 오래된 lock 파일 (30분 이상) 제거
# - heartbeat 끊긴 codex-auto/gemini-auto/claude-auto cmd 창 종료
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
  while IFS= read -r -d '' lock; do
    if [ -f "$lock" ]; then
      rm -f "$lock" 2>/dev/null && REMOVED=$((REMOVED + 1))
    fi
  done < <(find .claude/tasks/locks -name "*.lock" -type f -mmin +30 -print0 2>/dev/null)
  [ "$REMOVED" -gt 0 ] && log_line "removed $REMOVED stale lock file(s)"
fi

# ─────────────────────────────────────────────
# 2. heartbeat 끊긴 auto.bat cmd 창 종료 (heartbeat 갱신이 5분 이상 없으면)
# ─────────────────────────────────────────────
if [ -f ".claude/orca-heartbeat" ]; then
  HB_AGE=$(( $(date +%s) - $(stat -c %Y .claude/orca-heartbeat 2>/dev/null || echo 0) ))
  if [ "$HB_AGE" -gt 300 ]; then
    # heartbeat 5분 이상 안 갱신 → 워커 좀비 상태로 간주 → 관련 cmd 창 정리
    KILLED=$(powershell -NoProfile -Command "
      \$count = 0;
      Get-WmiObject Win32_Process -Filter \"Name='cmd.exe'\" 2>\$null |
        Where-Object { \$_.CommandLine -match '(codex-auto|gemini-auto|claude-auto)\.bat' } |
        ForEach-Object {
          try { Stop-Process -Id \$_.ProcessId -Force -ErrorAction Stop; \$count++ } catch {}
        };
      \$count
    " 2>/dev/null | tr -d '\r\n ')
    [ "${KILLED:-0}" -gt 0 ] && log_line "killed $KILLED orphan cmd.exe (heartbeat stale ${HB_AGE}s)"
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
# 4. .bak / .safe_bak / .bak_YYYYMMDD_* 파일 제거
#    git 저장소 안에서는 백업 파일이 불필요 (git history 가 대체)
#    .git/ 디렉터리와 node_modules 는 제외
# ─────────────────────────────────────────────
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BAK_REMOVED=0
  while IFS= read -r -d '' bak; do
    rm -f "$bak" 2>/dev/null && BAK_REMOVED=$((BAK_REMOVED + 1))
  done < <(find . \
    -path ./.git -prune -o \
    -path ./node_modules -prune -o \
    -path ./venv -prune -o \
    -path ./.venv -prune -o \
    \( -name "*.bak" -o -name "*.safe_bak" -o -name "*.bak_*" -o -name "*.bak.*" -o -name "*.orig" \) \
    -type f -print0 2>/dev/null)
  [ "$BAK_REMOVED" -gt 0 ] && log_line "removed $BAK_REMOVED backup file(s) (.bak/.safe_bak) — git history 대체"
fi

exit 0
