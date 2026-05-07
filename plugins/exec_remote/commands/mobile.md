---
description: 스마트폰 (iOS·Android) 에서 VPS 접속 — Termius·Blink Shell·iSH 옵션별 단계 가이드
allowed-tools: Read
---

## Context

- VPS 등록: !`grep -h "VPS_HOST" docs/ini/vps.ini .env 2>/dev/null | head -1 || echo "MISSING — run /exec_remote-ssh"`
- 공개키: !`ls ~/.ssh/oracle_orch_ed25519.pub 2>/dev/null || echo "MISSING — run /exec_remote-ssh"`

## Your task

### 모바일 앱 비교

| 앱 | 플랫폼 | 무료? | 강점 | 권장 |
|---|---|---|---|---|
| **Termius** | iOS·Android·데스크톱 | ✅ 무료 (Pro 옵션) | 키 동기화·SFTP·snippets | ⭐ 1순위 |
| Blink Shell | iOS | $20 (한 번) | mosh·ssh-agent·터미널 품질 최상 | iOS 헤비유저 |
| Termux | Android | ✅ | 안드로이드 자체 리눅스 환경 | 안드로이드 파워유저 |
| iSH | iOS | ✅ | iOS 안에서 alpine 리눅스 | 학습용 |
| JuiceSSH | Android | ✅ | 가벼움 | Termius 대안 |

### 1. Termius 권장 흐름 (가장 빠름)

#### Step 1 — 앱 설치

- iOS: App Store → "Termius"
- Android: Play Store → "Termius"

#### Step 2 — 로컬 PC에서 키 export

```bash
cat ~/.ssh/oracle_orch_ed25519       # private key
cat ~/.ssh/oracle_orch_ed25519.pub   # public key (이건 VPS 에 이미 있음)
```

private key 전체 내용을 안전 채널로 폰으로 전송 (Apple 메모·iCloud 키체인·Bitwarden·1Password 권장 / 카톡·이메일 비추).

#### Step 3 — Termius 에 등록

1. Termius 앱 → **Keys** (왼쪽 메뉴)
2. **+ New Key** → Type: **ED25519** → Private Key 붙여넣기 → 저장
3. **Hosts** → **+ New Host**
   - Label: `orch-vps`
   - Address: `<VPS_HOST IP>`
   - Username: `ubuntu`
   - Key: 방금 등록한 ED25519 선택
4. 저장 → 호스트 탭하면 SSH 접속

#### Step 4 — tmux 자동 attach 스니펫

Termius **Snippets** 에 등록:

| Snippet | Command |
|---|---|
| claude attach | `tmux attach -t claude \|\| tmux new -s claude 'cd ~/orch && claude'` |
| status | `cd ~/orch && bash .claude/scripts/orca-status.sh` |
| godmode | `cd ~/orch && claude --print "/godmode"` |

호스트 접속 후 우상단 ⚡ 아이콘 → snippet 실행.

### 2. Blink Shell (iOS, 유료) 안내

- App Store → "Blink Shell" ($19.99)
- 설정 → SSH Keys → Generate or Import (위 키 가져오기)
- Hosts → Add → `orch-vps` (위 정보 동일)
- mosh 사용 권장: `mosh ubuntu@<IP>` (지하철·터널에서도 끊김 없음)

### 3. 보안 권장

- 폰 잠금 (Face ID·지문·PIN) **필수**
- Termius **Touch ID / Face ID 보호** 활성 (Settings → Security)
- 분실 시 즉시 VPS `~/.ssh/authorized_keys` 에서 해당 키 라인 삭제 (스크립트로 키마다 주석 라벨 남기는 게 좋음)

### 4. 완료 후

> ✅ 어디서든 폰으로 Claude Code 접속 가능.
> 다음:
> - 영속 세션 패턴: `/exec_remote-tmux`
> - 헬스체크: `/exec_remote-status`
