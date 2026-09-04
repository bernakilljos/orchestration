---
name: ai-governance-iso42001
description: ISO 42001 AI 관리시스템 + EU AI Act + 금감원 AI 거버넌스 + Bias Detection + Explainability 통합 거버넌스. IBM watsonx.governance·Credo AI·Holistic AI 활용. 사용자가 "AI Governance", "ISO 42001", "EU AI Act", "Bias Detection", "Explainability", "AI 거버넌스" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: governance
---

# AI Governance Bundle — ISO 42001·EU AI Act·금감원

## 50 기술 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 46 | AI Governance Platforms | IBM watsonx.governance·Credo AI·Holistic AI |
| 47 | Bias Detection / Explainability | Fiddler·Arthur·H2O·SHAP·LIME |

## 의무화 일정

| 법규·표준 | 발효 | 영향 |
|---|---|---|
| EU AI Act | 2025-02 / 2026-08 GPAI / **2027-08 고위험 의무** | 한국 EU 수출 의무 |
| **ISO 42001** | 2024 발행 / **2026-2027 한국 도입** | 모든 AI 사용 기업 |
| 금감원 AI 거버넌스 | **2026 발효** | 모든 금융사 |
| 개인정보 AI 영향평가 | **2026-2027 의무화** | 모든 AI 도입 기업 |

→ **2026-2027 한국 모든 대기업이 도입 의무**. ITCEN CORE 1위 base = 즉시 사업화.

## ISO 42001 핵심 요구사항

| 영역 | 요구 |
|---|---|
| **거버넌스 위원회** | AI 정책·책임자·감사 |
| **AI 라이프사이클 관리** | 설계·학습·검증·배포·모니터·은퇴 |
| **모델 카드** | 학습 데이터·성능·한계·편향 |
| **위험 평가** | 정기 risk assessment + 완화책 |
| **모니터링** | 운영 중 성능·드리프트·편향 자동 추적 |
| **인증 audit** | 외부 인증기관 audit |

## 우리 솔루션 자산 활용 

| ISO 요구 | 우리 자산 |
|---|---|
| 모델 카드 | `validate-plugin-schema.py` 패턴 → AI 모델 schema |
| 라이프사이클 | `.claude-plugin/plugin.json` precedence·status·version |
| 헌법화 | `.claude/rules/*.md` (Constitutional AI) |
| 위반 자동 차단 | `approval-gate.py` 패턴 |
| 정기 audit | `sync-plugins.sh --check` 패턴 → AI 모델 drift 감지 |
| 학습 패턴 | `learn` skill → 사고·실패 영구 기록 |

→ **우리 패턴 그대로 부서 AI 거버넌스에 이식 가능**. 추가 R&D 없음.

## Bias Detection · Explainability 도구

```bash
pip install shap lime fairlearn

# OSS — 즉시 사용
```

```python
import shap

# Bias detection (Fairlearn)
from fairlearn.metrics import demographic_parity_difference
dpd = demographic_parity_difference(y_true, y_pred, sensitive_features=gender)
# < 0.1 = OK / > 0.2 = bias 위험

# Explainability (SHAP)
explainer = shap.Explainer(model)
shap_values = explainer(X_test)
# 결정 근거 시각화 + EU AI Act 의무 충족
```

## OEM SaaS (구매 가능)

| 회사 | 특징 | 한국 진입 |
|---|---|---|
| **IBM watsonx.governance** | 종합 (정책·audit·모델 카드) | 추격 중 |
| **Credo AI** | 위험·컴플라이언스 자동 | 없음  |
| **Holistic AI** | EU AI Act 특화 | 없음  |
| **Fiddler** | Bias·Explainability | 추격 중 |
| **Arthur** | 모델 모니터 | 추격 중 |

→ ITCEN CORE 가 Credo AI · Holistic AI **한국 1호 파트너** 가능.

## 사업 모델 (부서 즉시 사업화)

| 단계 | 매출 |
|---|---|
| **무료 진단** | 잠재 고객 AI 거버넌스 점수 측정 |
| **컨설팅** (1社 5천만~3억) | ISO 42001 인증 컨설팅 |
| **인증 대행** | 외부 인증기관 매칭·운영 |
| **SaaS 구독** (월 200만~) | 모델 카드·audit·모니터 자동화 |
| **K-AI Standard lobby** | 금감원·KISA 협력 |

→ 1社 5천만 × 1000社 = **500억 영구 매출**. ITCEN CORE EPM·Compliance 1위 채널 직판.

## AI Risk Lighthouse #4 (Interpretability 12%) + #6 (Compliance 10%)

| 카테고리 | 검사 |
|---|---|
| 모델 카드 작성? | ISO 42001 의무 |
| SHAP·LIME 설명? | EU AI Act 의무 |
| Bias 정기 audit? | demographic parity |
| 거버넌스 위원회? | 회사 정책 |
| 라이프사이클 추적? | plugin.json 패턴 |

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | ISO 42001 한국어 가이드·체크리스트 작성 | 1주 |
| 2 | SHAP·Fairlearn PoC (부서 UEBA 모델) | 2주 |
| 3 | Credo AI / Holistic AI 파트너십 등록 | 1개월 |
| 4 | 첫 고객사 ISO 42001 인증 컨설팅 | 3개월 |
| 5 | SaaS 자동화 (모델 카드·audit) | 6개월 |

## 트리거
- "AI Governance", "AI 거버넌스"
- "ISO 42001", "EU AI Act"
- "금감원 AI"
- "Bias Detection", "Fairlearn"
- "Explainability", "SHAP", "LIME"

## 참조
- ISO 42001:2024 (AI Management System)
- EU AI Act timeline
- IBM watsonx.governance
- `solution-capability-audit.md` #46-47 ( → )
- `constitutional-ai.md` (헌법화 패턴 연동)
