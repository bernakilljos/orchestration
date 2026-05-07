# exec_remote — 원격 24/7 운영

> **목적**: 내 PC 가 꺼져 있어도 Claude Code + 우리 킷이 클라우드에서 24시간 작동.
> **타깃**: Oracle Cloud Free Tier (1순위) · Vultr · AWS Lightsail.
> **결과물**: 스마트폰(Termius) → SSH → tmux → Claude Code 직통 라인.

---

## 빠른 흐름 (4단계)

```
1) /exec_remote-setup    → Oracle 가입 + VM 생성 가이드
2) /exec_remote-ssh      → SSH 키 자동 생성 + ~/.ssh/config 등록
3) /exec_remote-deploy   → VPS 에 Claude Code + 우리 킷 배포
4) /exec_remote-mobile   → 스마트폰 Termius 접속 세팅
```

작업 중 `/exec_remote-tmux` 로 영속 세션 만들고, `/exec_remote-status` 로 헬스체크.

---

## 커맨드

| 커맨드 | 역할 |
|---|---|
| `/exec_remote-setup` | Oracle Free Tier 가입 → ARM Ampere A1 VM(4 OCPU/24GB) 생성 절차 |
| `/exec_remote-ssh` | ED25519 키 생성 + `~/.ssh/config` Host 블록 자동 추가 |
| `/exec_remote-deploy` | `bootstrap-vps.sh` 업로드 → Node·git·tmux 설치 → 우리 킷 clone → sync |
| `/exec_remote-mobile` | Termius(iOS·Android)·iSH·Blink Shell 옵션별 단계 가이드 |
| `/exec_remote-tmux` | 영속 세션 패턴 (`main` / `claude` / `worker`) + cheatsheet |
| `/exec_remote-status` | 핑 + uptime + RAM/CPU + claude 프로세스 + heartbeat |

---

## 스킬

- **cloud-provider-select** — 무료/유료/사양·지역·결제 카드 매트릭스 (Oracle vs Vultr vs Lightsail)
- **ssh-hardening** — 키만 허용 / fail2ban / 포트 변경 / UFW 5분 셋업
- **tmux-workflow** — 윈도·페인 패턴, detach/attach, Mosh 옵션

---

## 스크립트

```
scripts/
├── gen-ssh-key.sh        ED25519 키 + ~/.ssh/config 등록
├── bootstrap-vps.sh      VPS 초기 패키지 (Node 20·Python·tmux·UFW·fail2ban)
└── deploy-kit.sh         orchestration_v1 clone → install → sync
```

---

## 환경 변수 (.env 또는 docs/ini)

```
VPS_HOST=123.45.67.89
VPS_USER=ubuntu
VPS_SSH_KEY=~/.ssh/oracle_orch_ed25519
```

---

## 연관 플러그인

- `exec_orch` — 의존 (워커 스폰 로직)
- `mcp_collab` — Telegram·Slack 알림 (3주차)
- `exec_session_guard` — VPS 세션 끊김 대비 스냅샷

---

## 비용 (2026-05 기준)

| 업체 | 사양 | 월 |
|---|---|---|
| **Oracle Free Tier** ⭐ | 4 OCPU ARM / 24GB | **$0** |
| Vultr | 1 vCPU / 1GB | $3.50 |
| AWS Lightsail | 1 vCPU / 1GB | $5 |
| Hetzner CX22 | 2 vCPU / 4GB | €4.51 |

> Oracle 무료 티어가 사양·가격 모두 압도적. 지역(서울 리전 가능) 선택 후 발급.

---

## 보안 체크리스트

- [ ] 비밀번호 로그인 비활성 (키만 허용)
- [ ] 기본 포트 22 → 임의 포트 변경 (예: 49222)
- [ ] UFW: 22(또는 변경 포트)·80·443 만 허용
- [ ] fail2ban 설치 (brute-force 차단)
- [ ] `.env` / `.ssh/` 권한 600 / 700
- [ ] PAT·API 키는 `docs/ini/` (gitignore) 에만 저장

---

## 참조

- 4주차 강의 매칭: `docs/2026-05-07/4주차-원격제어.md` (생성 예정)
- 라우팅: `plugins/exec_orch/skills/route_dispatch.md`
- 보안: `.claude/rules/best-practices.md` § 시크릿 관리
