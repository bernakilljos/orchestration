---
description: VPS 부트스트랩 + Claude Code 설치 + orchestration_v1 클론 + 초기 sync 자동화
allowed-tools: Bash(ssh:*), Bash(scp:*), Bash(rsync:*), Read, Write
---

## Context

- VPS 환경: !`grep -h "VPS_HOST" .env docs/ini/vps.ini 2>/dev/null | head -1 || echo "VPS_HOST NOT SET — run /exec_remote-ssh first"`
- 첫 접속 가능: !`ssh -o ConnectTimeout=5 -o BatchMode=yes orch-vps "echo ok" 2>/dev/null || echo "NEED ssh setup"`

## Your task

### 0. 사전 조건 체크

`VPS_HOST` 없거나 `ssh orch-vps` 실패 시 → `/exec_remote-ssh` 로 되돌리기.

### 1. bootstrap-vps.sh 업로드 + 실행

```bash
scp plugins/exec_remote/scripts/bootstrap-vps.sh orch-vps:~/bootstrap.sh
ssh orch-vps "bash ~/bootstrap.sh"
```

스크립트 내용:
- apt update + 필수 패키지 (git·tmux·python3·python3-pip·jq·curl·ufw·fail2ban·build-essential)
- Node 20 LTS (NodeSource 저장소)
- Claude Code: `curl -fsSL https://claude.ai/install.sh | sh`
- UFW 방화벽: 22(또는 변경 포트)·80·443 만 허용
- fail2ban 활성화

### 2. 우리 킷 배포

```bash
ssh orch-vps "git clone https://github.com/bernakilljos/orchestration.git ~/orch"
scp plugins/exec_remote/scripts/deploy-kit.sh orch-vps:~/orch/deploy.sh
ssh orch-vps "cd ~/orch && bash deploy.sh"
```

`deploy-kit.sh` 가 하는 일:
- `bash .claude/scripts/install.sh` (스캐폴드 검증·sync·env)
- `python .claude/scripts/init-state-db.py` (SQLite 초기화)
- `bash .claude/scripts/watchdog-start.sh` (워커 heartbeat 백그라운드)
- claude 인증 안내 (사용자가 토큰 직접 입력 필요 — 자동화 X)

### 3. 인증 (사용자 액션 필수)

```bash
ssh -t orch-vps "claude login"
```

- Claude Code 토큰 발급 URL 출력 → 로컬 브라우저로 열어 인증 → 콘솔에 토큰 붙여넣기
- 인증 후 `claude --version` 으로 검증

### 4. tmux 세션 시작

```bash
ssh orch-vps "tmux new -d -s claude 'cd ~/orch && claude'"
```

`/exec_remote-tmux` 로 attach 패턴 안내.

### 5. 완료 후 출력

> ✅ VPS 에 Claude Code + orchestration_v1 배포 완료.
> 다음:
> - 모바일 접속: `/exec_remote-mobile`
> - tmux 사용법: `/exec_remote-tmux`
> - 헬스체크: `/exec_remote-status`
