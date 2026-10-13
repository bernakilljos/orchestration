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

# 자동 설치 (한 번만, async X — 즉시 실행 필요)
INSTALL_SCRIPT="${PROJECT_ROOT}/.claude/scripts/install-sec-tools.sh"
[ -x "$INSTALL_SCRIPT" ] && bash "$INSTALL_SCRIPT" >/dev/null 2>&1 || true

# gitleaks 경로 결정 (PATH > TOOLS_DIR/.exe > TOOLS_DIR/)
TOOLS_DIR="${PROJECT_ROOT}/.claude/state/tools"
GITLEAKS_BIN=""
if command -v gitleaks >/dev/null 2>&1; then
  GITLEAKS_BIN="gitleaks"
elif [ -x "$TOOLS_DIR/gitleaks.exe" ]; then
  GITLEAKS_BIN="$TOOLS_DIR/gitleaks.exe"
elif [ -x "$TOOLS_DIR/gitleaks" ]; then
  GITLEAKS_BIN="$TOOLS_DIR/gitleaks"
fi

RESULT_FILE="${PROJECT_ROOT}/.claude/state/gitleaks-staged.json"
mkdir -p "$(dirname "$RESULT_FILE")"

# ★2026-10-06 실측 수리 — 오탐으로 커밋이 막히고, 정작 스캔은 돌지 않았다.
#   증상: A.RMS 를 커밋하려는데 "secret detected" 로 차단. gitleaks 로그는 "no leaks found".
#   원인 2개가 겹쳤다:
#     ① 스캔 위치가 틀렸다 — CLAUDE_PROJECT_DIR(= 저장소 루트의 상위, git 아님)에서
#        `gitleaks protect --staged` 를 돌렸다. 실제 커밋 대상(Project1.5·A.RMS)이 아니다.
#        → 커밋하려는 저장소(git rev-parse --show-toplevel)를 스캔한다.
#     ② 종료코드 해석이 틀렸다 — gitleaks 는 「시크릿 발견」도 「실행 실패」도 non-zero 다.
#        그걸 한 덩어리로 GITLEAKS_FAIL=1 로 받아 **에러를 시크릿으로 보고**했다.
#        그래서 스캔이 한 번도 안 돌았는데 차단만 됐다(= 보안 기능 0, 차단 100%).
#        → 리포트 JSON 에 실제 발견이 있을 때만 차단. 실행 실패는 로그 + 통과(열어둔다 —
#          닫으면 모든 커밋이 멈춘다. 발견 못 한 것을 발견으로 위장하지 않는다).
SCAN_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$SCAN_DIR" ] || SCAN_DIR="$PROJECT_ROOT"

if [ -n "$GITLEAKS_BIN" ]; then
  GL_RC=0
  ( cd "$SCAN_DIR" && "$GITLEAKS_BIN" protect --staged --report-format json --report-path "$RESULT_FILE" ) 2>>"$LOG" || GL_RC=$?
  # 리포트에 실제 발견이 있는가 — 파일이 없거나 빈 배열이면 발견 0
  GL_FOUND=0
  if [ -s "$RESULT_FILE" ]; then
    if grep -q '"RuleID"' "$RESULT_FILE" 2>/dev/null; then GL_FOUND=1; fi
  fi
  if [ "$GL_FOUND" = "1" ]; then
    GITLEAKS_FAIL=1
    echo "[$(date +%F_%T)] BLOCK: gitleaks 발견 (scan_dir=$SCAN_DIR)" >> "$LOG"
  elif [ "$GL_RC" != "0" ]; then
    echo "[$(date +%F_%T)] WARN: gitleaks 실행 실패 rc=$GL_RC (scan_dir=$SCAN_DIR) — 발견 0 으로 통과" >> "$LOG"
  fi
else
  # fallback: 자체 패턴 (gitleaks 미설치 환경)
  STAGED=$(cd "$SCAN_DIR" && git diff --cached --name-only 2>/dev/null)
  for f in $STAGED; do
    [ -f "$SCAN_DIR/$f" ] || continue
    if grep -qE "(ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{32,}|AKIA[A-Z0-9]{16}|-----BEGIN .* PRIVATE KEY-----)" "$SCAN_DIR/$f" 2>/dev/null; then
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
