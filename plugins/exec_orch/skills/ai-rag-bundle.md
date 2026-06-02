---
name: ai-rag-bundle
description: Vector DB·HyDE·Long Context·Memory Architectures 통합 RAG 기반 인프라 가이드. ChromaDB·Pinecone·Weaviate 활용 + Claude 1M ctx + MemGPT·Letta 장기 기억. 사용자가 "Vector DB", "RAG 인프라", "HyDE", "Long Context", "Memory", "MemGPT", "Letta" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: rag
---

# RAG Bundle — Vector·HyDE·Long Context·Memory

## 50 기술 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 22 | GraphRAG | (별도 `graphrag-behavior.md`) |
| 23 | Memory Architectures | MemGPT·Letta·Mem0 |
| 43 | Vector Databases | Pinecone·Weaviate·Chroma·Qdrant |
| 44 | HyDE | LangChain·LlamaIndex |
| 45 | Long Context (1M+) | Claude Opus·Gemini 1M |

## Vector DB 무료 도입 (ChromaDB)

```bash
pip install chromadb
```

```python
import chromadb

client = chromadb.PersistentClient(path='.claude/state/vector')
coll = client.get_or_create_collection('behavior_patterns')

# 행동 패턴 저장
coll.add(
    documents=['직원 A 가 새벽 3시 결재 승인',
               '거래 X 가 평소보다 10배 큰 금액'],
    metadatas=[{'type': 'temporal'}, {'type': 'amount'}],
    ids=['evt-001', 'evt-002']
)

# 유사 위험 사례 검색
results = coll.query(
    query_texts=['새벽 시간대 비정상 결재'],
    n_results=10
)
```

## HyDE (Hypothetical Document Embedding)

```python
def hyde_search(query, vector_db, llm):
    # 1. LLM 이 가상 답 먼저 생성
    hypothetical = llm.generate(f"'{query}' 에 대한 답을 작성:")
    # 2. 가상 답으로 검색 (질의보다 검색 정확도 ↑)
    results = vector_db.query(query_texts=[hypothetical], n_results=10)
    # 3. 실제 답 생성 (검색 결과 기반)
    final = llm.generate(f"질의: {query}\n참고: {results}\n답:")
    return final
```

## Long Context — Claude Opus 4.7 (1M tokens)

```python
# 1년치 거래·접근·결재 로그를 단일 호출
prompt = f"""
다음은 직원 X 의 1년치 행동 로그입니다 (800K 토큰):

{full_year_logs}

질문: 이 직원의 위험 패턴·이상 시점·예상 행동을 종합 분석하세요.
"""
# Claude Opus 1M ctx 한 번에 처리
response = anthropic.messages.create(
    model='claude-opus-4-7',
    max_tokens=8000,
    messages=[{'role': 'user', 'content': prompt}]
)
```

## Memory Architectures — MemGPT/Letta 통합

```bash
pip install letta
```

```python
from letta import create_client

client = create_client()
agent = client.create_agent(
    name='dept-risk-officer',
    persona='리스크모니터링·행동위험 분석 에이전트',
    human='ITCEN CORE 부서원',
    # OS-style 가상 메모리
    memory={
        'core_memory_human': '부서 SOP·법규·고객 정보',
        'core_memory_persona': '내 역할·임무·원칙',
        'archival_storage': '과거 모든 위험 사례 (영구)',
        'recall_storage': '최근 대화·세션 메모리'
    }
)

# 직원 행동 영구 학습
agent.send_message('직원 A 의 2025-Q3 행동 패턴 기록')
agent.send_message('직원 A 가 2026-Q1 이상 행동 — 과거와 비교?')
# Letta 가 자동으로 archival → recall → reasoning
```

## 우리 솔루션 통합

| 자산 | 활용 |
|---|---|
| `.claude/state/orca.db` SQLite | ChromaDB 와 결합 (메타데이터) |
| `plugins/exec_offline-vector` (이미 존재) | 활성화·확장 |
| `plugins/exec_learning/learn` skill | Memory Architecture base |
| `.claude/memory/` | Letta 와 비슷한 구조 — 통합 가능 |

## ITCEN CORE 적용

| 시나리오 | 적용 기술 |
|---|---|
| 유사 부정 사례 즉시 검색 | Vector DB (ChromaDB) |
| 행동위험 가상 답 검색 | HyDE |
| 1년치 행동 단일 분석 | Long Context (Claude 1M) |
| 직원 영구 행동 학습 | MemGPT/Letta |
| 규제 변경 영향 분석 | GraphRAG (별도 skill) |

## AI Risk Lighthouse #3 (Coverage) 보강

데이터 통합 + 영구 기억 = Coverage 점수 +20.

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | ChromaDB 활성화 (`exec_offline-vector`) | 1일 |
| 2 | HyDE 검색 PoC | 1주 |
| 3 | Letta 통합 — 부서 Risk Officer Agent | 2주 |
| 4 | 1년치 로그 Long Context 분석 PoC | 2주 |
| 5 | 종합 RAG 인프라 가동 | 1개월 |

## 트리거
- "Vector DB", "ChromaDB", "Pinecone"
- "HyDE", "Hypothetical Document"
- "Long Context", "1M context"
- "MemGPT", "Letta", "Memory Architectures"

## 참조
- ChromaDB: https://www.trychroma.com/
- Letta: https://www.letta.com/
- LangChain HyDE
- `plugins/ai_rag/skills/rag-hyde.md` (보강)
- `solution-capability-audit.md` #23, #43, #44, #45 (보강 완성)
