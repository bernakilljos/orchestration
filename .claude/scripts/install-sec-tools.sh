#!/usr/bin/env bash
# install-sec-tools.sh — sec_scan 도구 자동 설치 (멱등)
#
# 설치:
#   - semgrep / bandit  → pip --user
#   - gitleaks          → GitHub release binary (OS 감지)
#
# 호출:
#   - SessionStart hook (백그라운드)
#   - sec_scan hook 첫 발동 시
#
# Idempotent: .claude/state/.sec-tools-installed flag 로 추적
set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
STATE_DIR="${PROJECT_ROOT}/.claude/state"
TOOLS_DIR="${STATE_DIR}/tools"
mkdir -p "$LOG_DIR" "$STATE_DIR" "$TOOLS_DIR"

LOG="${LOG_DIR}/sec-tools-install.log"
FLAG="${STATE_DIR}/.sec-tools-installed"

# Sub-project guard
[ -d "${PROJECT_ROOT}/plugins" ] || exit 0

# 강제 재설치: --force 또는 flag 없을 때만
if [ "${1:-}" != "--force" ] && [ -f "$FLAG" ]; then
  # 매일 한 번만 verify
  AGE=$(( $(date +%s) - $(stat -c %Y "$FLAG" 2>/dev/null || stat -f %m "$FLAG" 2>/dev/null || echo 0) ))
  [ "$AGE" -lt 86400 ] && exit 0
fi

echo "===== [$(date +%F_%T)] sec-tools install start =====" >> "$LOG"

# OS 감지
OS_KIND="unknown"
case "$(uname -s 2>/dev/null)" in
  MINGW*|CYGWIN*|MSYS*) OS_KIND="windows" ;;
  Linux*)               OS_KIND="linux" ;;
  Darwin*)              OS_KIND="darwin" ;;
esac
echo "[$(date +%F_%T)] OS: $OS_KIND" >> "$LOG"

# ───────────────────────────────────────────────────────────
# 1. Python 도구 (bandit, semgrep)
# ───────────────────────────────────────────────────────────
if command -v pip >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
  PIP_CMD=""
  command -v pip >/dev/null 2>&1 && PIP_CMD="pip"
  [ -z "$PIP_CMD" ] && command -v python >/dev/null 2>&1 && PIP_CMD="python -m pip"

  if [ -n "$PIP_CMD" ]; then
    # bandit (Python 코드 보안 — Windows OK)
    if ! python -c "import bandit" 2>/dev/null; then
      echo "[$(date +%F_%T)] installing bandit..." >> "$LOG"
      $PIP_CMD install --user --quiet bandit >>"$LOG" 2>&1 || echo "[WARN] bandit install fail" >> "$LOG"
    else
      echo "[$(date +%F_%T)] bandit already installed" >> "$LOG"
    fi

    # semgrep (Windows 에서는 제한적 — pip 시도, 실패 시 skip)
    if ! python -c "import semgrep" 2>/dev/null; then
      if [ "$OS_KIND" = "windows" ]; then
        echo "[$(date +%F_%T)] semgrep on Windows = limited support, attempting pip install" >> "$LOG"
      else
        echo "[$(date +%F_%T)] installing semgrep..." >> "$LOG"
      fi
      $PIP_CMD install --user --quiet semgrep >>"$LOG" 2>&1 || echo "[WARN] semgrep install fail (Windows limited)" >> "$LOG"
    else
      echo "[$(date +%F_%T)] semgrep already installed" >> "$LOG"
    fi
  else
    echo "[WARN] pip not found, skip python tools" >> "$LOG"
  fi
fi

# ───────────────────────────────────────────────────────────
# 2. gitleaks (GitHub release binary)
# ───────────────────────────────────────────────────────────
GITLEAKS_VER="8.21.2"

# 이미 PATH에 있으면 skip
if command -v gitleaks >/dev/null 2>&1; then
  echo "[$(date +%F_%T)] gitleaks found in PATH" >> "$LOG"
elif [ -x "$TOOLS_DIR/gitleaks" ] || [ -x "$TOOLS_DIR/gitleaks.exe" ]; then
  echo "[$(date +%F_%T)] gitleaks found in $TOOLS_DIR" >> "$LOG"
else
  URL=""
  ARCHIVE=""
  case "$OS_KIND" in
    windows) URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER}_windows_x64.zip"; ARCHIVE="$TOOLS_DIR/gitleaks.zip" ;;
    linux)   URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER}_linux_x64.tar.gz"; ARCHIVE="$TOOLS_DIR/gitleaks.tar.gz" ;;
    darwin)  URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER}_darwin_x64.tar.gz"; ARCHIVE="$TOOLS_DIR/gitleaks.tar.gz" ;;
    *)       echo "[WARN] OS unknown, gitleaks skip" >> "$LOG" ;;
  esac

  if [ -n "$URL" ] && command -v curl >/dev/null 2>&1; then
    echo "[$(date +%F_%T)] downloading gitleaks v${GITLEAKS_VER} ($OS_KIND)" >> "$LOG"
    curl -sSL --max-time 60 -o "$ARCHIVE" "$URL" >>"$LOG" 2>&1 || echo "[WARN] curl fail" >> "$LOG"

    if [ -f "$ARCHIVE" ]; then
      case "$ARCHIVE" in
        *.zip)
          if command -v unzip >/dev/null 2>&1; then
            unzip -o "$ARCHIVE" -d "$TOOLS_DIR" >>"$LOG" 2>&1 || echo "[WARN] unzip fail" >> "$LOG"
          else
            python -c "import zipfile; zipfile.ZipFile('$ARCHIVE').extractall('$TOOLS_DIR')" 2>>"$LOG" || echo "[WARN] python unzip fail" >> "$LOG"
          fi
          ;;
        *.tar.gz)
          tar -xzf "$ARCHIVE" -C "$TOOLS_DIR" >>"$LOG" 2>&1 || echo "[WARN] tar fail" >> "$LOG"
          ;;
      esac

      chmod +x "$TOOLS_DIR/gitleaks" 2>/dev/null || true
      rm -f "$ARCHIVE"

      if [ -x "$TOOLS_DIR/gitleaks" ] || [ -x "$TOOLS_DIR/gitleaks.exe" ]; then
        echo "[$(date +%F_%T)] gitleaks installed: $TOOLS_DIR/" >> "$LOG"
      else
        echo "[WARN] gitleaks extracted but not executable" >> "$LOG"
      fi
    fi
  else
    echo "[WARN] curl not available, gitleaks skip" >> "$LOG"
  fi
fi

# ───────────────────────────────────────────────────────────
# 3. 검증 (smoke test)
# ───────────────────────────────────────────────────────────
{
  echo "=== verify ==="
  # bandit: module + CLI 둘 다 시도
  python -m bandit --version 2>/dev/null | head -1 || \
    python -c "import bandit; print('bandit:', bandit.__version__)" 2>/dev/null || \
    echo "bandit: NOT FOUND"

  # semgrep: CLI 시도 (Windows 에서 import 실패해도 CLI 는 동작 가능)
  python -m semgrep --version 2>/dev/null | head -1 || \
    semgrep --version 2>/dev/null | head -1 || \
    echo "semgrep: NOT FOUND (Windows limitation — fallback regex 사용)"

  # gitleaks: PATH > TOOLS_DIR
  if command -v gitleaks >/dev/null 2>&1; then
    gitleaks version 2>&1 | head -1
  elif [ -x "$TOOLS_DIR/gitleaks.exe" ]; then
    "$TOOLS_DIR/gitleaks.exe" version 2>&1 | head -1
  elif [ -x "$TOOLS_DIR/gitleaks" ]; then
    "$TOOLS_DIR/gitleaks" version 2>&1 | head -1
  else
    echo "gitleaks: NOT FOUND"
  fi
} >> "$LOG" 2>&1

# 결과 export
export SEC_TOOLS_DIR="$TOOLS_DIR"

touch "$FLAG"
echo "===== [$(date +%F_%T)] sec-tools install done =====" >> "$LOG"
exit 0
