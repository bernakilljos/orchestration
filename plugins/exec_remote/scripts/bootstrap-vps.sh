#!/usr/bin/env bash
# =====================================================
# bootstrap-vps.sh — VPS 초기 패키지 + 보안 + Claude Code
# 실행 위치: VPS 안 (Ubuntu 22.04 / 24.04)
# Usage: bash bootstrap.sh
# =====================================================
set -euo pipefail

echo "=== [1/7] apt update + 필수 패키지 ==="
sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt -y full-upgrade
sudo apt install -y \
  git tmux mosh jq curl wget unzip \
  python3 python3-pip python3-venv \
  build-essential \
  ufw fail2ban \
  unattended-upgrades \
  ca-certificates gnupg

echo "=== [2/7] Node.js 20 LTS (NodeSource) ==="
if ! command -v node &>/dev/null || [[ "$(node -v 2>/dev/null)" != v20* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt install -y nodejs
fi
node -v
npm -v

echo "=== [3/7] Claude Code 설치 ==="
if ! command -v claude &>/dev/null; then
  curl -fsSL https://claude.ai/install.sh | sh
  # PATH 추가 (다음 셸부터 적용)
  if ! grep -q 'claude' "${HOME}/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${HOME}/.bashrc"
  fi
  export PATH="${HOME}/.local/bin:${PATH}"
fi
claude --version || echo "[!] claude 설치는 됐으나 인증 필요 — 'claude login'"

echo "=== [4/7] UFW 방화벽 ==="
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'ssh'
sudo ufw allow 80/tcp comment 'http'
sudo ufw allow 443/tcp comment 'https'
# Mosh
sudo ufw allow 60000:61000/udp comment 'mosh'
sudo ufw --force enable
sudo ufw status verbose

echo "=== [5/7] fail2ban (sshd) ==="
sudo tee /etc/fail2ban/jail.local >/dev/null <<'EOF'
[sshd]
enabled  = true
port     = ssh
maxretry = 5
findtime = 600
bantime  = 3600
EOF
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd || true

echo "=== [6/7] sshd 보안 (비밀번호 비활성, root 차단) ==="
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo systemctl restart sshd

echo "=== [7/7] tmux 기본 설정 ==="
if [ ! -f "${HOME}/.tmux.conf" ]; then
  cat > "${HOME}/.tmux.conf" <<'EOF'
set -g mouse on
set -g history-limit 50000
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
set -g status-interval 5
unbind C-b
set -g prefix C-a
bind C-a send-prefix
bind | split-window -h
bind - split-window -v
bind r source-file ~/.tmux.conf \; display "Reloaded"
EOF
fi

echo
echo "[OK] 부트스트랩 완료."
echo "다음:"
echo "  1) git clone https://github.com/bernakilljos/orchestration.git ~/orch"
echo "  2) cd ~/orch && bash ~/deploy.sh   (deploy-kit.sh)"
echo "  3) tmux new -s claude 'cd ~/orch && claude'   (인증)"
