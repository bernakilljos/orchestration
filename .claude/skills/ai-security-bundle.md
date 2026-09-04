---
name: ai-security-bundle
description: AI 보안 신영역 통합 — Adversarial ML·AI Workload Protection·NHI·CSMA·DSPM·Mechanistic Interpretability·Deepfake Detection·Prompt Injection·Anti-Drone 등. 글로벌 OEM (Palo Alto·Wiz·Reality Defender·Lakera) 한국 통합 가이드. 사용자가 "AI 보안", "AI Workload", "NHI", "Deepfake", "Adversarial ML", "Interpretability" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: ai-security
  tags: [ai-security, oem, msp, deepfake, ai-workload]
---

# AI Security Bundle — 9 영역 통합 OEM 가이드

## 50 기술 매핑

| # | 기술 | OEM 후보 | 한국 진입 |
|---|---|---|---|
| 24 | Prompt Injection Defense | Lakera·HiddenLayer·Protect AI | 없음 |
| 25 | Mechanistic Interpretability | Anthropic·Goodfire | 학계 |
| 26 | Deepfake Detection / C2PA | Reality Defender·Hive·Pindrop | 없음  |
| 31 | Adversarial ML Defense | Robust Intelligence·CalypsoAI | 없음 |
| 32 | AI Workload Protection | Palo Alto AI·Wiz AI·Aim Security | 없음  |
| 33 | Non-Human Identity (NHI) | Astrix·Oasis·Entro | 없음 |
| 34 | Cybersecurity Mesh Architecture | Fortinet·Cisco·Palo Alto | 추격 중 |
| 35 | DSPM | Cyera·Sentra·Varonis | 추격 중 |
| 47 | Bias Detection / Explainability | Fiddler·Arthur·H2O | 추격 중 |

## OEM 한국 1호 운영 모델

```text
글로벌 SaaS (예: Wiz AI)
        ↓
ITCEN CORE 가 한국 총판·MSP 운영
        ↓
한국 고객 (금융·공공·기업)
- 1차: 라이선스 재판매
- 2차: 한국 환경 설정·운영
- 3차: 한국 컴플라이언스 매핑 (금감원·KISA)
- 4차: 사고 대응 24/7
```

## 영역별 OEM 추천 + 한국 시장

### 1. Deepfake Detection  (보이스피싱법 2026 의무)

**OEM 후보**:
- **Reality Defender** — 다중 모달 (음성·영상·문서)
- **Pindrop** — 음성 위조 (콜센터)
- **Hive** — 비전 워터마킹
- **Sensity** — 영상 + 합성 미디어

**한국 사업화**:
- 금융권 보이스피싱법 2026 의무 — 모든 은행·증권사
- 법무·회계 문서 위조 검증
- 정치권 선거 미디어 검증 (2027 대선)

```bash
# Reality Defender SDK 예시
pip install realitydefender-sdk
```

### 2. AI Workload Protection  (Agentic AI 폭증)

**OEM 후보**:
- **Palo Alto Networks AI Security** — 종합
- **Wiz AI** — Cloud AI
- **Aim Security** — Prompt Injection 강함

**한국 사업화**:
- 모든 한국 기업이 ChatGPT·Claude·Gemini 도입 → 보호 필수
- ITCEN PNS 협업 (사이버보안 영역) + ITCEN CORE 운영

### 3. NHI (Non-Human Identity)

**OEM 후보**:
- **Astrix** — 종합 NHI
- **Oasis Security** — 서비스계정·OAuth
- **Entro** — secret·credential

**한국 사업화**:
- AI 에이전트·로봇·서비스계정 신원관리 — 모든 기업 필수
- 금감원·KISA 가이드 대응

### 4. Mechanistic Interpretability  (EU AI Act 의무)

**도구**:
- **Anthropic Mech Interp** — 학술 도구 (오픈)
- **Goodfire** — 상용 해석
- **Captum** (Meta) — PyTorch 해석

**한국 사업화**:
- EU AI Act 2027 고위험 의무 충족
- 금감원 AI 거버넌스 — 결정 설명 가능성

### 5. Adversarial ML Defense

**OEM**:
- **Robust Intelligence** — 모델 audit
- **CalypsoAI** — 엔터프라이즈
- **HiddenLayer** — 런타임 보호

### 6-9. CSMA·DSPM·Bias·Anti-Drone

| 영역 | OEM | 한국 |
|---|---|---|
| **CSMA** | Fortinet·Cisco SCA | ITCEN PNS 협업 |
| **DSPM** | Cyera·Sentra·Varonis | 개인정보위 대응 |
| **Bias Detection** | Fiddler·Arthur·H2O | EU AI Act 의무 |
| **Anti-Drone** | Anduril·Dedrone·DroneShield | 군·공항 입찰 |

## 통합 OEM 사업 모델

```text
Phase 1: 한국 1호 파트너 인증 (각 OEM)
Phase 2: ITCEN CORE 가 운영·통합·한국화
Phase 3: 한국 고객사 직판·MSP
Phase 4: 컨소시엄 (보안 OEM 5-10개 통합 패키지)

매출:
- 라이선스 재판매: 30-40% 마진
- MSP 운영: 월구독
- 통합 컨설팅: 1社 3-10억
```

## ITCEN PNS 협업 (그룹 시너지)

- ITCEN PNS = 사이버보안 전문
- ITCEN CORE = 솔루션 통합·운영
- 그룹 자원 활용 시 한국 1위 AI 보안 종합 회사 가능

## AI Risk Lighthouse 카테고리 #4 (Interpretability 12%) + #7 (Quality 11%) 충족

OEM 통합 시 두 카테고리 ≥ 80점.

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | Top 3 OEM 파트너십 등록 (Reality Defender·Wiz·Astrix) | 1개월 |
| 2 | 한국 PoC 환경 구축 | 2개월 |
| 3 | 첫 고객사 통합 (베타) | 3개월 |
| 4 | 한국 MSP 운영 본격 | 6개월 |

## 트리거

- "AI 보안", "AI Security"
- "AI Workload Protection", "Wiz AI"
- "NHI", "Non-Human Identity"
- "Deepfake", "Reality Defender"
- "Adversarial ML", "Prompt Injection"
- "Interpretability", "SHAP"
- "Anti-Drone"

## 참조

- Palo Alto AI Security
- Wiz AI Security: https://www.wiz.io/
- Reality Defender: https://realitydefender.com/
- Astrix Security: https://astrix.security/
- `solution-capability-audit.md` #24-26, #31-35, #47 ( →  OEM 가이드)
