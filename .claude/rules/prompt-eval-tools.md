# 프롬프트 테스트·평가 도구 룰

> **근거**: 2026-09-02 · Promptfoo·DeepEval·Ragas·LangSmith 통합.

## 절대 룰

**프롬프트 변경 = A/B 테스트 · LLM 응답 = 평가 · RAG = Ragas · 회귀 방지.**

## 도구 매트릭스

| 도구 | 목적 | 라이선스 |
|---|---|---|
| **Promptfoo** | 프롬프트 A/B 테스트 · CLI · 회귀 방지 | MIT |
| **DeepEval** | LLM 응답 평가 (correctness·hallucination·bias) | Apache |
| **Ragas** | RAG 평가 (context·answer relevance·faithfulness) | Apache |
| **LangSmith** | LangChain · trace + eval | Freemium |
| **TruLens** | LLM 평가·모니터링 | Apache |

## Promptfoo 사용

```yaml
# promptfooconfig.yaml
prompts:
  - "감사조서 요약해줘 · {{document}}"
providers:
  - anthropic:claude-opus-5
  - anthropic:claude-sonnet-5
tests:
  - vars:
      document: "감사 대상 문서 1"
    assert:
      - type: contains
        value: "핵심 결과"
      - type: llm-rubric
        value: "감사 결과가 3 줄 이내로 간결한가?"
```

```bash
npx promptfoo eval  # A/B 실행
npx promptfoo view  # 결과 뷰
```

## DeepEval

```python
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric

test_case = LLMTestCase(
    input="개보법 위반 감사",
    actual_output=llm_response,
    context=[감사_문서]
)
assert_test(test_case, [AnswerRelevancyMetric(0.8), HallucinationMetric(0.1)])
```

## Ragas (RAG 평가)

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

result = evaluate(
    dataset=my_rag_dataset,
    metrics=[faithfulness, answer_relevancy, context_precision]
)
```

## 우리 kit 통합

- `.claude/rules/prompt-eval-tools.md` (이 파일)
- `plugins/eval_quality/` 확장 (Promptfoo·DeepEval 통합)
- CI 워크플로우 · PR 시 자동 실행

## 언제 사용

| 상황 | 도구 |
|---|---|
| 프롬프트 수정 후 회귀 방지 | Promptfoo |
| RAG 파이프라인 품질 | Ragas |
| LLM 응답 편향·hallucination | DeepEval |
| 프로덕션 모니터링 | LangSmith / TruLens |

## 관련

- `plugins/eval_quality/`
- `.claude/rules/embedding-strategy.md` (RAG 임베딩)
- `plugins/exec_orch/skills/route_dispatch.md`
