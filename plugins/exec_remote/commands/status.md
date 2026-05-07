---
description: VPS 상태 한눈에 — 핑·uptime·CPU/RAM·claude 프로세스·tmux 세션·heartbeat
allowed-tools: Bash(ssh:*), Bash(ping:*), Read
---

## Context

- VPS 호스트: !`grep -h "VPS_HOST" docs/ini/vps.ini .env 2>/dev/null | head -1 || echo "not set"`
- 핑: !`ping -n 1 -w 2000 orch-vps 2>/dev/null | grep -i "time=" || ping -c 1 -W 2 orch-vps 2>/dev/null | grep -i "time=" || echo "unreachable"`
- ssh 원격 한 줄: !`ssh -o ConnectTimeout=5 -o BatchMode=yes orch-vps "uptime; free -h | head -2; tmux ls 2>/dev/null; pgrep -af claude | head -3" 2>/dev/null || echo "ssh failed"`

## Your task

위 컨텍스트를 사용자에게 표로 정리:

### 출력 포맷

```
🌐 VPS:        <VPS_HOST>
⏱  Uptime:     <uptime>
💾 RAM:        <free 결과>
🔥 Load:       <1m / 5m / 15m>
🪟 tmux:       <세션 수> (claude / worker / main)
🤖 Claude:     <pid 수>
📦 Heartbeat:  <ssh orch-vps "cat ~/orch/.claude/orca-heartbeat" 결과>
💰 Cost(MTD):  <Oracle 무료면 $0, 아니면 추정>
```

### 비정상 감지 시 액션 추천

| 증상 | 추천 액션 |
|---|---|
| 핑 실패 | 콘솔에서 VM 상태 확인 → reboot |
| ssh 실패 | 보안그룹 22 포트 / fail2ban ban 여부 |
| RAM <10% | `tmux kill-session` 으로 안 쓰는 세션 정리 |
| Claude 프로세스 0 | `tmux attach -t claude` → claude 재시작 |
| Heartbeat 5분 이상 정지 | `bash .claude/scripts/watchdog-start.sh` 재실행 |

### 비용 모니터 (Oracle 무료 사용 시)

```bash
ssh orch-vps "cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null"
```

ARM Ampere A1 = Always Free 한도 내.
Boot volume 200GB·Block storage 200GB·Outbound traffic 10TB/월 모두 무료 한도 안.
초과 위험은 outbound 트래픽뿐 — 정상 사용 시 도달 불가.
