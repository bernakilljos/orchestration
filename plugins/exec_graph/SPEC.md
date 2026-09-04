# exec_graph (spec-only)

> **목적**: linear task-instruction 외 **stateful graph orchestration** 도입 — LangGraph 패턴.
> **근거**: `docs/2026-06-16/tooling-comparison.md` §  LangGraph.
> **상태**: spec-only — 우리 linear 패러다임으로 충분한 case 대다수. graph 가 필요한 case 식별 후 활성.

## linear vs graph 비교

| 항목 | 우리 linear (task-instruction) | LangGraph graph |
|---|---|---|
| 흐름 | 직선 (A → B → C) | 그래프 (조건 분기, loop, parallel) |
| 상태 | task-instruction.md + DB | 명시적 state node |
| 적합 | 단순 workflow, 명확한 단계 | 복잡 멀티 에이전트, 반복 정제, 조건 분기 많음 |
| 복잡도 | 낮음 (markdown 만) | 높음 (graph DSL 또는 Python) |
| 우리 사용 | 95%+ task | 5% — multi-angle 검증·반복 정제 |

## 활용 시점 (graph 가 의미 있는 case)

1. **multi-angle 검증** — 같은 결과를 3개 다른 분석가가 평가 → 합의
2. **반복 정제** — draft → check → refine loop (n 번 까지)
3. **조건 분기 많음** — task 결과에 따라 다른 후속 단계
4. **parallel + merge** — 3 워커 병렬 → 결과 merge → 다음 단계
5. **long-running autonomy** — Fable 5 + Dynamic Workflows 와 함께 (Fable 5 재-suspend 시 Opus 4.8)

## 명령 (예정)

| 명령 | 동작 |
|---|---|
| `/graph-define <name>` | yaml graph spec 작성 (nodes·edges·state) |
| `/graph-run <name>` | spec 실행 (Python LangGraph runtime) |
| `/graph-status <id>` | 실행 중인 graph 상태 |
| `/graph-visualize <name>` | mermaid 다이어그램 출력 |

## 의존성

- `pip install langgraph langchain` (Python 3.10+)
- `exec_orch` (task-instruction 표준)
- Claude Code Dynamic Workflows (v2.1.154+) 와 비교·통합

## 다음 단계 (사용자 결정 시)

1. 우리 multi-angle 검증·반복 정제 case 식별 (현재 어떤 task 가 linear 로 부족한가?)
2. POC — 1~2 graph spec 작성 (예: 산출물 visual 검증 loop)
3. status → `experimental`
4. CLAUDE.md § 3.5 전역 오케스트레이션 옆에 § 3.5b graph orchestration 신설
