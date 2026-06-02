---
name: ai-risk-lighthouse
description: AI 시스템·내부통제·행동위험을 8 카테고리 가중점수로 자동 감사. Google Lighthouse 패턴을 AI 위험관리에 적용한 한국 표준 후보. 사용자가 "AI 위험 점수", "Risk Lighthouse", "내부통제 자동 감사", "ISO 42001 인증", "EU AI Act 컴플라이언스" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: ai-governance
  tags: [risk-management, governance, ueba, compliance]
---

# AI Risk Lighthouse — 8 카테고리 자동 감사

## 컨셉

Google Lighthouse 가 웹페이지 점수 (성능·접근성·SEO·PWA) 매기듯,
**회사의 AI·내부통제·행동위험을 8 카테고리 가중점수**로 자동 감사.

## 8 카테고리 + 가중치

| # | 카테고리 | 가중 | 검사 항목 |
|---|---|---|---|
| 1 | **Self-Critique** | 15% | AI 결정 2단계 검증·confidence 점수 공개·재시도 루프 |
| 2 | **Causal AI** | 15% | 인과 설명·DoWhy 적용·상관관계만 X |
| 3 | **Behavioral Coverage** | 15% | UEBA·VMS·CCTV·결재·감정 데이터 통합 |
| 4 | **Interpretability** | 12% | EU AI Act 의무·SHAP·LIME·모델 카드 |
| 5 | **Privacy (PET)** | 12% | Federated·Confidential·동형암호·차등프라이버시 |
| 6 | **Compliance** | 10% | 한국 법규·EU AI Act·금감원 가이드 자동 추적 |
| 7 | **Quality (FP/FN)** | 11% | 거짓양성·거짓음성 모니터·정기 audit |
| 8 | **Self-Improvement** | 10% | 실패 학습·Reflexion·learn skill 적용 |

## 점수 산정 알고리즘

```python
def lighthouse_score(target_system):
    scores = {}
    weights = {
        'self_critique': 0.15, 'causal': 0.15, 'coverage': 0.15,
        'interpretability': 0.12, 'privacy': 0.12, 'compliance': 0.10,
        'quality': 0.11, 'self_improvement': 0.10,
    }
    for cat, weight in weights.items():
        scores[cat] = audit_category(target_system, cat)  # 0-100
    total = sum(scores[c] * w for c, w in weights.items())
    return {
        'total': round(total),
        'categories': scores,
        'grade': grade(total),  # A 90+ / B 70-89 / C 50-69 / D <50
        'recommendations': diff_against_best_practice(scores),
    }
```

## 우리 솔루션 활용 (orchestration_v1)

| 카테고리 | 우리 자산 |
|---|---|
| Self-Critique | `haiku-validator.md` · `verify-subagent-confidence.sh` · `post-codex-verify.sh` |
| Causal AI | 신규 `causal-ai.md` skill 필요 (DoWhy 통합) |
| Behavioral Coverage | 부서 UEBA·VMS·CCTV 통합 매핑 필요 |
| Interpretability | `auto-planner` 5단계 plan = 결정 근거 명시 |
| Privacy | 신규 `pet-bundle.md` 필요 (Federated·Confidential·동형암호) |
| Compliance | `.claude/rules/*.md` = Constitutional AI 패턴 |
| Quality | `verify-image-fit·verify-docx·verify-render-coverage` 등 hook |
| Self-Improvement | `learn.md` skill + memory 시스템 |

→ **5/8 카테고리 이미 우리 자산에 있음**. 나머지 3 보강만 하면 즉시 사업화.

## 사업화 (부서)

| 단계 | 매출 모델 |
|---|---|
| 무료 진단 (Lead Gen) | 잠재 고객 위험점수 무료 측정 |
| 컨설팅 (1社 5천만~3억) | 8 카테고리 audit + 개선 권고 + 인증 |
| SaaS 구독 (월 200만~) | 점수 자동 업데이트·분기 audit·1000+社 |
| 한국 표준 라이선스 (영구) | KISA·금감원 등록 후 모든 한국 기업 의무 |

## 트리거

- "AI 위험 점수", "Risk Lighthouse"
- "내부통제 자동 감사", "AI 거버넌스 점검"
- "ISO 42001", "EU AI Act 컴플라이언스"
- "행동위험 + 인과 추론"
- "Self-Critique 다중 합의"

## 참조

- `plugins/exec_orch/skills/self-critique-loop.md`
- `plugins/exec_orch/skills/causal-ai.md`
- `plugins/exec_orch/skills/constitutional-ai.md`
- `plugins/ai_rag/skills/rag-graph.md` (GraphRAG)
- `docs/ssj/ai-tech-deep-dive-20.md` (Lighthouse 설계)
- `docs/ssj/solution-capability-audit.md` (적용 점검)
