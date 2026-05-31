---
name: llm-as-judge
description: Haiku 4.5 격리 채점관. 4차원 (Correctness·Completeness·Style·Safety) 0~10 점수화. post-impl·PR 직전·회귀 감지·라우팅 검증 시. Prompt caching 90% 절감.
---

# LLM-as-judge (Haiku Scoring)

## 트리거

- task 완료 후 자동 (Stop hook async)
- 사용자가 `/score-task` 실행
- code-reviewer subagent 가 보조 점수 요청

## 평가 프롬프트 골격 (cache_control 적용)

```python
SYSTEM_RUBRIC = """
You are a strict code/output evaluator. Score 0-10 on 4 dimensions:

1. Correctness  — Does it meet the spec?
2. Completeness — Are all requirements covered? Any missing pieces?
3. Style        — Does it follow project conventions (CLAUDE.md, indentation, frontmatter)?
4. Safety       — Any hardcoded secrets, dangerous commands, injection risks?

Rules:
- Be honest. Round-numbers (5, 7, 10) are fine — don't pad.
- If you cannot evaluate (file empty, missing context), output score=null and explain.
- Output STRICT JSON only. No prose outside JSON.
"""

USER_TEMPLATE = """
## Task spec
{task_md}

## Result to evaluate
{result_md}

Output JSON:
{{
  "correctness":  <0-10 or null>,
  "completeness": <0-10 or null>,
  "style":        <0-10 or null>,
  "safety":       <0-10 or null>,
  "reason":       "<one sentence each dimension>",
  "verdict":      "PASS" | "FAIL" | "INCONCLUSIVE"
}}
"""
```

## Verdict 룰 (스크립트 측 후처리)

```text
PASS: 모든 점수 >= 7  AND  safety == 10
FAIL: 어느 점수 <= 4  OR   safety <= 7
INCONCLUSIVE: 그 외
```

## Prompt caching

- `SYSTEM_RUBRIC` 은 변하지 않음 → `cache_control: ephemeral` 적용
- 5분 TTL 안에 N번 호출하면 90% 비용 절감
- TTL 만료 직전 자동 갱신은 미구현 (수동)

## 결과 누적

`.claude/state/evaluations.jsonl`:
```jsonl
{"ts":"2026-05-07T17:30:00","task_id":"task-042","scores":{"correctness":8,"completeness":7,"style":9,"safety":10},"verdict":"PASS","reason":"요구사항 충족, edge case 일부 미커버","model":"claude-haiku-4-5-20251001","cost_usd":0.0012}
```

## 실패 모드

- API 키 없음 → exit 2, "ANTHROPIC_API_KEY missing" 로그
- 응답이 JSON 아님 → 1회 retry, 그래도 실패 시 verdict=INCONCLUSIVE 기록
- 결과 파일 없음 → score=null, verdict=INCONCLUSIVE

## 향후 (TODO)

- regression set: 동일 task 를 주기적으로 재평가해 점수 추이 그래프
- 라우팅 피드백: PASS 율 낮은 라우트 자동 deprecate (route.py 연동)
- SQLite `evaluations` 테이블 마이그레이션 (현재 jsonl)
