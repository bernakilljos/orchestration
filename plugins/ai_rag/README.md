# ai_rag — RAG 파이프라인 (8 패턴)

> **Prefix**: `ai_` | **버전**: 1.0 | **Status**: stable (Naive) · spec-only (Multimodal·HyDE·Corrective·Graph·Hybrid·Adaptive·Agentic) | **Phase**: 2

## ✅ 현재 상태 (2026-05-31 갱신)

| 패턴 | 상태 | 동작 방식 |
|---|---|---|
| **Naive RAG (`/rag-naive`)** | ✅ **stable — 즉시 동작** | `.claude/scripts/rag-recall.py` (ChromaDB PersistentClient + multilingual MiniLM 임베딩, 한·영 OK). 첫 호출 시 chromadb 자동 install (zero-touch). |
| Multimodal·HyDE·Corrective·Graph·Hybrid·Adaptive·Agentic | 📋 spec-only | 스크립트 stub 존재, 실구현 install 후 플랫폼에서 |

## 🚀 즉시 사용 (Naive RAG)

```bash
# 1) 인덱스 빌드 (CLAUDE.md + rules + memory + skills + references + commands + docs 자동 수집)
bash plugins/ai_rag/scripts/rag-build.sh
# Output: {"indexed": 1247, "docs": 130, "collection": "project_knowledge"}

# 2) 의미 검색
bash plugins/ai_rag/scripts/rag-search.sh "RAG 패턴 비교" --top 5
# Output: top-5 chunk + path + distance (의미 유사도)
```

ChromaDB 자동 install (없으면) — `chromadb` + `sentence-transformers` 패키지.

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

## 상세 스펙

### 8 패턴 비교

| 패턴 | 복잡도 | 정확도 | 레이턴시 | 추천 용도 |
|---|---|---|---|---|
| Naive | 1 | 낮음 | 빠름 | 간단 FAQ |
| Multimodal | 3 | 높음 | 중간 | 이미지 + 텍스트 혼합 DB |
| HyDE | 2 | 중상 | 중간 | 검색어 모호 |
| Corrective | 3 | 높음 | 느림 | 정확도 최우선 |
| Graph | 4 | 매우 높음 | 느림 | 관계형 지식 |
| Hybrid | 4 | 매우 높음 | 느림 | 엔터프라이즈 |
| Adaptive | 4 | 높음 | 가변 | 복잡 추론 |
| Agentic | 5 | 최고 | 가장 느림 | MCP 도구 필요 |

### 공통 스택 (Brij $0 stack 2026)

- Retrieval: **LlamaIndex**
- Storage/Search: **ChromaDB** (default), **Qdrant** (스케일 시)
- LLM: Claude Sonnet 또는 Ollama (로컬)
- Observability: Phoenix (self-hosted)

### 구현 가이드라인

각 `/rag-*` 커맨드 공통:
- `--dry-run` 지원
- 입력: `source.md|pdf|url`, `--top-k=5`, `--threshold=0.7`
- 출력: `data/ai_rag/<date>/` + JSON 로그
- 캐시: 임베딩 재사용 (비용 절감)

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 참조

- 출처: `docs/upgrade-analysis-2026-04-19.md` § 이미지 1·2
- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
