#!/usr/bin/env bash
# =====================================================
# deploy-kit.sh — VPS 안에서 orchestration_v1 초기화
# 실행 위치: VPS 의 ~/orch (clone 직후)
# Usage: cd ~/orch && bash deploy.sh
# =====================================================
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"
echo "[i] Project root: ${PROJECT_ROOT}"

# 1) install.sh (scaffold·sync·env)
if [ -f ".claude/scripts/install.sh" ]; then
  echo "=== [1/4] install.sh ==="
  bash .claude/scripts/install.sh
else
  echo "[!] .claude/scripts/install.sh 없음 — sync-plugins.sh 만 실행"
  bash .claude/scripts/sync-plugins.sh
fi

# 2) SQLite 초기화
if [ -f ".claude/scripts/init-state-db.py" ]; then
  echo "=== [2/4] state DB 초기화 ==="
  python3 .claude/scripts/init-state-db.py
fi

# 3) Watchdog 백그라운드
if [ -f ".claude/scripts/watchdog-start.sh" ]; then
  echo "=== [3/4] watchdog 시작 ==="
  bash .claude/scripts/watchdog-start.sh &
fi

# 4) .env 템플릿 (있으면 skip)
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "[+] .env 생성 (.env.example 기준) — 값 채워주세요"
fi

# 5) Claude 인증 안내
echo
echo "=== [4/4] Claude 인증 (사용자 액션 필요) ==="
if ! claude --version &>/dev/null; then
  echo "[!] claude 미설치. bootstrap-vps.sh 먼저 실행 필요"
  exit 1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ ! -f "${HOME}/.claude/credentials.json" ]; then
  cat <<'EOF'

⚠ Claude Code 인증 필요. 다음 중 하나:
   A) tmux 세션에서 직접:
      tmux new -s claude 'cd ~/orch && claude login'
      → 출력된 URL 을 로컬 브라우저로 열고 토큰 받아 붙여넣기

   B) API 키 환경변수:
      export ANTHROPIC_API_KEY=sk-ant-...
      echo 'export ANTHROPIC_API_KEY=...' >> ~/.bashrc

EOF
fi

# 6) tmux 세션 자동 생성 (worker·main)
if command -v tmux &>/dev/null; then
  if ! tmux has-session -t worker 2>/dev/null; then
    tmux new-session -d -s worker "cd ${PROJECT_ROOT} && bash .claude/scripts/watchdog-start.sh; bash"
    echo "[+] tmux session 'worker' 시작"
  fi
  if ! tmux has-session -t main 2>/dev/null; then
    tmux new-session -d -s main -c "${PROJECT_ROOT}"
    echo "[+] tmux session 'main' 시작"
  fi
fi

echo
echo "[OK] 배포 완료. 다음:"
echo "   tmux new -s claude 'cd ${PROJECT_ROOT} && claude'   # 인증 후 작업 시작"
echo "   tmux ls                                              # 세션 목록"
echo "   /exec_remote-status                                   # 헬스체크"
