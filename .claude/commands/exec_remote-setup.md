---
description: VPS 가입 + VM 생성 단계별 안내 — Oracle Free Tier 1순위 (4 OCPU·24GB 무료)
allowed-tools: Bash(where:*), Read
---

## Context

- 사용자 OS: !`uname -s 2>/dev/null || echo Windows`
- ssh 클라이언트: !`where ssh 2>/dev/null && echo OK || echo MISSING`
- 기존 VPS 환경변수: !`grep -l "VPS_HOST" .env docs/ini/*.ini 2>/dev/null || echo "none"`

## Your task

`cloud-provider-select` 스킬을 활용해 사용자에게 다음 순서로 안내:

### 1. 업체 선택 (Oracle 1순위)

| 우선 | 업체 | 사양 | 월 |
|---|---|---|---|
| 🥇 | **Oracle Free Tier** | 4 OCPU ARM Ampere / 24GB / 200GB | **$0** |
| 🥈 | Vultr | 1 vCPU / 1GB / 25GB | $3.50 |
| 🥉 | AWS Lightsail | 1 vCPU / 1GB / 40GB | $5 |

> Oracle 무료가 단연 압도적이지만 카드 등록 + 발급 어려움 있음 → 막히면 Vultr 폴백.

### 2. Oracle 가입 절차 (안내)

1. https://signup.cloud.oracle.com 접속
2. 이메일 + 무료 평가판 등록 (해외결제 카드 필요, 청구는 안 됨)
3. **홈 리전: Seoul / Chuncheon** 선택 (한 번 선택하면 변경 불가, 한국이 가장 빠름)
4. 본인 인증 SMS + 카드 등록 (예치금 $0, 일시 1USD 검증 후 환불)
5. 콘솔 진입 후 **Compute → Instances → Create Instance**
6. **Image: Canonical Ubuntu 22.04** / **Shape: VM.Standard.A1.Flex** (ARM)
7. **OCPU=4, Memory=24GB** (무료 한도 최대)
8. SSH 키: `/exec_remote-ssh` 로 만든 공개키 붙여넣기 (먼저 ssh 커맨드 실행 권유)
9. 생성 → Public IP 메모

### 3. 다음 단계로 라우팅

설치 끝나면 사용자에게:
> "Public IP 받으셨으면 `/exec_remote-ssh` 실행 후, IP 알려주세요. `~/.ssh/config` 자동 등록할게요."

### 4. 막히면 Vultr 폴백 안내

Oracle 카드 거절·VM 생성 실패(out of capacity) 시:
- Vultr (https://vultr.com) → Cloud Compute → Seoul → Ubuntu 22.04 → $3.50 플랜
- 절차는 5분, 카드만 있으면 즉시 발급
