#!/usr/bin/env bash
# doc_auto Hook — sec_scan 완료 후 자동 호출
# AI-Native 파이프라인 3단계 (마지막)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/doc-auto.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

FILE_PATH="${1:-}"
[ -z "$FILE_PATH" ] && exit 0

echo "[$(date +%F_%T)] doc_auto start: $FILE_PATH" >> "$LOG"

# diff 추출
STATE_DIR="${PROJECT_ROOT}/.claude/state"
mkdir -p "$STATE_DIR"
SHA=$(echo "$FILE_PATH" | sha256sum 2>/dev/null | cut -c1-8)
[ -z "$SHA" ] && SHA=$(date +%s)
OUT_FILE="${STATE_DIR}/doc-auto-${SHA}.md"

cd "$PROJECT_ROOT"
DIFF=$(git diff HEAD -- "$FILE_PATH" 2>/dev/null | head -200)

if [ -z "$DIFF" ]; then
  echo "[$(date +%F_%T)] no diff: $FILE_PATH" >> "$LOG"
  exit 0
fi

# task-instruction 생성 (Claude Sonnet 위임)
cat > "$OUT_FILE" <<EOF
# doc_auto task — $FILE_PATH

## Diff (HEAD)
\`\`\`
$DIFF
\`\`\`

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md \`[Unreleased]\` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
EOF

echo "[$(date +%F_%T)] task created: $OUT_FILE" >> "$LOG"

# claude-auto worker 가 픽업할 수 있도록 task 큐에 넣기
TASK_DIR="${PROJECT_ROOT}/.claude/tasks"
mkdir -p "$TASK_DIR"
cp "$OUT_FILE" "${TASK_DIR}/doc-auto-${SHA}.md"

exit 0
