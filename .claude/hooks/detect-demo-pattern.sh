#!/usr/bin/env bash
# 데모/목업 패턴 자동 감지 · PostToolUse Write/Edit hook.
#
# 근거: 사용자 지시 "운영이라고 했는데 데모로 만든다 답답" (2026-08-18).
# 룰: feedback_no_mock_default.md · CLAUDE.md § 실전 원칙.
#
# 감지 시 systemMessage 로 알림 + 로그. 사용자가 명시 (목업·mock·demo·MVP·시연) 승인 있으면 skip.
#
# 감지 패턴 (아래 하나라도 매치 → 데모 의심):
#   - 하드코딩 sample/mock JSON (예: "mockUsers = ["·"const SAMPLE_DATA")
#   - stub 함수 (예: "return { status: 'ok' }" · "TODO: connect real DB")
#   - dummy/fake/example 명명
#   - "이 정도면 시연 되지 않을까" 유형 주석
#
# 룰 정합:
#   - feedback_no_mock_default.md (사용자 명시 없으면 실전)
#   - CLAUDE.md § 실전 원칙
#   - .claude/rules/best-practices.md § 실전 원칙 (No 데모·MVP·목업)

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/demo-pattern.log"

INPUT=$(cat 2>/dev/null || echo '{}')
FILE=$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//;s/"$//')

# 스킬·룰·메모리·docs·markdown 은 스킵 (설명 문서 정상)
case "$FILE" in
  *.md|*.txt|*.rst|*.log|*.json|*/memory/*|*/docs/*|*/rules/*|*/skills/*|*/hooks/*) exit 0 ;;
esac

[ -f "$FILE" ] || exit 0

# 사용자 명시 (목업·mock·demo·MVP·시연) 최근 conversation 감지 — 세션 flag 로 우회
SKIP_FLAG="$PROJECT_ROOT/.claude/state/demo-mode-approved"
if [ -f "$SKIP_FLAG" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$SKIP_FLAG" 2>/dev/null || echo 0) ))
  # 4시간 이내 승인만 유효
  if [ "$AGE" -lt 14400 ]; then
    exit 0
  fi
fi

# 감지 패턴 (실전 위반 신호)
MATCHES=""

# 1. 하드코딩 sample/mock array (JavaScript/Python/TypeScript)
if grep -qE '^\s*(const|let|var)\s+(mock|sample|dummy|fake|example|test)[A-Z][a-zA-Z]*\s*=\s*\[' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - 하드코딩 sample/mock 배열 (const mockX / sampleY / dummyZ)"
fi

if grep -qE '^\s*(MOCK|SAMPLE|DUMMY|FAKE|EXAMPLE)_[A-Z_]+\s*=\s*\[' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - 하드코딩 상수 배열 (MOCK_USERS / SAMPLE_DATA 등)"
fi

# 2. Stub return (Python·JS)
if grep -qE 'return\s+\{\s*["\x27]status["\x27]\s*:\s*["\x27]ok["\x27]\s*\}\s*$' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - Stub return (status: ok 만 리턴)"
fi

# 3. TODO connect real DB 유형
if grep -qiE 'TODO[:\s]+(connect|integrate|hook up|wire up|replace with)\s+(real|actual|production|prod)' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - TODO connect real DB/API (스텁 상태 자백)"
fi

# 4. "시연"·"데모"·"MVP" 주석
if grep -qE '(^|\s)#.*시연|(^|\s)//.*시연|(^|\s)#.*데모|(^|\s)//.*데모|MVP\s*정도' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - '시연/데모/MVP 정도' 주석 (실전 위반 자각)"
fi

# 5. hardcoded "example@example.com" · "test@test.com" 등
if grep -qE '["\x27](example|test|dummy|fake)@(example|test)\.(com|org)["\x27]' "$FILE" 2>/dev/null; then
  MATCHES="$MATCHES\n  - dummy email/domain (example@example.com 등)"
fi

if [ -z "$MATCHES" ]; then
  exit 0
fi

echo "[$(date -Iseconds)] $FILE 데모 패턴 감지" >> "$LOG_FILE"
printf '%b\n' "$MATCHES" >> "$LOG_FILE"

# systemMessage JSON (Claude 다음 응답에서 사용자에게 알림)
MSG="[⚠ 데모/목업 패턴 감지 — $FILE]$MATCHES\n\n실전 원칙 위반 가능성. 사용자가 '목업/데모/시연/MVP' 명시 안 했으면 실전으로 재작성 필요.\n승인 시 4시간 skip: touch .claude/state/demo-mode-approved"

if command -v jq >/dev/null 2>&1; then
  printf '%s' "$MSG" | jq -Rs '{systemMessage: .}'
else
  ESC=$(printf '%s' "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "%s\\n", $0}')
  printf '{"systemMessage":"%s"}\n' "$ESC"
fi

exit 0
