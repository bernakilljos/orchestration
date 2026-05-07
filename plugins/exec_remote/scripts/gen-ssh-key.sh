#!/usr/bin/env bash
# =====================================================
# gen-ssh-key.sh — ED25519 키 생성 + ~/.ssh/config 등록
# Usage: bash plugins/exec_remote/scripts/gen-ssh-key.sh [host_label] [vps_ip]
# Defaults: host_label=orch-vps, vps_ip=<empty> (수동 채움 안내)
# =====================================================
set -euo pipefail

HOST_LABEL="${1:-orch-vps}"
VPS_IP="${2:-}"
KEY_NAME="oracle_orch_ed25519"
SSH_DIR="${HOME}/.ssh"
KEY_PATH="${SSH_DIR}/${KEY_NAME}"
CONFIG="${SSH_DIR}/config"

mkdir -p "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

# 1. 키 생성 (이미 있으면 묻기)
if [ -f "${KEY_PATH}" ]; then
  echo "[!] 기존 키 존재: ${KEY_PATH}"
  read -p "    덮어쓰시겠습니까? (y/N): " yn
  if [[ ! "${yn}" =~ ^[Yy]$ ]]; then
    echo "[*] 기존 키 유지. 다음 단계 진행."
  else
    rm -f "${KEY_PATH}" "${KEY_PATH}.pub"
  fi
fi

if [ ! -f "${KEY_PATH}" ]; then
  COMMENT="orch-$(hostname)-$(date +%Y%m%d)"
  echo "[+] ED25519 키 생성: ${KEY_PATH}"
  echo "    (패스프레이즈 빈 줄도 허용)"
  ssh-keygen -t ed25519 -C "${COMMENT}" -f "${KEY_PATH}"
  chmod 600 "${KEY_PATH}"
  chmod 644 "${KEY_PATH}.pub"
fi

# 2. ~/.ssh/config 에 Host 블록 추가
touch "${CONFIG}"
chmod 600 "${CONFIG}"

if grep -q "^Host ${HOST_LABEL}$" "${CONFIG}" 2>/dev/null; then
  echo "[*] ${CONFIG} 에 'Host ${HOST_LABEL}' 이미 등록됨 — 변경 없음"
else
  cat >> "${CONFIG}" <<EOF

Host ${HOST_LABEL}
    HostName ${VPS_IP:-<VPS_HOST_IP>}
    User ubuntu
    IdentityFile ${KEY_PATH}
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 30
EOF
  echo "[+] ${CONFIG} 에 Host ${HOST_LABEL} 추가"
fi

# 3. 공개키 출력
echo
echo "===== 공개키 (Oracle 콘솔 'SSH Keys' 에 붙여넣기) ====="
cat "${KEY_PATH}.pub"
echo "======================================================"
echo

if [ -z "${VPS_IP}" ]; then
  echo "[i] VPS Public IP 받으면 다음 명령으로 자동 채움:"
  echo "    sed -i 's|<VPS_HOST_IP>|<실제IP>|' ${CONFIG}"
fi

echo "[OK] 다음: /exec_remote-deploy (또는 ssh ${HOST_LABEL} 으로 접속 테스트)"
