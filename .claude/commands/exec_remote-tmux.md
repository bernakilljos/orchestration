---
description: tmux 영속 세션 패턴 (main·claude·worker 3 세션) + 핵심 단축키 cheatsheet
allowed-tools: Bash(ssh:*), Read
---

## Context

- 활성 세션: !`ssh -o ConnectTimeout=3 orch-vps "tmux ls 2>/dev/null" || echo "VPS unreachable or tmux empty"`

## Your task

`tmux-workflow` 스킬에 정의된 3-세션 패턴을 사용자에게 적용 안내.

### 기본 3 세션 구조

| 세션 이름 | 용도 |
|---|---|
| `claude` | Claude Code 인터랙티브 (메인 작업) |
| `worker` | codex-auto·gemini-auto·watchdog 백그라운드 |
| `main` | 셸·git·로그 모니터링 |

### 1. 처음 만들기

```bash
ssh orch-vps
tmux new -s claude 'cd ~/orch && claude'
# Ctrl+b d  → detach (claude 는 살아있음)

tmux new -s worker -d 'cd ~/orch && bash .claude/scripts/watchdog-start.sh'
tmux new -s main -d
```

### 2. 다시 들어가기 (재접속 시)

```bash
ssh orch-vps
tmux ls                # 세션 목록
tmux attach -t claude  # claude 세션으로 진입
```

### 3. 핵심 단축키 (prefix = `Ctrl+b`)

| 키 | 동작 |
|---|---|
| `Ctrl+b d` | detach (세션은 살아있음) |
| `Ctrl+b s` | 세션 전환 (목록) |
| `Ctrl+b $` | 세션 이름 변경 |
| `Ctrl+b c` | 새 윈도 |
| `Ctrl+b ,` | 윈도 이름 변경 |
| `Ctrl+b %` | 페인 세로 분할 |
| `Ctrl+b "` | 페인 가로 분할 |
| `Ctrl+b ←/→/↑/↓` | 페인 이동 |
| `Ctrl+b [` | 스크롤 모드 (q 로 종료) |
| `Ctrl+b x` | 페인 종료 |
| `Ctrl+b &` | 윈도 종료 |

### 4. 폰에서 단축키 누르기

Termius/Blink Shell 모두 키보드 위 툴바에 `Ctrl·b` 버튼 있음.
없으면 키보드 매핑(Termius 설정) 에서 추가:
- `Esc` → `Ctrl+b` 매핑하면 한 손 운용 편함

### 5. .tmux.conf 권장 (deploy 가 자동 설치)

```
set -g mouse on                          # 마우스/터치 스크롤
set -g history-limit 50000               # 스크롤백 길게
set -g status-interval 5                 # 상태바 5초
set -g default-terminal "tmux-256color"  # 컬러
bind r source-file ~/.tmux.conf \; display "Reloaded"
```

### 6. 끊김 대비 (Mosh — 선택)

지하철·해외·끊기는 와이파이 환경:

```bash
ssh orch-vps "sudo apt install -y mosh"
ssh orch-vps "sudo ufw allow 60000:61000/udp"
mosh ubuntu@<VPS_HOST> -- tmux attach -t claude
```

UDP 60000~61000 포트가 모바일 IP 변경에도 자동 재연결.

### 7. 사용자에게 안내

> tmux 세팅 끝나면 Ctrl+b d 로 빠져나오고 ssh 종료해도 작업 유지됩니다.
> 다음 접속 때는 `tmux attach -t claude` 만 하면 끝.
