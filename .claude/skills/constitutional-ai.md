---
name: constitutional-ai
description: 부서 SOP·금감원 가이드·EU AI Act·ISO 42001 을 AI 가 따라야 할 헌법(원칙)으로 박고, AI 가 자기 답을 헌법에 비교·위반 시 자동 수정. Anthropic Constitutional AI 패턴을 컴플라이언스·내부통제에 적용. 사용자가 "Constitutional AI", "헌법화", "SOP 자동 준수", "법규 자동 준수", "원칙 기반 AI" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: governance
  tags: [constitutional-ai, compliance, sop, governance]
---

# Constitutional AI — 헌법 기반 자기 규제

## 원리

Anthropic 의 Constitutional AI (Bai et al. 2022) 패턴:

```text
1. 헌법 (원칙) 정의 — "AI 가 절대 위반 X 항목"
2. AI 가 답 생성
3. AI 가 자기 답을 헌법과 대조 → 위반 항목 식별
4. 위반 발견 시 답을 수정 → 재제출
5. RLHF 대신 RLAIF (AI Feedback) 로 학습 (선택)
```

→ 사람 RLHF 대비 비용 1/10, 일관성 ↑, 정책 변경 즉시 반영.

## 우리 솔루션이 이미 Constitutional AI 패턴 ✅

| 우리 자산 | Anthropic 패턴 대응 |
|---|---|
| `.claude/rules/failure-mode.md` | 거짓·헤지 금지 헌법 |
| `.claude/rules/best-practices.md` | 베스트프랙티스 헌법 |
| `.claude/rules/teaching-doc.md` | 교재 8섹션 의무 헌법 |
| `.claude/rules/cleanup-policy.md` | 정리 정책 헌법 |
| `.claude/hooks/check-mojibake.sh` | 헌법 위반 자동 차단 (PreToolUse) |
| `.claude/scripts/approval-gate.py` | 위험 명령 자동 거부 |
| `plugins/exec_orch/skills/auto-planner.md` | 5단계 자가 점검 (헌법 따라) |

→ **이미 Constitutional AI 시스템 구축됨**. 부서 SOP·법규만 같은 형식으로 추가하면 즉시 활용.

## 부서 헌법 작성 (실전 템플릿)

### `rules/dept-risk-sop.md` (부서 SOP 헌법)

```markdown
# 리스크모니터링·행동위험분석 부서 SOP

## 절대 위반 금지 (Hard Rules)

1. 행동위험 점수 ≥ 0.85 → 24시간 내 보고서 작성 의무
2. 개인정보 노출 → 즉시 격리·법무 통보
3. 거짓양성 의심 사건 → 2차 Critic 검증 후 알람
4. 카지노 부정거래 의심 → VMS + CCTV 통합 분석 의무

## 워크플로우 (Soft Rules)

- UEBA 점수 → GraphRAG 관계 검증 → Causal 인과 추론 → 합의
- 모든 AI 결정에 confidence + 인과 설명 첨부
- 매주 거짓양성·거짓음성 비율 자동 보고
- 분기마다 모델 bias 감사

## Self-Critique 임계

- 일반 사건: confidence ≥ 0.7
- 고위험 (≥ 0.85): confidence ≥ 0.9 + 2차 검증 의무
```

### `rules/regulatory-compliance.md` (법규 헌법)

```markdown
# 한국·EU 법규 헌법

## EU AI Act (2025-02 발효, 2027-08 고위험 의무)

- 고위험 AI 결정 → 설명 가능성 의무 (SHAP·LIME)
- 인간 감독 (Human-in-the-Loop) 의무
- bias·discrimination 정기 audit

## 금감원 AI 거버넌스 (2026 발효)

- AI 모델 거버넌스 위원회 구성
- AI 결정 로그 5년 보존
- 정기 위험 보고서 (분기)

## 개인정보보호법 (가명·익명 2026 확대)

- 가명정보 안전조치
- 행동데이터 처리 동의·고지

## ISO 42001 AI 관리시스템 (2026-27 한국 도입)

- AI 라이프사이클 관리 의무
- 모델 카드 작성
- 정기 인증 audit
```

## Hook 자동 강제 (PreToolUse·PostToolUse)

```bash
# .claude/hooks/dept-constitution-check.sh

#!/bin/bash
# 부서 헌법 위반 자동 차단

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# 헌법 위반 패턴
if echo "$CMD" | grep -qE 'risk_score=0\.[89][0-9]|fraud_alert'; then
    # 고위험 알람 → 24시간 보고서 의무
    if [ ! -f .claude/state/risk_reports/$(date +%Y-%m-%d).md ]; then
        echo '{"systemMessage": "⚠️ 부서 헌법 위반 — 고위험 알람 발생 시 24h 내 보고서 의무. 즉시 작성하세요."}'
        exit 1  # 차단
    fi
fi

if echo "$CMD" | grep -q 'personal_info\|개인정보'; then
    # 개인정보 노출 의심 → 격리
    echo '{"systemMessage": "🚨 개인정보 처리 감지 — 격리 + 법무 통보 절차 의무"}'
    exit 1
fi

exit 0
```

## RLAIF (선택, 자체 학습 가능 시)

```python
# 도메인 모델 학습 시 Constitutional AI 적용

def constitutional_finetune(model, data, constitution):
    """RLAIF 패턴 학습"""
    for sample in data:
        # 1. 초기 답
        answer = model.generate(sample['question'])
        # 2. 헌법 위반 검사
        for principle in constitution:
            critique = model.evaluate(f"답: {answer}\n원칙: {principle}\n위반? JSON")
            if critique['violation']:
                # 3. 수정
                revised = model.generate(
                    f"이전: {answer}\n원칙 위반: {critique['reason']}\n수정 답:"
                )
                # 4. preference pair 학습 (revised > answer)
                model.dpo_step(chosen=revised, rejected=answer)
    return model
```

## AI Risk Lighthouse 카테고리 #6 (Compliance, 10%)

| 점검 | 우리 자산 |
|---|---|
| 부서 SOP 헌법 명시? | `rules/dept-risk-sop.md` |
| 법규 자동 추적? | `rules/regulatory-compliance.md` + 주기적 갱신 |
| AI 위반 자동 차단? | `hooks/dept-constitution-check.sh` |
| 정기 audit 로그? | `.claude/state/audit/` |
| 위반 시 자동 격리? | approval-gate.py 패턴 활용 |

## 부서 즉시 도입 (1주 이내)

1. **Day 1-2**: 부서 SOP 를 `rules/dept-risk-sop.md` 로 작성
2. **Day 3-4**: 금감원·EU AI Act 핵심 조항을 `rules/regulatory-compliance.md` 로
3. **Day 5**: `dept-constitution-check.sh` hook 작성·등록
4. **Day 6-7**: PoC 실행 + 위반 사례 수집 → 헌법 갱신

→ **0원·1주·즉시 Constitutional AI 시스템 가동**.

## 트리거

- "Constitutional AI", "헌법화"
- "SOP 자동 준수", "법규 자동 준수"
- "원칙 기반 AI", "RLAIF"
- "위반 자동 차단"

## 참조

- Anthropic Constitutional AI (Bai et al. 2022)
- `.claude/rules/*.md` (이미 구축된 헌법 시스템)
- `ai-risk-lighthouse.md` § Compliance
- `solution-capability-audit.md` # 41 (✅ 이미 적용 — 부서로 확장)
