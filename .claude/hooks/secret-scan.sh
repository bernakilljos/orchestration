#!/usr/bin/env bash
# PreToolUse hook — Bash git commit / push 직전 secret 스캔
# .env / API key / PAT 검출 시 차단
set -e
INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$INPUT" | jq -r '.tool_input.command // ""')"
else
  CMD="$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
fi

# git commit 또는 push 만 검사
if ! echo "$CMD" | grep -qE '^(git commit|git push)'; then
  exit 0
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Secret 패턴
SECRET_PATTERNS=(
  'sk-[A-Za-z0-9]{40,}'                          # OpenAI API key
  'sk-ant-[A-Za-z0-9_-]{40,}'                    # Anthropic key
  'ghp_[A-Za-z0-9]{36,}'                          # GitHub PAT
  'AKIA[0-9A-Z]{16}'                              # AWS access key
  'AIza[0-9A-Za-z_-]{35}'                         # Google API key
  'xox[baprs]-[0-9]+-[0-9]+-[A-Za-z0-9]+'         # Slack token
  'glpat-[A-Za-z0-9_-]{20,}'                      # GitLab PAT
)

# staged 파일 중 secret 검사
STAGED="$(cd "$PROJECT_ROOT" && git diff --cached --name-only 2>/dev/null || echo "")"
FOUND=""
for f in $STAGED; do
  [ -f "$PROJECT_ROOT/$f" ] || continue
  # 사용자 명시 화이트리스트 (내부 use OK)
  case "$f" in
    docs/ini/*) continue ;;  # 내부 ini 허용
  esac
  case "$f" in
    *.env|*.env.local|.env*|*secret*|*credentials*) FOUND="${FOUND}\\n- $f (위험 파일명)" ;;
  esac
  for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -qE "$pattern" "$PROJECT_ROOT/$f" 2>/dev/null; then
      FOUND="${FOUND}\\n- $f (secret 패턴 감지)"
      break
    fi
  done
done

if [ -n "$FOUND" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"⛔ Secret 감지 — commit 차단:${FOUND}\\n.env / API key 제거 후 재시도. .gitignore 에 추가 권장."}}
EOF
  exit 0
fi

exit 0
