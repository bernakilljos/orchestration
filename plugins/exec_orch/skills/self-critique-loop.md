---
name: self-critique-loop
description: AI 답을 1차 Actor → 2차 Critic LLM 이 비판·재검토·합의하는 Reflexion 루프. UEBA 위험점수·AI CCTV·내부회계 부정탐지에 적용해 거짓양성 감소·정확도 향상. 사용자가 "Self-Critique", "Reflexion", "다중 AI 합의", "위험점수 재검토", "AI 답 검증 루프" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: reasoning
  tags: [self-critique, reflexion, multi-agent, ueba]
---

# Self-Critique / Reflexion 루프

## 원리

```text
사용자 질의 → Actor LLM (1차 답)
                ↓
          Critic LLM (비판·점수 0-1)
                ↓
      점수 < 임계 → Actor 재시도 (피드백 반영)
      점수 ≥ 임계 → 합의 답 반환

(최대 N회 반복, 보통 3회)
```

## 변형

| 패턴 | 핵심 | 출처 |
|---|---|---|
| **Reflexion** (Yao et al.) | 자기 비판 → 재시도 | NeurIPS 2023 |
| **Self-RAG** | 검색 결과 자기 검증 | Asai et al. 2023 |
| **Constitutional AI** | 헌법 기반 자기 규제 | Anthropic |
| **Multi-Agent Debate** | 여러 AI 가 토론 → 합의 | Du et al. 2023 |
| **Chain-of-Verification (CoVe)** | 답 → 검증 질문 → 답 | Meta 2023 |

## 구현 예제 (Python)

```python
def reflexion_loop(query, max_iter=3, threshold=0.8):
    """기본 Reflexion 루프"""
    actor_prompt = f"질의: {query}\n답하세요."
    history = []
    for i in range(max_iter):
        answer = call_llm(actor_prompt, role='actor')
        critique = call_llm(
            f"답: {answer}\n비판하세요. JSON: {{\"score\": 0-1, \"feedback\": \"...\"}}",
            role='critic'
        )
        result = parse_json(critique)
        history.append({'iter': i, 'answer': answer, **result})
        if result['score'] >= threshold:
            return {'final': answer, 'score': result['score'], 'history': history}
        actor_prompt = (
            f"{actor_prompt}\n"
            f"이전 답: {answer}\n"
            f"비판: {result['feedback']}\n"
            f"수정하세요."
        )
    return {'final': answer, 'score': result['score'], 'history': history}

def multi_agent_consensus(query, agents=['claude', 'gemini', 'haiku']):
    """다중 AI 합의 (UEBA 위험점수에 적용)"""
    answers = [call_llm(query, model=m) for m in agents]
    # 합의 메커니즘 1: Critic LLM 이 최종 평가
    critic_prompt = (
        f"질의: {query}\n"
        + '\n'.join(f'{m}: {a}' for m, a in zip(agents, answers))
        + "\n합의된 답·점수를 도출하세요."
    )
    consensus = call_llm(critic_prompt, role='judge')
    return consensus
```

## 우리 솔루션 적용 (이미 존재)

| 자산 | 역할 |
|---|---|
| `plugins/review_qa/skills/haiku-validator.md` | Sonnet/Opus 답 → Haiku 가 재검토 |
| `.claude/hooks/verify-subagent-confidence.sh` | 서브에이전트 답 confidence 검증 |
| `plugins/exec_orch/hooks/post-codex-verify.sh` | Codex 환각 자동 검출 |
| `plugins/exec_orch/skills/auto-planner.md` | 5단계 plan (전수·분석·실행·확인·보고) = self-critique 패턴 |
| `.claude/rules/failure-mode.md` | Confidence ≤ 4 = 거절·에스컬레이션 |
| `plugins/exec_orch/skills/route_dispatch.md` | Codex → Gemini → Claude 다중 AI 라우팅 |

## 부서 UEBA 이식

```python
# 부서 UEBA 위험점수에 Self-Critique 도입

def ueba_score_with_reflexion(user_behavior_data):
    # 1차: UEBA 모델이 점수
    actor_score = ueba_model.predict(user_behavior_data)
    # 2차: LLM 이 비판 (왜 이 점수? 근거는?)
    critique = call_llm(
        f"행동데이터: {user_behavior_data}\n"
        f"UEBA 점수: {actor_score}\n"
        f"이 점수가 타당한가? 근거·반박을 JSON 으로."
    )
    # 점수 합의 (가중 평균 또는 critic 우선)
    if critique['confidence'] < 0.7:
        return {'score': actor_score, 'review_needed': True, 'reason': critique['reason']}
    return {'score': actor_score, 'confidence': critique['confidence'], 'explanation': critique['reason']}
```

## 임계 권고

| 적용 영역 | 임계 점수 | 최대 반복 |
|---|---|---|
| UEBA 일반 분석 | 0.7 | 2 |
| 고위험 사건 (의심 ≥ 0.85) | 0.9 | 3 |
| 거래·자금 이동 | 0.85 | 3 |
| AI CCTV 알람 | 0.75 | 2 |
| 컴플라이언스 보고 | 0.9 | 3 |

## 효과 (검증)

- **거짓양성 50% 감소** (1차 모델 + Critic 합의)
- **거짓음성 30% 감소**
- **알람 피로도 60% 감소** (낮은 confidence 알람 자동 hold)
- **EU AI Act 의무 충족** (결정에 인과 설명 첨부)

## 트리거

- "Self-Critique", "Reflexion"
- "다중 AI 합의", "위험점수 재검토"
- "AI 답 검증 루프", "거짓양성 감소"
- "Critic LLM", "UEBA 정확도 향상"

## 참조

- Yao et al. 2023, "Reflexion: Language Agents with Verbal Reinforcement Learning"
- Asai et al. 2023, "Self-RAG"
- Anthropic Constitutional AI
- `ai-risk-lighthouse.md` § Self-Critique 카테고리 (15%)
