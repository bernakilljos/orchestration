#!/usr/bin/env bash
# weekly-audit.sh — 매주 자동 감사 (hook 미등록, README 현행화, 문서 누락)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

LOG=".claude/logs/weekly-audit.log"
mkdir -p .claude/logs 2>/dev/null
TS=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TS] Weekly Audit Start" > "$LOG"

# 1. 미등록 hook
echo "" >> "$LOG"
echo "=== 미등록 hook ===" >> "$LOG"
MISSING_HOOKS=0
for f in $(find plugins -path "*/hooks/*.sh" -type f -exec basename {} \;); do
  grep -q "$f" .claude/settings.json 2>/dev/null || {
    echo "  [X] $f" >> "$LOG"
    MISSING_HOOKS=$((MISSING_HOOKS + 1))
  }
done
echo "  총 $MISSING_HOOKS 개 미등록" >> "$LOG"

# 2. 빈 README
echo "" >> "$LOG"
echo "=== 빈/짧은 README ===" >> "$LOG"
for d in plugins/*/; do
  p=$(basename "$d")
  [ "$p" = "_template" ] && continue
  readme="$d/README.md"
  if [ ! -f "$readme" ]; then
    echo "  [X] $p: README.md 없음" >> "$LOG"
  elif [ $(wc -l < "$readme") -lt 5 ]; then
    echo "  [WARN] $p: README.md 5줄 미만" >> "$LOG"
  fi
done

# 3. sync drift
echo "" >> "$LOG"
echo "=== Sync drift ===" >> "$LOG"
bash .claude/scripts/sync-plugins.sh --check 2>&1 | tail -5 >> "$LOG"

# 4. 스키마 검증
echo "" >> "$LOG"
echo "=== Plugin schema ===" >> "$LOG"
python .claude/scripts/validate-plugin-schema.py 2>&1 | grep -E "FAIL|WARN|ERROR" >> "$LOG" || echo "  [OK] All PASS" >> "$LOG"

# 5. 하드코딩 경로
echo "" >> "$LOG"
echo "=== 하드코딩 경로 ===" >> "$LOG"
HARD=$(grep -rn 'C:\\Users\\[a-z]' plugins/ .claude/ setup/ --include='*.sh' --include='*.py' --include='*.bat' 2>/dev/null | grep -v '.md:' | wc -l)
echo "  하드코딩 경로: $HARD 건" >> "$LOG"

echo "" >> "$LOG"
echo "[$TS] Weekly Audit Complete" >> "$LOG"

# 요약 출력
echo ""
echo "[weekly-audit] 결과:"
echo "  미등록 hook: $MISSING_HOOKS"
echo "  하드코딩 경로: $HARD"
echo "  상세: .claude/logs/weekly-audit.log"
