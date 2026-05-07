---
name: tmux-workflow
description: tmux 영속 세션 패턴 (claude·worker·main 3 세션) + 폰 친화 단축키. 세션·attach·detach·끊김·persistent 언급 시 활성화.
---

## Trigger

- "tmux", "세션 유지", "끊겨도", "attach", "detach", "ssh 끊기면"
- `/exec_remote-tmux` 자동 참조

## 3 세션 패턴

| 세션 | 역할 | 시작 명령 |
|---|---|---|
| `claude` | Claude Code 인터랙티브 | `tmux new -s claude 'cd ~/orch && claude'` |
| `worker` | watchdog·codex-auto·gemini-auto | `tmux new -s worker -d 'cd ~/orch && bash .claude/scripts/watchdog-start.sh'` |
| `main` | 셸·git·로그 | `tmux new -s main -d` |

## 핵심 라이프사이클

### 처음 만들기 (deploy 후 1회)
```bash
ssh orch-vps
tmux new -s claude 'cd ~/orch && claude'
# (Claude 인증 페이지 로컬 브라우저로 → 토큰 입력)
# Ctrl+b d → detach
tmux new -s worker -d 'cd ~/orch && bash .claude/scripts/watchdog-start.sh'
tmux new -s main -d
exit  # ssh 종료해도 세션 살아있음
```

### 다시 들어가기
```bash
ssh orch-vps
tmux ls                # claude·worker·main 모두 보임
tmux attach -t claude  # 작업 이어서
```

### 분리 / 종료
- `Ctrl+b d` — detach (세션 살아있음, 권장)
- `tmux kill-session -t main` — 명시적 종료
- `tmux kill-server` — 모든 세션 종료 (재부팅 효과, 비추)

## 모바일 친화 키 매핑

`~/.tmux.conf` 권장:

```bash
# 마우스/터치 스크롤
set -g mouse on

# prefix 변경 (Ctrl+b 누르기 어려운 폰)
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# 페인 분할 직관적 키
bind | split-window -h
bind - split-window -v

# 세션 전환 빠르게
bind s choose-session

# 스크롤백
set -g history-limit 50000

# 컬러
set -g default-terminal "tmux-256color"
set -ga terminal-overrides ",xterm-256color:Tc"

# 상태바
set -g status-interval 5
set -g status-left "#[fg=cyan]#S #[fg=white]| "
set -g status-right "#[fg=yellow]%H:%M #[fg=cyan]| #(uptime | awk -F'load average:' '{print $2}')"

# 리로드
bind r source-file ~/.tmux.conf \; display "Reloaded"
```

## 끊김 대비 — Mosh

지하철·해외 로밍·끊기는 와이파이:

```bash
ssh orch-vps "sudo apt install -y mosh && sudo ufw allow 60000:61000/udp"
mosh ubuntu@<VPS_HOST> -- tmux attach -t claude
```

- 모바일 IP 변경에도 자동 재연결
- Termius·Blink Shell 모두 mosh 지원

## 자주 쓰는 패턴

### Claude 가 응답 안 함 / 멈춤
```bash
tmux attach -t claude
# Ctrl+c 로 현재 입력 취소
# /clear 또는 Ctrl+d 로 새 세션
```

### 백그라운드 작업 모니터
```bash
tmux attach -t worker
# Ctrl+b [ 로 스크롤 모드, q 로 종료
```

### 동시에 여러 화면 보기 (페인 분할)
```bash
tmux attach -t main
# Ctrl+b | (커스텀) 또는 Ctrl+b % → 세로 분할
# Ctrl+b - 또는 Ctrl+b "    → 가로 분할
# Ctrl+b 화살표 로 페인 이동
```

## 부팅 시 자동 복구

VPS 재부팅 시 세션 자동 생성 (systemd):

```bash
sudo tee /etc/systemd/system/claude-tmux.service <<'EOF'
[Unit]
Description=Claude tmux session
After=network.target

[Service]
Type=forking
User=ubuntu
ExecStart=/usr/bin/tmux new-session -d -s claude 'cd /home/ubuntu/orch && claude'
ExecStop=/usr/bin/tmux kill-session -t claude
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable claude-tmux.service
```

## 안티패턴

- ❌ `nohup` 만 사용 (tmux 가 더 직관적·재진입 쉬움)
- ❌ `screen` 신규 도입 (tmux 가 표준, screen 은 레거시)
- ❌ 세션 이름 없이 만들기 (`tmux new` → `0`, `1` 헷갈림)
