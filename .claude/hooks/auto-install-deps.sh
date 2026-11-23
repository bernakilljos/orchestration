#!/usr/bin/env bash
# [차단] 킬스위치 - 파일 있으면 아무것도 안 하고 종료
if [ -f "$HOME/.claude/NO-SCHTASKS" ]; then exit 0; fi
# auto-install-deps.sh — Zero-touch dependency installation.
# Runs at SessionStart. Detects missing tools (playwright python, core MCP servers)
# and installs them in the background. NEVER prompts the user.
#
# Idempotent: each item checked individually; only installs what's missing.
# All work logged to .claude/logs/auto-install-deps.log
#
# Aligns with CLAUDE.md § Zero-touch automation: alerts only for the 5 critical
# categories; package installs are routine and proceed silently.

set -uo pipefail

# Sub-project guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG="$PROJECT_DIR/.claude/logs/auto-install-deps.log"
mkdir -p "$PROJECT_DIR/.claude/logs" 2>/dev/null
TS="$(date '+%Y-%m-%d %H:%M:%S')"

# Throttle: don't re-run within 1 hour
MARK="$PROJECT_DIR/.claude/state/auto-install-deps.last"
if [ -f "$MARK" ]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$MARK" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 3600 ] && exit 0
fi
mkdir -p "$PROJECT_DIR/.claude/state" 2>/dev/null
date +%s > "$MARK"

# ---- 1) Playwright Python package + Chromium browser ----
PYBIN=""
for cand in python python py; do
  if command -v "$cand" >/dev/null 2>&1; then
    PYBIN="$cand"; break
  fi
done

if [ -n "$PYBIN" ]; then
  if ! "$PYBIN" -c "import playwright" >/dev/null 2>&1; then
    echo "[$TS] pip install playwright pillow PyMuPDF python-docx" >> "$LOG"
    nohup "$PYBIN" -m pip install --quiet --user playwright pillow PyMuPDF python-docx \
      >> "$LOG" 2>&1 &
    disown 2>/dev/null || true
  fi
  # Chromium driver — only if playwright imports successfully
  if "$PYBIN" -c "import playwright" >/dev/null 2>&1; then
    if ! "$PYBIN" -c "import playwright; from pathlib import Path; import sys; sys.exit(0 if any(Path(p).rglob('chrome.exe') or Path(p).rglob('chrome') for p in [str(Path.home() / 'AppData/Local/ms-playwright'), '/opt/ms-playwright', str(Path.home() / '.cache/ms-playwright')] if Path(p).exists()) else 1)" 2>/dev/null; then
      echo "[$TS] playwright install chromium" >> "$LOG"
      nohup "$PYBIN" -m playwright install chromium >> "$LOG" 2>&1 &
      disown 2>/dev/null || true
    fi
  fi
fi

# ---- 2) Core MCP servers (claude CLI required) ----
if command -v claude >/dev/null 2>&1; then
  # R357 (2026-11-23): 등록 명령 문자열만 필요한데 `claude mcp list` 는 MCP 서버 전부를 한 번씩 띄워 연결을 확인하고
  #   그 CLI 가 프로젝트 SessionEnd 훅까지 띄웠다 (세션 시작마다 · 60초 뒤 check-mcp-health 가 같은 일을 또 함)
  #   → ~/.claude.json 의 사용자 범위 등록을 «이름: 명령 인자» 줄로 읽는다 (아래 비교 형식 그대로) · 읽기 실패 시 종전 방식
  MCP_LIST="$(python -X utf8 -c "
import json, os, sys
try:
    d = json.load(open(os.path.join(os.path.expanduser('~'), '.claude.json'), encoding='utf-8'))
except Exception:
    sys.exit(3)
for n, e in (d.get('mcpServers') or {}).items():
    if isinstance(e, dict):
        print(n + ': ' + ' '.join([str(e.get('command') or e.get('url') or '')] + [str(a) for a in (e.get('args') or [])]))
" 2>/dev/null)" || MCP_LIST="$(claude mcp list 2>&1 || echo '')"

  # name : install command (cmd /c npx for Windows shell-cross-compat)
  CORE_MCP=(
    "playwright|claude mcp add playwright -s user -- cmd /c npx -y @playwright/mcp"
    "sequential-thinking|claude mcp add sequential-thinking -s user -- cmd /c npx -y @modelcontextprotocol/server-sequential-thinking"
    "fetch|claude mcp add fetch -s user -- uvx mcp-server-fetch"  # npm @modelcontextprotocol/server-fetch 는 404 (2026-10-02 npm view) · 정본은 PyPI mcp-server-fetch
    "context7|claude mcp add context7 -s user -- cmd /c npx -y @upstash/context7-mcp"
  )

  for entry in "${CORE_MCP[@]}"; do
    NAME="${entry%%|*}"
    CMD="${entry#*|}"
    # 출력 형식 = "name: <command> - ✓ Connected" (콜론). 예전 패턴 "^name[공백]" 은 한 번도 안 맞았다.
    LINE="$(echo "$MCP_LIST" | grep -E "^${NAME}:" | head -1)"
    # Git Bash 가 "cmd /c" 의 /c 를 "C:/" 로 바꿔 등록한 깨진 항목 → 지우고 재등록 (2026-10-02 실측 4개 전부)
    WANT="${CMD#*-- }"   # 등록돼야 할 실행 명령 (예: uvx mcp-server-fetch)
    if [ -n "$LINE" ] && echo "$LINE" | grep -qF "$WANT"; then
      continue   # 이미 kit 정의대로 등록됨
    fi
    # R357: mcp-direct-launch.py 가 같은 패키지를 고정 위치(orca-mcp) 의 node 직접 실행으로 바꾼 등록도 정상 (npx 로 되돌리지 않음)
    #   경로 구분자는 / 로 맞춰 비교 (Windows 경로 @playwright\mcp ↔ 패키지 이름 @playwright/mcp)
    PKG="$(echo "$WANT" | sed -E 's/.*npx (-y )?//; s/ .*//; s/(.)@[^/]*$/\1/')"
    LINE_FWD="${LINE//\\//}"
    if [ -n "$LINE" ] && [[ "$LINE_FWD" == *orca-mcp* && "$LINE_FWD" == *"$PKG"* ]]; then
      continue
    fi
    echo "[$TS] installing MCP: $NAME ${LINE:+(정의와 다름 → 재등록)}" >> "$LOG"
    [ -n "$LINE" ] && claude mcp remove "$NAME" -s user >> "$LOG" 2>&1
    # MSYS_NO_PATHCONV: /c 경로 변환 차단 (이게 없으면 cmd /c → cmd C:/)
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" nohup bash -c "$CMD" >> "$LOG" 2>&1 &
    disown 2>/dev/null || true
  done
  # R357: cmd /c npx 로 등록된 MCP → 고정 위치 node 직접 실행 (서버당 약 100MB·프로세스 3개 절약 · 하루 1번 · 응답 확인된 것만)
  if [ -f "$PROJECT_DIR/.claude/scripts/mcp-direct-launch.py" ]; then
    nohup python -X utf8 "$PROJECT_DIR/.claude/scripts/mcp-direct-launch.py" --auto >> "$LOG" 2>&1 &
    disown 2>/dev/null || true
  fi
fi

exit 0
