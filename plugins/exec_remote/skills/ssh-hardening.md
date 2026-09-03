---
name: ssh-hardening
description: VPS SSH 보안 강화 — 키만 허용·포트 변경·UFW·fail2ban 5분 셋업. 보안·hardening·brute-force·무차별 공격 언급 시 활성화.
---

## Trigger

- "SSH 보안", "VPS 안전하게", "무차별 대입", "fail2ban", "포트 변경"
- `/exec_remote-deploy` 자동 참조

## 5분 셋업 체크리스트

### 1. 비밀번호 로그인 비활성

```bash
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
```

### 2. 포트 변경 (선택, 권장)

기본 22 → 49222 (1024~65535 사이 랜덤):

```bash
sudo sed -i 's/^#\?Port .*/Port 49222/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

 **주의**: 새 세션에서 새 포트로 접속 가능한지 먼저 확인하고 기존 세션 종료. UFW 도 새 포트 허용 후 22 차단해야 self-lockout 방지.

### 3. UFW 방화벽

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 49222/tcp comment 'ssh-custom'  # 또는 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Mosh 사용 시
# sudo ufw allow 60000:61000/udp
sudo ufw enable
sudo ufw status verbose
```

### 4. fail2ban (brute-force 차단)

```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local <<'EOF'
[sshd]
enabled = true
port    = 49222
maxretry = 5
findtime = 600
bantime = 3600
EOF
sudo systemctl enable --now fail2ban
sudo fail2ban-client status sshd
```

### 5. 자동 보안 업데이트

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 검증 체크

```bash
# 키 외 로그인 차단 확인
ssh -o PubkeyAuthentication=no orch-vps        # → "Permission denied"

# fail2ban jail 활성 확인
sudo fail2ban-client status sshd               # → 5번 실패 시 ban

# UFW 룰
sudo ufw status numbered                       # → 22 차단, 49222 허용
```

## 가지 말 것 (안티패턴)

-  `PermitRootLogin yes` (root 직접 로그인 → 자동공격 1순위)
-  약한 비밀번호 패스프레이즈로 키 보호 (또는 패스프레이즈 없음 + 키만 있는 USB 분실 시 즉시 노출)
-  ufw 활성 안 하고 sshd 만 셋업 (다른 포트 노출 위험)
-  22 포트 그대로 + fail2ban 없음 (분당 수백 시도 받음)

## 키 분실 / 분실 의심 시

```bash
# 모든 인가키 확인
ssh orch-vps "cat ~/.ssh/authorized_keys"

# 의심 라인 제거
ssh orch-vps "sed -i '/<comment_label>/d' ~/.ssh/authorized_keys"

# 새 키 발급 → 등록
bash plugins/exec_remote/scripts/gen-ssh-key.sh
ssh-copy-id -i ~/.ssh/oracle_orch_ed25519_v2.pub orch-vps
```

## 참조

- gen-ssh-key.sh — 키 라벨에 발급일·디바이스 자동 주석 (분실 추적용)
- bootstrap-vps.sh — 위 1·3·4 자동 적용
