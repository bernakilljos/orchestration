---
name: graphrag-behavior
description: 행동패턴·자금흐름·관계 데이터를 지식그래프(Knowledge Graph)로 구축하고 LLM 으로 다단계 추론. Microsoft GraphRAG 패턴을 행동위험분석·내부자위협·자금세탁 탐지에 적용. 사용자가 "GraphRAG", "지식그래프", "행동패턴 그래프", "자금세탁 다단계 추적", "관계 기반 위험" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: rag
  tags: [graphrag, knowledge-graph, ueba, money-laundering]
---

# GraphRAG — 행동패턴 그래프 + LLM

## 왜 GraphRAG 인가

| Vector RAG 한계 | GraphRAG 해결 |
|---|---|
| 텍스트 청크 간 관계 모름 | entity·relation 추출 → 명시 그래프 |
| 다단계 추론 약함 | graph traversal 로 hop 다중 가능 |
| "X 의 친구가 Y 한테 송금" 같은 질의 약함 | 그래프 cycle·path 탐색 |
| 전사 패턴·community 모름 | community detection (Leiden) |

→ **행동위험분석·자금세탁·내부자위협** 처럼 **관계 기반** 분석에 필수.

## Microsoft GraphRAG 아키텍처

```text
원문/데이터 → LLM 추출 → entity·relation
                            ↓
                    Knowledge Graph (Neo4j·NetworkX)
                            ↓
                  Community detection (Leiden 알고리즘)
                            ↓
                    Community summary (LLM)
                            ↓
       질의 → graph traversal + summary → LLM 답
```

## 행동위험 그래프 노드·엣지 설계

```cypher
// Neo4j 예제

// 노드
(:Employee {id, name, dept, role, hire_date})
(:Transaction {id, amount, time, type})
(:Account {id, type, owner_id})
(:Approval {id, level, status, time})
(:Access {id, system, time, location})
(:Document {id, type, sensitivity})

// 엣지
(Employee)-[:WORKS_IN]->(Dept)
(Employee)-[:APPROVES]->(Approval)
(Employee)-[:ACCESSES]->(Access)
(Employee)-[:OWNS]->(Account)
(Transaction)-[:FROM]->(Account)
(Transaction)-[:TO]->(Account)
(Approval)-[:APPLIES_TO]->(Transaction)
(Access)-[:READS]->(Document)
```

## 위험 패턴 (그래프 cycle·path)

| 패턴 | Cypher 질의 |
|---|---|
| **다중 hop 자금세탁** | `MATCH p=(a:Account)-[:TRANSFER*3..6]->(a) RETURN p` (3-6 hop cycle) |
| **승인-실행 동일인** | `MATCH (e:Employee)-[:APPROVES]->(a:Approval)-[:APPLIES_TO]->(t:Transaction)-[:FROM]->(:Account)-[:OWNED_BY]->(e)` |
| **이직 직전 대량 다운로드** | `MATCH (e:Employee)-[:ACCESSES]->(a:Access)-[:READS]->(d:Document {sensitivity:'high'}) WHERE e.exit_date - a.time < 30 days` |
| **부서 외 데이터 접근** | `MATCH (e:Employee {dept:'A'})-[:ACCESSES]->(:Access {system:'B'}) WHERE NOT (e)-[:AUTHORIZED_FOR]->(:System {name:'B'})` |
| **카지노 딜러-플레이어 공모** | `MATCH (d:Dealer)-[:SAW]->(p:Player)-[:WON_ABNORMALLY]->(:Game) WHERE d.shift = game.time AND repeat > 5` |

## 구현 예제 (Python + Neo4j)

```python
from neo4j import GraphDatabase
import openai

class BehaviorGraphRAG:
    def __init__(self, neo4j_uri, llm_api):
        self.driver = GraphDatabase.driver(neo4j_uri)
        self.llm = openai.OpenAI()

    def build_graph(self, employee_data, transaction_data, access_logs):
        """LLM 으로 entity·relation 추출 → 그래프 구축"""
        with self.driver.session() as s:
            # LLM 이 텍스트 로그에서 entity·relation 추출
            for log in access_logs:
                entities = self.extract_entities(log)
                for e in entities:
                    s.run(f"MERGE (:{e['type']} {{id: $id}}) ", id=e['id'])
                # relations
                rels = self.extract_relations(log)
                for r in rels:
                    s.run(
                        f"MATCH (a:{r['from_type']} {{id: $from}}), (b:{r['to_type']} {{id: $to}}) "
                        f"MERGE (a)-[:{r['rel']}]->(b)",
                        **{'from': r['from_id'], 'to': r['to_id']}
                    )

    def detect_community(self):
        """Leiden 알고리즘으로 community 탐지"""
        with self.driver.session() as s:
            result = s.run("""
                CALL gds.leiden.stream('behavior_graph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id AS id, communityId
            """)
            return list(result)

    def query_risk(self, question):
        """그래프 traversal + LLM"""
        # 1. LLM 이 질의 → Cypher 변환
        cypher = self.llm.chat.completions.create(
            model='gpt-4',
            messages=[{
                'role': 'user',
                'content': f'행동위험 그래프에서 다음 질의를 Cypher 로 변환: {question}'
            }]
        ).choices[0].message.content
        # 2. Cypher 실행
        with self.driver.session() as s:
            result = list(s.run(cypher))
        # 3. LLM 이 결과 해석
        answer = self.llm.chat.completions.create(
            model='gpt-4',
            messages=[{
                'role': 'user',
                'content': f'질의: {question}\n그래프 결과: {result}\n위험 평가 보고서를 작성'
            }]
        ).choices[0].message.content
        return {'cypher': cypher, 'graph_result': result, 'answer': answer}
```

## 우리 솔루션 통합

```bash
# 1. Neo4j Community 무료 설치 (Docker)
docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest

# 2. plugin 신설
plugins/ai_rag/
├── plugin.json (기존)
└── skills/
    ├── rag-graph.md (이미 있음, 보강)
    └── graphrag-behavior.md (본 파일)

# 3. 라이브러리
pip install neo4j graphrag networkx

# 4. PoC: 부서 행동데이터 그래프화
```

## 부서 적용 우선순위

| 순위 | 시나리오 | 예상 ROI |
|---|---|---|
| 🥇 | **다중 hop 자금세탁 탐지** (금융) | 1社 5억+ |
| 🥈 | **승인-실행 동일인 탐지** (회계 분식) | 1社 3억+ |
| 🥉 | **이직 직전 대량 다운로드 탐지** (정보 유출) | 1社 2억+ |
| 4 | **카지노 딜러-플레이어 공모** (카지노 9社) | 1社 1억 × 9 |
| 5 | **부서 외 데이터 접근 anomaly** (전사) | 컨설팅 base |

## AI Risk Lighthouse 카테고리 #3 (Behavioral Coverage, 15%)

GraphRAG 가 핵심. 그래프 없이는 "여러 source 통합" 점수 ≤ 30%.

## 트리거

- "GraphRAG", "지식그래프"
- "행동패턴 그래프", "관계 기반 위험"
- "자금세탁 다단계", "다중 hop 추적"
- "Neo4j", "Cypher"

## 참조

- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- Neo4j Graph Data Science Library
- `plugins/ai_rag/skills/rag-graph.md` (보강)
- `ai-risk-lighthouse.md` § Behavioral Coverage
- `solution-capability-audit.md` # 22 (🟡 부분 → ✅ 완성 목표)
