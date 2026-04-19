#!/bin/bash
# install.sh — Orchestration Kit 설치 (macOS/Linux용. Windows는 setup/setup.bat)
#
# 기능:
#   1. 의존성 확인 (python3, git, bash)
#   2. ~/.claude/orca/ 전역 큐 디렉토리 생성
#   3. plugins/ → .claude/ 초기 sync
#   4. 환경변수 템플릿 (.env.example) 생성
#   5. 검증 (validate-plugin-schema.py)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "=== Orchestration Kit Install ==="
echo "  위치: $REPO_ROOT"
echo ""

# ------------------------------------------
# 1. 의존성 확인
# ------------------------------------------
echo "[1/5] 의존성 확인..."
MISS=0
for cmd in git bash; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "   ❌ $cmd 없음"
    MISS=$((MISS+1))
  fi
done
if command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then
  echo "   ✓ python OK"
else
  echo "   ❌ python 없음"
  MISS=$((MISS+1))
fi
if [ $MISS -gt 0 ]; then
  echo "필수 도구 $MISS 개 누락. 설치 후 재시도."
  exit 1
fi
echo "   ✓ 의존성 OK"
echo ""

# ------------------------------------------
# 2. 전역 orca 큐 디렉토리
# ------------------------------------------
echo "[2/5] 전역 orca 큐 생성..."
mkdir -p ~/.claude/orca/tasks ~/.claude/orca/done ~/.claude/orca/locks ~/.claude/orca/logs
[ -f ~/.claude/orca/workers-config.json ] || cat > ~/.claude/orca/workers-config.json <<'EOF'
{
  "max_workers": { "codex": 4, "gemini": 2, "claude": 2 },
  "heartbeat_interval_sec": 30
}
EOF
echo "   ✓ ~/.claude/orca/ 준비 완료"
echo ""

# ------------------------------------------
# 3. plugins → .claude sync
# ------------------------------------------
echo "[3/5] 플러그인 동기화..."
bash .claude/scripts/sync-plugins.sh | tail -8
echo ""

# ------------------------------------------
# 4. .env.example 생성
# ------------------------------------------
echo "[4/5] 환경변수 템플릿..."
if [ ! -f .env.example ]; then
  cat > .env.example <<'EOF'
# Orchestration Kit 환경변수
# 필요한 것만 복사해서 .env 파일 생성 후 실제 값 입력

# === 핵심 AI API ===
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...

# === Phase 1 (로드맵) ===
YT_API_KEY=                 # YouTube Data API v3
YT_OAUTH_CLIENT_ID=
YT_OAUTH_CLIENT_SECRET=

# === MCP 서버 (선택) ===
GITHUB_TOKEN=
FIGMA_TOKEN=
CANVA_API_KEY=

# === DB (선택) ===
DATABASE_URL=
EOF
  echo "   ✓ .env.example 생성됨 (복사해서 .env 만든 뒤 값 입력)"
else
  echo "   ✓ .env.example 이미 있음"
fi
echo ""

# ------------------------------------------
# 5. 검증
# ------------------------------------------
echo "[5/5] 스키마 검증..."
PY=$(command -v python || command -v python3)
if [ -n "$PY" ] && [ -f .claude/scripts/validate-plugin-schema.py ]; then
  $PY .claude/scripts/validate-plugin-schema.py | tail -20
else
  echo "   ⏭  검증 스크립트 건너뜀"
fi
echo ""

echo "=== 설치 완료 ==="
echo ""
echo "다음 단계:"
echo "  1. cp .env.example .env && vi .env      # API 키 입력"
echo "  2. guide.txt 읽기"
echo "  3. Claude Code 세션 시작 → exec_orca-auto 자동 동작"
