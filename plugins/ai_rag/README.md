# ai_rag — RAG 파이프라인 (8 패턴)

> **Prefix**: `ai_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2

## ⚠️ 현재 상태
**spec-only** — 스펙 + 공통 헬퍼만. 실구현은 install 후 플랫폼에서.

## 📋 커맨드 (8 RAG 패턴)

| 커맨드 | 패턴 | 특징 |
|---|---|---|
| `/rag-naive` ⭐ 기본 | Naive RAG | Query → Embed → VectorDB → Prompt → LLM |
| `/rag-multimodal` | Multimodal | 이미지·텍스트 동시 검색 |
| `/rag-hyde` | HyDE | Hypothetical Response 생성 후 검색 |
| `/rag-corrective` | Corrective RAG | Grade · Query Analyzer · Web Search fallback |
| `/rag-graph` | Graph RAG | Knowledge Graph · Entity extraction |
| `/rag-hybrid` | Hybrid | Vector + Graph DB 동시 |
| `/rag-adaptive` | Adaptive | Multi-step reasoning chain |
| `/rag-agentic` | Agentic | ReAct + CoT + Multi-agent + MCP |

## 🧠 스킬

- `skill-rag-patterns` — 8 패턴 선택 가이드
- `skill-vector-db` — ChromaDB · Qdrant · Pinecone 운영

## 🔗 의존성

- **플러그인**: `exec_orch`, `mcp_data`
- **MCP**: `llamaindex`, `chromadb`, `qdrant`
- **환경변수**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

## 참조

- 출처: `docs/upgrade-analysis-2026-04-19.md` § 이미지 1·2
- 스펙: `SPEC.md`
