---
name: ai-biometric-auth
description: Behavioral Biometrics·Continuous Authentication·Passkeys/FIDO2 통합 — 타이핑·마우스·걸음·심박변동으로 상시 인증. VMS·금융·카지노 차세대 인증. 사용자가 "Behavioral Biometrics", "상시 인증", "Continuous Authentication", "Passkeys", "FIDO2" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: authentication
---

# Biometric Auth Bundle — 행동·상시·비밀번호 종말

## 50 기술 매핑

| # | 기술 | OEM |
|---|---|---|
| 36 | Behavioral Biometrics | BioCatch·Nuance·Mastercard |
| 37 | Continuous Authentication | Plurilock·Cognito |
| 38 | Passkeys / FIDO2 | FIDO Alliance·Apple·Google·1Password |

## 통합 인증 흐름

```text
초기 로그인 (Passkeys/FIDO2 — 비밀번호 X)
        ↓
세션 내 상시 검증 (타이핑·마우스 패턴)
        ↓
이상행동 탐지 (UEBA + Behavioral Biometrics)
        ↓
위험 ≥ 임계 → Step-up 인증 (생체 추가)
```

## ITCEN CORE 적용

| 영역 | 결합 |
|---|---|
| 금융 VMS | Continuous + Behavioral = 차세대 인증 |
| 카지노 VMS | 딜러·VIP 상시 신원 검증 |
| 내부회계 | 결재·승인 시 상시 생체 (위변조 방지) |
| 부서 행동위험 | UEBA + 타이핑/마우스 패턴 IP 확장 |

## 도입 OEM

```bash
# Behavioral — BioCatch 한국 파트너
# https://www.biocatch.com/

# Passkeys — FIDO2 무료 표준
# 자체 구현 또는 1Password·Auth0

# Continuous — Plurilock SDK
```

## Step-by-Step

| Phase | 작업 |
|---|---|
| 1 | FIDO2 Passkeys 자체 구현 (무료, 1개월) |
| 2 | BioCatch 또는 자체 행동 패턴 모델 PoC |
| 3 | VMS 통합 (카지노·금융) |
| 4 | 차세대 인증 표준 lobby (금감원) |

## AI Risk Lighthouse #3 (Coverage 15%) 보강

행동 차원에 상시 인증 데이터 추가.

## 트리거
- "Behavioral Biometrics", "상시 인증"
- "Continuous Auth", "Passkeys", "FIDO2"

## 참조
- BioCatch·Nuance·1Password Passkeys
- `solution-capability-audit.md` #36-38 (❌ → 🟡)
