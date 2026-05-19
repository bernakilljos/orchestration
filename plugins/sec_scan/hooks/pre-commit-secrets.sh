#!/usr/bin/env bash
# sec_scan Hook — PreToolUse Bash matcher (git commit)
# 시크릿 노출 차단 (CLAUDE.md § 7-23 알림 5가지 중 #1)
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/sec-scan.log"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# stdin 에서 hook input
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# git commit 명령만 처리
if command -v jq >/dev/null 2>&1; then
  CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
else
  CMD=$(echo "$INPUT" | grep -oE '"command"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

# git commit / git push 만 검사
case "$CMD" in
  *"git commit"*|*"git push"*) ;;
  *) exit 0 ;;
esac

# gitleaks 실행 (없으면 fallback grep)
RESULT_FILE="${PROJECT_ROOT}/.claude/state/gitleaks-staged.json"
mkdir -p "$(dirname "$RESULT_FILE")"

if command -v gitleaks >/dev/null 2>&1; then
  cd "$PROJECT_ROOT"
  gitleaks protect --staged --report-format json --report-path "$RESULT_FILE" 2>>"$LOG" || GITLEAKS_FAIL=1
else
  # fallback: 자체 패턴
  STAGED=$(cd "$PROJECT_ROOT" && git diff --cached --name-only 2>/dev/null)
  for f in $STAGED; do
    [ -f "$PROJECT_ROOT/$f" ] || continue
    if grep -qE "(ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,}|AKIA[A-Z0-9]{16}|-----BEGIN .* PRIVATE KEY-----)" "$PROJECT_ROOT/$f" 2>/dev/null; then
      echo "[$(date +%F_%T)] secret detected: $f" >> "$LOG"
      GITLEAKS_FAIL=1
    fi
  done
fi

if [ "${GITLEAKS_FAIL:-0}" = "1" ]; then
  cat >&2 <<EOF
{
  "decision": "block",
  "reason": "sec_scan: secret detected in staged files. Review .claude/state/gitleaks-staged.json or .claude/logs/sec-scan.log",
  "systemMessage": "보안 위협: 시크릿(PAT/API key/private key) 노출 가능. /sec-scan 으로 상세 확인 후 .env 분리 또는 placeholder 변환."
}
EOF
  exit 2
fi

exit 0
