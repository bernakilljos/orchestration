---
description: LangGraph stateful graph orchestration 실행 — yaml spec → multi-agent graph
allowed-tools: Bash(python:*), Read, Write
---

# /graph-run — Stateful graph 실행

> **근거**: `docs/2026-06-16/tooling-comparison.md` § ⭐ LangGraph 패턴.
> **사용**: linear task-instruction 부족 case — multi-angle 검증·반복 정제·조건 분기 많음.
> **요구**: `pip install langgraph langchain` (Python 3.10+).

## 사용

```bash
/graph-run <graph-spec.yaml>
/graph-run --visualize <graph-spec.yaml>  # mermaid 출력만
```

## graph-spec.yaml 예시

```yaml
name: multi-angle-verify
nodes:
  - id: draft
    agent: claude-opus-4-8
    prompt: "{input} 에 대한 초안 작성"
  - id: critique-1
    agent: claude-haiku-4-5
    prompt: "초안을 보안 관점에서 비판"
  - id: critique-2
    agent: claude-haiku-4-5
    prompt: "초안을 성능 관점에서 비판"
  - id: critique-3
    agent: claude-haiku-4-5
    prompt: "초안을 가독성 관점에서 비판"
  - id: synthesize
    agent: claude-opus-4-8
    prompt: "3개 critique 를 통합해 최종안"
edges:
  - from: draft
    to: [critique-1, critique-2, critique-3]   # parallel
  - from: [critique-1, critique-2, critique-3]
    to: synthesize
state:
  - input: str
  - draft: str
  - critiques: list[str]
  - final: str
```

## 동작

```bash
# 1. 의존성 확인
python -c "import langgraph" 2>/dev/null || {
  echo "[FAIL] pip install langgraph langchain"
  exit 1
}

# 2. spec 파싱 + graph 빌드
python plugins/exec_graph/runtime/build_graph.py "$1"

# 3. visualize (선택)
[ "$2" = "--visualize" ] && python plugins/exec_graph/runtime/visualize.py "$1" && exit 0

# 4. 실행
python plugins/exec_graph/runtime/run_graph.py "$1"

# 5. 결과 → .claude/state/graph-runs/<spec-name>-<timestamp>/
#    - state.json (final state)
#    - traces/ (각 node 입출력)
#    - mermaid.md (실행 흐름)

# 6. metrics 기록 (.claude/state/orca.db metrics 테이블)
```

## linear vs graph 결정 기준

| 상황 | linear (task-instruction) | graph (이 명령) |
|---|---|---|
| 단순 implementation | ✅ | ❌ |
| 1회 검증 | ✅ | ❌ |
| 3+ 다른 시각 비판 | ❌ | ✅ |
| 반복 정제 (n 회) | ❌ | ✅ |
| 조건 분기 많음 | ❌ | ✅ |
| parallel + merge | partial | ✅ |

## 참조

- `plugins/exec_graph/SPEC.md`
- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- CLAUDE.md § 3.5 전역 오케스트레이션 (옆에 § 3.5b graph 추가 예정)
