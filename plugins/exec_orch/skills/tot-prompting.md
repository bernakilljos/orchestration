---
name: tot-prompting
description: Tree of Thoughts — 여러 branch 생성·평가·pruning·확장. 탐색 공간 큰 결정 (아키텍처·알고리즘 선택·디버깅 가설 분기). "tree of thoughts", "ToT", "branch", "여러 후보", "비교 선택" 키워드.
---

# Skill: Tree of Thoughts (Anthropic #9)

> **목적**: 단일 CoT 가 막힐 때 여러 경로 동시 탐색 + 평가 + 가지치기.
> **트리거**: 결정에 옵션 3+ 개 / CoT 1번에서 fail / 사용자 "여러 방법 비교".

## 1. 언제

| 상황 | ToT 적용? |
|---|---|
| 아키텍처 결정 (MQ vs DB polling vs WebSocket) | ✅ |
| 알고리즘 선택 (BFS vs DFS vs Dijkstra) | ✅ |
| 디버깅 가설 분기 (network·db·cache·permission) | ✅ |
| 단순 구현 (CoT 1번 충분) | ❌ |
| 정답 1개 명확 | ❌ |

## 2. 표준 프로토콜 (4 단계)

```text
Step 1 — Branch
  Input: <문제>
  Generate: N=3~5 개 후보 (서로 다른 접근)
  
Step 2 — Evaluate
  각 branch 에 대해 score(0-10):
    - Feasibility (실현 가능)
    - Cost (실행 비용 + 유지 비용)
    - Risk (실패 시 손실)
  
Step 3 — Prune
  Score 합산 하위 2개 제거.
  Top 1~2 만 유지.

Step 4 — Expand
  Top 의 다음 단계 (sub-tree).
  Step 1~4 반복 (depth 3 까지).
  
Final — Select
  leaf 중 best path 선택. 다른 path 는 fallback 으로 기록.
```

## 3. depth × branch 한계

| Depth | Branch / level | 총 node | 비용 |
|---|---|---|---|
| 1 | 5 | 5 | 작음 |
| 2 | 3 (prune 후) | 15 | 중간 |
| 3 | 2 | 30 | 큼 |
| 4+ | — | 90+ | ❌ 비용 폭증 |

→ Depth ≤ 3 / 각 level branch ≤ 5 / prune 매 단계 (top 50% 만).

## 4. 자동 적용 (route_dispatch 보강)

route_dispatch.md § Step 2 의 `DESIGN`·`DECISION` 분류 시:

```bash
if [ "$TASK_TYPE" = "DESIGN" ] || [ "$TASK_TYPE" = "DECISION" ]; then
  # ToT 자동 활성 — Opus 4.7 Extended Thinking + 3 branch
  call_claude_opus_with_tot --branches 3 --depth 2 --task "$TASK"
fi
```

## 5. 평가 차원 표준 (Self-consistency #8 와 결합)

| 차원 | 0~10 | 가중치 |
|---|---|---|
| Feasibility | 동작 가능성 | × 0.4 |
| Cost | 비용 효율 | × 0.3 |
| Risk | 실패 영향 | × 0.3 |

Self-consistency: N=3 평가자 (Haiku ×3) 다수결.

## 6. 예시

### Problem: "lottoclaude 의 codex 결과가 엉망. 원인 추정 + fix 선택."

Branch 1: **task-instruction 품질 부족 (12 기법 누락)**
  - Feasibility 9 (즉시 보강)
  - Cost 2 (template 1회)
  - Risk 1 (실패해도 되돌리기 쉬움)
  - Score: 9×0.4 + 8×0.3 + 9×0.3 = 8.7

Branch 2: **codex 자체 hallucination 빈도 높음**
  - Feasibility 4 (외부 모델 fix 불가)
  - Cost 8 (다른 worker 로 교체 비용 큼)
  - Risk 6 (대체 worker 도 동일 가능)
  - Score: 4×0.4 + 2×0.3 + 4×0.3 = 3.4

Branch 3: **컨텍스트 부족 (RAG 미설치)**
  - Feasibility 8 (ChromaDB 설치 가능)
  - Cost 4 (인덱싱 비용)
  - Risk 2 (실패해도 fall back 쉬움)
  - Score: 8×0.4 + 6×0.3 + 8×0.3 = 7.4

**Prune**: Branch 2 제거. Top = Branch 1·3.

**Expand**:
  Branch 1 → § 12 기법 prompt-techniques.md 추가 (이미 완료)
  Branch 3 → § ChromaDB local 즉시 설치 (이미 완료)

**Select**: 둘 다 채택 (보완적).

→ 이번 세션의 결정이 이 ToT 패턴이었음.

## 7. 무한 확장 방지

- Depth = 3 hard limit
- Branch / level ≤ 5 hard limit
- Score top 50% 만 expand
- Score 차 ≥ 3 = 즉시 select (다른 branch 무의미)

## 8. 금지

- Depth > 3 (비용 폭증)
- 평가 차원 없이 "느낌"으로 prune
- 1번에 모든 branch 동시 expand (메모리 폭증)
- Branch 다수결 (Self-consistency #8 와 혼동 X — ToT 는 best path)

## 9. 참조

- `plugins/exec_orch/skills/prompt-techniques.md` § #9 Tree of Thoughts
- `plugins/exec_orch/skills/route_dispatch.md` § Step 2 DESIGN/DECISION
- `plugins/eval_quality/skills/llm-as-judge.md` (branch 평가)
- `plugins/exec_orch/skills/auto-planner.md` § 1 전수조사 (branch 후보 수집)
- `plugins/exec_orch/skills/meta-prompting.md` (#7 와 결합 — 약한 branch 는 meta-rewrite)
