---
description: SSH 키 생성 (ED25519) + ~/.ssh/config Host 블록 자동 등록 + 권한 600 정리
allowed-tools: Bash(ssh-keygen:*), Bash(ssh:*), Bash(chmod:*), Bash(cat:*), Bash(test:*), Read, Write, Edit
---

## Context

- 기존 키: !`ls ~/.ssh/oracle_orch_ed25519 2>/dev/null && echo "EXISTS" || echo "NEW"`
- 기존 config: !`grep -l "Host oracle\|Host orch-vps" ~/.ssh/config 2>/dev/null || echo "none"`
- ssh-keygen: !`where ssh-keygen 2>/dev/null && echo OK || echo MISSING`

## Your task

### 1. 키 생성 (없으면)

```bash
bash plugins/exec_remote/scripts/gen-ssh-key.sh
```

스크립트가 하는 일:
- `~/.ssh/oracle_orch_ed25519` (키 이름 충돌 시 사용자 확인)
- 패스프레이즈 묻기 (선택, 빈 줄도 허용)
- 권한 600 / 폴더 700 자동
- `~/.ssh/config` 에 다음 블록 추가 (이미 있으면 skip):

```
Host orch-vps
    HostName <VPS_HOST>            # 사용자에게 IP 받아 채움
    User ubuntu
    IdentityFile ~/.ssh/oracle_orch_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 30
```

### 2. 사용자에게 공개키 보여주기

```bash
cat ~/.ssh/oracle_orch_ed25519.pub
```

> "이 공개키를 Oracle 콘솔의 VM 생성 화면 'SSH Keys' 에 붙여넣으세요."

### 3. VPS_HOST 받으면 config 업데이트

사용자가 IP 알려주면:
- `~/.ssh/config` 의 `HostName <VPS_HOST>` 자리에 IP 치환
- `.env` 또는 `docs/ini/vps.ini` 에 다음 저장:
  ```
  VPS_HOST=<IP>
  VPS_USER=ubuntu
  VPS_SSH_KEY=~/.ssh/oracle_orch_ed25519
  ```

### 4. 첫 접속 테스트

```bash
ssh orch-vps "uname -a && uptime"
```

성공하면:
- `/exec_remote-deploy` 로 이동 안내
- 실패 시: 키 권한·VM 보안그룹 22 포트·키 등록 여부 순서대로 점검
