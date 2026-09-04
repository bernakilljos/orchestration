# RAG Patterns & Tools Comprehensive Toolkit Reference

> **목적**: RAG(Retrieval-Augmented Generation) 전체 생태계의 공통 도구·패턴 카탈로그
> **대상**: `ai_rag` 플러그인 및 모든 RAG 관련 스킬·커맨드에서 참고
> **범위**: 8 RAG 패턴 + 100+ 도구 (벡터DB, 임베딩, 청킹, 프레임워크, 평가, 최적화)
> **최종 갱신**: 2026-05-20

---

##  카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|---|---------|--------|---------|
| 1 |  8 RAG 패턴 | 8 | Naive, Multimodal, HyDE, Corrective, Graph, Hybrid, Adaptive, Agentic |
| 2 | 🗃 벡터 데이터베이스 | 8 | ChromaDB, Pinecone, Weaviate, Qdrant, Milvus, FAISS, LanceDB, pgvector |
| 3 | 🧮 임베딩 모델 | 9 | OpenAI, Cohere, Sentence-Transformers, BAAI/BGE, Instructor, Nomic, Jina, Hugging Face |
| 4 | ✂ 청킹 전략 | 7 | RecursiveCharacter, SemanticChunker, MarkdownHeader, HTMLSplitter, Token, SentenceWindow |
| 5 | 🏗 RAG 프레임워크 | 6 | LangChain, LlamaIndex, Haystack, RAGFlow, Verba, AutoRAG |
| 6 | 🔄 리랭킹 & 리트리버 | 7 | Cohere Rerank, ColBERT, bge-reranker, FlashRank, RankLLM, BGE, Jina Reranker |
| 7 |  평가 & 모니터링 | 8 | RAGAS, DeepEval, TruLens, Phoenix, LangSmith, OpenLLM, Giskard, WhyLabs |
| 8 | ⚡ 캐싱 & 최적화 | 7 | Semantic Cache, GPTCache, Prompt Caching, Token Optimizer, Litellm, Marqo, MiniRAG |
| 9 | 🔗 그래프 & 구조화 | 6 | Neo4j, LlamaIndex KG, GraphRAG, Knowledge Graphs, RxDB, Nebula Graph |
| 10 | 🛠 유틸 & 통합 | 9 | Unstructured, LangUI, Cursor Composer, JSONSchema, Query Rewriting, Metadata Filter |
| 11 | 🤖 멀티모달 & 이미지 | 8 | CLIP, GPT-4V, LLaVA, LayoutLM, Tesseract, EasyOCR, ColPali, Qwen-VL |
| 12 | 🔐 보안 & 규정 준수 | 6 | PII Masking, Data Privacy, Audit Trail, Fairness Check, Poisoning Detection |

**총 도구 수: 100+개** (각 카테고리별 최소 6개 이상)

---

## 1⃣ 8 RAG 패턴 개요 & 코드

### 패턴 선택 매트릭스

| 패턴 | 복잡도 | 정확도 | 레이턴시 | 추천 용도 | 선결 조건 |
|------|--------|--------|---------|---------|---------|
| **Naive RAG** |  | ★★☆ | 빠름 | 간단 FAQ, 문서 검색 | Vector DB + 임베딩 |
| **Multimodal** | ★★★ | ★★★★ | 중간 | 이미지 + 텍스트 혼합 | Vision 모델 + 벡터DB |
| **HyDE** | ★★ | ★★★ | 중간 | 검색어 모호, 쿼리 다양성 | LLM + 임베딩 |
| **Corrective (CRAG)** | ★★★ | ★★★★★ | 느림 | 높은 정확도 필요 | 품질 평가 모델 + Web API |
| **Graph RAG** | ★★★★ | ★★★★★ | 느림 | 관계형 지식, 구조화 정보 | Graph DB + NER |
| **Hybrid** | ★★★★ | ★★★★★ | 느림 | 엔터프라이즈 검색 | Vector + Keyword + Graph |
| **Adaptive** | ★★★★ | ★★★★ | 가변 | 복잡 추론, 멀티스텝 | Router + CoT |
| **Agentic** | ★★★★★ | ★★★★★ | 가장 느림 | 동적 도구 사용, MCP 통합 | Tool use + Agent framework |

---

### 패턴 1⃣: Naive RAG (기본 패턴)

**정의**: Query → Embed → Vector Retrieve → Prompt → LLM

```python
# 기본 구현 예시
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import ChatOpenAI

# 1. 문서 로드 및 청킹
documents = load_documents("data.pdf")
chunks = split_documents(documents, chunk_size=1000)

# 2. 임베딩 생성 및 벡터DB 저장
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 3. Retrieval 체인
llm = ChatOpenAI(model="gpt-4")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(k=5)
)

# 4. 쿼리 실행
result = qa_chain.run("질문?")
print(result)
```

**강점**:
- 가장 빠르고 간단
- 구현 진입장벽 낮음
- 비용 효율적

**약점**:
- 정확도 낮음 (관련성 낮은 문서 포함)
- 검색 품질 검증 없음
- 외부 지식 부족 시 성능 저하

---

### 패턴 2⃣: Multimodal RAG

**정의**: 이미지 + 텍스트 동시 벡터화 → 멀티모달 검색

```python
from langchain_community.document_loaders import UnstructuredLoader
from langchain.embeddings.multimodal_embedding import MultiModalEmbedding
from langchain_community.vectorstores import Chroma

# 1. 멀티모달 문서 로드 (이미지+텍스트)
loader = UnstructuredLoader("mixed_content/")
documents = loader.load()  # 이미지는 OCR + 임베딩 자동

# 2. CLIP 또는 비전 모델 기반 임베딩
embeddings = MultiModalEmbedding()  # 자동 이미지 인코딩
vectorstore = Chroma.from_documents(documents, embeddings)

# 3. 텍스트 쿼리 또는 이미지 쿼리 동시 지원
results = vectorstore.similarity_search_with_score(query="쿼리 텍스트", k=5)
# 또는
results_img = vectorstore.similarity_search_by_image("image.png", k=5)
```

**추천 도구**:
- **Vision 모델**: GPT-4V, Claude 3 Vision, LLaVA, Qwen-VL
- **이미지 임베딩**: CLIP, BLIP-2, LayoutLM (표 + 이미지 동시)
- **OCR 통합**: Tesseract, EasyOCR, PaddleOCR

**강점**:
- 이미지 + 텍스트 혼합 데이터 처리
- 시각적 정보 활용

**약점**:
- 높은 계산 비용
- 이미지 임베딩 모델 선택 복잡

---

### 패턴 3⃣: HyDE (Hypothetical Document Embeddings)

**정의**: LLM으로 가상 답변 생성 → 임베딩 후 검색

```python
from langchain.prompts import PromptTemplate
from langchain.llms import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# 1. HyDE 프롬프트
hyde_prompt = PromptTemplate(
    input_variables=["query"],
    template="""다음 쿼리에 대해 한국어로 5문장 가상 답변을 생성하세요 (증거·예시 포함):
    
쿼리: {query}

가상 답변:"""
)

# 2. LLM으로 가상 답변 생성
llm = ChatOpenAI()
hypothetical_doc = hyde_prompt.format_prompt(query="질문").to_string()
hypothetical_response = llm.predict_text(hypothetical_doc)

# 3. 가상 응답 임베딩
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(...)
hypothetical_embedding = embeddings.embed_query(hypothetical_response)

# 4. 임베딩으로 검색
results = vectorstore.similarity_search_by_vector(hypothetical_embedding, k=5)
```

**사용 시나리오**:
- 검색어가 모호하거나 짧음
- 쿼리와 문서 표현 방식이 다름
- 다양한 표현의 문서 검색 필요

**강점**:
- 검색 쿼리 다양성 증대
- 의미 유사도 개선

**약점**:
- LLM 호출 추가 비용
- 가상 답변 품질 의존성

---

### 패턴 4⃣: Corrective RAG (CRAG)

**정의**: 검색 품질 평가 → 부실 시 재검색 또는 웹 폴백

```python
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms import ChatOpenAI

# 1. 검색 품질 평가기
grade_prompt = PromptTemplate(
    input_variables=["document", "query"],
    template="""다음 문서가 쿼리에 관련이 있는가? (yes/no):
    
문서: {document}
쿼리: {query}

판정:"""
)

# 2. CRAG 체인
class CorrectiveRAGChain:
    def __init__(self, retriever, llm, grader_llm):
        self.retriever = retriever
        self.llm = llm
        self.grader = grader_llm
        
    def run(self, query):
        # 1단계: 초기 검색
        initial_docs = self.retriever.get_relevant_documents(query)
        
        # 2단계: 품질 평가
        relevant_docs = []
        for doc in initial_docs:
            grade = self.grader.predict_text(
                grade_prompt.format(document=doc.page_content, query=query)
            )
            if "yes" in grade.lower():
                relevant_docs.append(doc)
        
        # 3단계: 부실 시 웹 검색 폴백
        if not relevant_docs:
            relevant_docs = web_search(query)  # 웹 검색
        
        # 4단계: 답변 생성
        context = "\n".join([d.page_content for d in relevant_docs])
        return self.llm.predict_text(
            f"질문: {query}\n\n문맥:\n{context}\n\n답변:"
        )

# 3. 사용
crag = CorrectiveRAGChain(retriever, llm, grader)
result = crag.run("질문?")
```

**평가 기준**:
- 쿼리-문서 유사도 > 0.7 (임계값)
- 키워드 매칭율 > 30%
- 의미 관련성 정량 점수

**강점**:
- 높은 정확도 (검증된 문서만 사용)
- 부실 시 웹 검색 자동 폴백
- 신뢰도 개선

**약점**:
- 추가 LLM 호출 (평가기)
- 레이턴시 증가
- 웹 API 의존성

---

### 패턴 5⃣: Graph RAG (Knowledge Graph)

**정의**: 문서 → 엔티티 추출 → 그래프 구축 → 관계 기반 검색

```python
from langchain.graphs import Neo4jGraph
from langchain_community.chains import GraphCypherQAChain
from langchain.llms import ChatOpenAI

# 1. 그래프 초기화
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# 2. 문서 → 엔티티 + 관계 추출
from langchain.chains import GraphQAChain
extraction_prompt = """다음 텍스트에서 엔티티와 관계를 추출하세요 (JSON):
{text}

출력 형식:
{
  "entities": [{"name": "...", "type": "..."}],
  "relationships": [{"source": "...", "target": "...", "relation": "..."}]
}"""

# 3. 그래프에 로드
for doc in documents:
    extracted = llm.predict_text(extraction_prompt.format(text=doc))
    graph.query(f"CREATE {extracted}")  # Cypher 생성

# 4. 관계 기반 검색 (Cypher 쿼리)
cypher_chain = GraphCypherQAChain.from_llm_and_graph(
    llm=ChatOpenAI(),
    graph=graph
)

result = cypher_chain.run("A와 B의 관계는?")
```

**그래프 DB 옵션**:
- **Neo4j**: 가장 성숙, 풍부한 도구
- **Nebula Graph**: 분산 그래프 DB
- **ArangoDB**: 멀티모델 DB (그래프 + 문서)

**강점**:
- 엔티티 간 관계 명시적 모델링
- 복합 질문 처리 (A→B→C 경로)
- 지식 그래프로 신뢰도 향상

**약점**:
- 엔티티 추출 정확도 의존
- 그래프 구축 및 유지 비용
- 초기 설정 복잡

---

### 패턴 6⃣: Hybrid RAG (벡터 + 키워드 + 그래프)

**정의**: 벡터 검색 + BM25 키워드 검색 + 그래프 검색 결합

```python
from langchain.retrievers import EnsembleRetriever
from langchain.vectorstores import Chroma
from langchain.retrievers.bm25 import BM25Retriever
from langchain.graphs import Neo4jGraph

# 1. 3개 검색기 초기화
vector_retriever = Chroma(...).as_retriever(k=5)
bm25_retriever = BM25Retriever.from_documents(documents)
graph_retriever = GraphCypherQAChain.as_retriever(graph=graph)

# 2. Ensemble 검색기 (가중 합산)
hybrid_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever, graph_retriever],
    weights=[0.5, 0.3, 0.2]  # 벡터 50%, 키워드 30%, 그래프 20%
)

# 3. 통합 검색
docs = hybrid_retriever.get_relevant_documents("질문?")

# 4. Reciprocal Rank Fusion (RRF)
from langchain_community.retrievers import RFRetriever
rrf_retriever = RFRetriever.from_chain_type(
    chain_type="stuff",
    chain_type_kwargs={"retriever": hybrid_retriever}
)
results = rrf_retriever.get_relevant_documents("질문?")
```

**리랭킹 전략**:
- **Reciprocal Rank Fusion (RRF)**: 순위 기반 합산 (1/(rank+60))
- **Cohere Rerank**: 신경망 기반 리랭킹 (정확도 ★★★★★)
- **Max Marginal Relevance (MMR)**: 다양성 보존

**강점**:
- 모든 검색 방식 장점 통합
- 높은 정확도 + 다양성
- 엔터프라이즈급 성능

**약점**:
- 구현 복잡도 높음
- 가중치 조정 필요
- 레이턴시 누적

---

### 패턴 7⃣: Adaptive RAG (라우터 기반)

**정의**: 쿼리 복잡도 판정 → 다단계 추론 라우팅

```python
from langchain.chains import LLMRouterChain
from langchain.prompts import PromptTemplate

# 1. 라우터 프롬프트 (쿼리 분류)
router_prompt = PromptTemplate(
    input_variables=["query"],
    template="""다음 쿼리의 복잡도를 판정하세요:
    
쿼리: {query}

선택:
1. simple - 한 번의 검색으로 해결 (Naive RAG)
2. moderate - 여러 단계 필요 (Query Decomposition)
3. complex - 도구 사용 필요 (Agentic RAG)

판정:"""
)

# 2. 쿼리 분해 (복잡 쿼리용)
decompose_prompt = PromptTemplate(
    input_variables=["query"],
    template="""다음 쿼리를 3개 이하의 서브쿼리로 분해하세요:
    
쿼리: {query}

서브쿼리:
1. ...
2. ...
3. ..."""
)

# 3. 적응형 RAG 체인
class AdaptiveRAGChain:
    def run(self, query):
        # 1단계: 복잡도 판정
        complexity = llm.predict_text(
            router_prompt.format(query=query)
        )
        
        if "simple" in complexity.lower():
            # Naive RAG
            return naive_rag(query)
        
        elif "moderate" in complexity.lower():
            # 쿼리 분해 + 병렬 검색
            subqueries = llm.predict_text(
                decompose_prompt.format(query=query)
            ).split("\n")
            results = [naive_rag(q) for q in subqueries]
            return combine_results(results)
        
        else:  # complex
            # Agentic RAG
            return agentic_rag(query)

adaptive = AdaptiveRAGChain()
result = adaptive.run("복잡한 질문?")
```

**라우팅 전략**:
- **쿼리 복잡도 분류**: Simple, Moderate, Complex
- **쿼리 분해 (Query Decomposition)**: 멀티홉 추론
- **동적 도구 선택**: 필요한 도구만 활성화

**강점**:
- 효율적 자원 할당
- 복잡도별 최적화
- 비용 + 정확도 균형

**약점**:
- 라우팅 로직 최적화 필요
- 분해 품질 의존

---

### 패턴 8⃣: Agentic RAG (ReAct + MCP)

**정의**: 에이전트 루프 + 도구 사용 (웹 검색, DB 쿼리, 계산 등)

```python
from langchain.agents import Tool, AgentExecutor, initialize_agent
from langchain.agents import AgentType
from langchain.llms import ChatOpenAI
from langchain.tools import BaseTool

# 1. 도구 정의
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "현재 정보를 위해 웹 검색"
    def _run(self, query: str):
        return web_search(query)

class VectorDBSearchTool(BaseTool):
    name = "vector_search"
    description = "내부 문서에서 관련 정보 검색"
    def _run(self, query: str):
        return vectordb.search(query)

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "수치 계산"
    def _run(self, expr: str):
        return eval(expr)

# 2. 에이전트 초기화
tools = [WebSearchTool(), VectorDBSearchTool(), CalculatorTool()]
llm = ChatOpenAI(model="gpt-4")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.REACT_DOCSTORE,  # ReAct 프로토콜
    verbose=True
)

# 3. 실행 (자동 도구 선택 및 반복)
result = agent.run("""
Q: 2024년 최신 AI 논문 + 우리 문서에서 관련 사례 + 비용 계산

Action: 먼저 웹에서 2024 AI 논문 검색
Observation: [웹 결과]

Action: 벡터DB에서 유사 사례 검색
Observation: [DB 결과]

Action: 계산기로 비용 계산
Observation: [계산 결과]

최종 답변: ...
""")
```

**ReAct (Reasoning + Acting) 프로토콜**:
```text
Thought: 다음 단계 계획
Action: 도구 선택
Action Input: 도구 입력
Observation: 도구 결과
Thought: 결과 분석
... (반복)
Final Answer: 최종 답변
```

**MCP (Model Context Protocol) 통합**:
- Slack 메시지 조회
- Google Drive 문서 검색
- Linear 이슈 조회
- GitHub 코드 검색

**강점**:
- 동적 도구 선택
- 복합 작업 자동화
- 외부 시스템 통합

**약점**:
- 도구 선택 오류 가능
- 레이턴시 높음
- 비용 많음

---

## 2⃣ 벡터 데이터베이스 (Vector DB)

| # | 도구명 | 설명 | 설치 명령 | 가격 모델 |
|---|--------|------|---------|---------|
| 2.1 | **ChromaDB** | 가장 간단한 오픈소스 벡터DB (로컬 또는 클라우드) | `pip install chromadb` | 무료 (오픈소스) + 유료 클라우드 |
| 2.2 | **Pinecone** | 완전 관리형 벡터DB (엔터프라이즈급) | `pip install pinecone-client` | 무료 (125만 벡터) + 종량제 |
| 2.3 | **Weaviate** | 멀티모달 + GraphQL API 벡터DB | `pip install weaviate-client` | 무료 (오픈소스) + 유료 클라우드 |
| 2.4 | **Qdrant** | 고성능 벡터 검색 (Rust 기반) | `pip install qdrant-client` | 무료 + 호스팅 서비스 |
| 2.5 | **Milvus** | 분산 벡터DB (대용량) | `pip install pymilvus` | 무료 (오픈소스) |
| 2.6 | **FAISS** | Facebook 메타 벡터 검색 (로컬, 경량) | `pip install faiss-cpu` (또는 `faiss-gpu`) | 무료 (오픈소스) |
| 2.7 | **LanceDB** | 인메모리 벡터DB (Apache Arrow 기반) | `pip install lancedb` | 무료 (오픈소스) |
| 2.8 | **pgvector** | PostgreSQL 확장 (벡터 저장) | PostgreSQL + `CREATE EXTENSION vector` | 무료 (오픈소스) |

### 벡터 DB 초기화 예시

```python
# ChromaDB (가장 간단)
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

vectorstore = Chroma.from_documents(
    documents,
    embeddings=OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)

# Pinecone (관리형, 스케일링)
from langchain.vectorstores import Pinecone
import pinecone

pinecone.init(api_key="KEY", environment="gcp-starter")
vectorstore = Pinecone.from_documents(
    documents,
    embeddings,
    index_name="my-index"
)

# Qdrant (오픈소스, 고성능)
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient

client = QdrantClient(":memory:")
vectorstore = Qdrant.from_documents(
    documents,
    embeddings,
    client=client,
    collection_name="my_collection"
)
```

---

## 3⃣ 임베딩 모델 (Embedding Models)

| # | 모델명 | 설명 | 크기 | 비용 | 설치 명령 |
|---|--------|------|------|------|---------|
| 3.1 | **OpenAI text-embedding-3-large** | 최고 품질 (1536차원) | 크기: 1536 | $0.02/1M 토큰 | `from langchain.embeddings import OpenAIEmbeddings` |
| 3.2 | **OpenAI text-embedding-3-small** | 경량 (384차원) | 크기: 384 | $0.02/1M 토큰 | 위 동일 |
| 3.3 | **Cohere Embed v3** | 멀티언어 강력 (1024차원) | 크기: 1024 | $1/1M 토큰 (검색), $0.10 (분류) | `from langchain.embeddings import CohereEmbeddings` |
| 3.4 | **Sentence-Transformers (all-MiniLM-L6-v2)** | 경량 오픈소스 (384차원) | 크기: 384 | 무료 | `pip install sentence-transformers` |
| 3.5 | **BAAI/bge-large-en** | 높은 품질 오픈소스 (1024차원) | 크기: 1024 | 무료 | `pip install FlagEmbedding` |
| 3.6 | **BAAI/bge-m3** | 멀티언어 (1024차원, 밀집+희소) | 크기: 1024 | 무료 | 위 동일 |
| 3.7 | **Instructor Embeddings** | 작업별 명령 기반 (768차원) | 크기: 768 | 무료 | `pip install InstructorEmbedding` |
| 3.8 | **Nomic AI embed-text-v1** | 무한 컨텍스트 길이 (768차원) | 크기: 768 | 무료 | `from nomic import embed` |
| 3.9 | **Jina Embeddings v3** | 멀티모달 + 매우 길은 컨텍스트 (1024차원) | 크기: 1024 | 무료 (자체) + API 유료 | `pip install jina` |

### 임베딩 모델 비교 코드

```python
# OpenAI (최고 품질, 유료)
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector = embeddings.embed_query("검색 쿼리")

# Sentence-Transformers (경량, 무료)
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
vector = model.encode("검색 쿼리")

# BAAI/BGE (높은 품질, 무료)
from FlagEmbedding import FlagModel
model = FlagModel('BAAI/bge-large-en', query_instruction_for_retrieval="Represent this sentence for searching relevant passages:")
vector = model.encode_queries(["검색 쿼리"])[0]

# Jina AI (매우 긴 컨텍스트)
from jina import Client
client = Client(host='grpcs://api.jina.ai')
vector = client.encode(['매우 긴 문서...'], show_progress=True)
```

---

## 4⃣ 청킹 전략 (Text Splitting & Chunking)

| # | 도구/전략 | 설명 | 용도 | 설치 명령 |
|---|----------|------|------|---------|
| 4.1 | **RecursiveCharacterTextSplitter** | 문자 기반 재귀 분할 | 일반 텍스트 | `from langchain.text_splitter import RecursiveCharacterTextSplitter` |
| 4.2 | **SemanticChunker** | 의미 유사도 기반 분할 | 의미 보존 중요 | `from langchain.text_splitter import SemanticSimilarityTextSplitter` |
| 4.3 | **MarkdownHeaderTextSplitter** | Markdown 헤더 구조 유지 | Markdown 문서 | `from langchain.text_splitter import MarkdownHeaderTextSplitter` |
| 4.4 | **HTMLSplitter** | HTML 태그 기반 분할 | 웹 콘텐츠 | 커스텀 구현 |
| 4.5 | **TokenTextSplitter** | 토큰 기반 정확한 분할 | 토큰 제한 | `from langchain.text_splitter import TokenTextSplitter` |
| 4.6 | **SentenceWindowNodeParser** | 문장 + 윈도우 컨텍스트 | 문맥 유지 | `from llama_index.node_parser import SentenceWindowNodeParser` |
| 4.7 | **LangChain Document Loaders** | PDF, DOCX, JSON 등 로드 + 분할 | 다양한 형식 | `from langchain.document_loaders import *` |

### 청킹 코드 예시

```python
# 1. RecursiveCharacterTextSplitter (기본)
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)
chunks = splitter.split_text(text)

# 2. SemanticChunker (의미 기반)
from langchain.text_splitter import SemanticSimilarityTextSplitter
from langchain.embeddings import OpenAIEmbeddings

splitter = SemanticSimilarityTextSplitter(
    embeddings=OpenAIEmbeddings(),
    chunk_size=1000
)
chunks = splitter.split_text(text)

# 3. MarkdownHeaderTextSplitter (Markdown)
from langchain.text_splitter import MarkdownHeaderTextSplitter
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
)
splits = splitter.split_text(markdown_text)

# 4. SentenceWindowNodeParser (LlamaIndex)
from llama_index.node_parser import SentenceWindowNodeParser
parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,
    window_metadata_key="window"
)
nodes = parser.get_nodes_from_documents(documents)
```

---

## 5⃣ RAG 프레임워크 (High-Level Frameworks)

| # | 프레임워크 | 설명 | 강점 | 약점 | 설치 명령 |
|---|-----------|------|------|------|---------|
| 5.1 | **LangChain** | 가장 인기 있는 LLM 체인 프레임워크 | 풍부한 도구, 생태계 | 낮은 추상화 | `pip install langchain langchain-openai` |
| 5.2 | **LlamaIndex (GPT Index)** | 구조화된 데이터 + 벡터 인덱싱 | 인덱싱 최적화, 로우레벨 컨트롤 | 가파른 학습곡선 | `pip install llama-index` |
| 5.3 | **Haystack** | 검색 중심 프레임워크 | 검색 파이프라인 최적화 | 커뮤니티 작음 | `pip install haystack-ai` |
| 5.4 | **RAGFlow** | Dify + RAG 통합 (로우코드) | 시각적 워크플로우 | 확장성 제한 | Docker: `docker run ragflow` |
| 5.5 | **Verba** | 로컬 RAG (오프라인) | 프라이버시, 오프라인 | 기능 제한 | `pip install verba` |
| 5.6 | **AutoRAG** | RAG 파이프라인 자동 최적화 | 실험 추적, 자동 튜닝 | 구현 복잡 | `pip install autorag` |

### 프레임워크 비교 코드

```python
# LangChain (가장 유연)
from langchain.chains import RetrievalQA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# LlamaIndex (인덱싱 강화)
from llama_index import GPTVectorStoreIndex
index = GPTVectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("질문?")

# Haystack (검색 파이프라인)
from haystack import Pipeline
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
pipeline = Pipeline()
pipeline.add_component("retriever", InMemoryBM25Retriever(docs))
result = pipeline.run({"retriever": {"query": "질문?"}})
```

---

## 6⃣ 리랭킹 & 고급 리트리버 (Reranking & Advanced Retrieval)

| # | 도구명 | 설명 | 정확도 | 비용 | 설치 명령 |
|---|--------|------|--------|------|---------|
| 6.1 | **Cohere Rerank 3** | 신경망 기반 리랭킹 (SOTA) | ★★★★★ | $1/1000 쿼리 | `from cohere import Client` |
| 6.2 | **ColBERT** | 밀집 검색 + 듀얼 인코더 | ★★★★ | 무료 | `pip install colbert-ai` |
| 6.3 | **bge-reranker-large** | BAAI 오픈소스 리랭킹 | ★★★★ | 무료 | `pip install FlagEmbedding` |
| 6.4 | **FlashRank** | 경량 리랭킹 (빠름) | ★★★ | 무료 | `pip install FlashRank` |
| 6.5 | **RankLLM** | LLM 기반 리랭킹 (pairwise) | ★★★★ | API 비용 | `pip install rankllm` |
| 6.6 | **Jina Reranker** | 멀티언어 리랭킹 | ★★★★ | 무료 API + 호스팅 | `pip install jina` |
| 6.7 | **Reciprocal Rank Fusion (RRF)** | 여러 검색기 결과 융합 | ★★★ | 무료 | `from langchain_community.retrievers import RFRetriever` |

### 리랭킹 코드 예시

```python
# Cohere Reranker (가장 높은 품질)
from cohere import Client
co = Client(api_key="$API_KEY")

# 초기 검색
docs = retriever.get_relevant_documents("질문?")
doc_texts = [d.page_content for d in docs]

# 리랭킹
reranked = co.rerank(
    query="질문?",
    documents=doc_texts,
    top_n=3,
    model="rerank-english-v3.0"
)

# BGE Reranker (무료)
from FlagEmbedding import FlagReranker
reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True)
scores = reranker.compute_score([[query, doc.page_content] for doc in docs])
reranked_docs = [doc for _, doc in sorted(zip(scores, docs), reverse=True)]
```

---

## 7⃣ 평가 & 모니터링 (Evaluation & Monitoring)

| # | 도구명 | 설명 | 메트릭 | 설치 명령 |
|---|--------|------|--------|---------|
| 7.1 | **RAGAS** | RAG 평가 프레임워크 (SOTA) | Faithfulness, Relevance, F1 | `pip install ragas` |
| 7.2 | **DeepEval** | LLM 기반 평가 (Confident AI) | Hallucination, Retrieval, Triad | `pip install deepeval` |
| 7.3 | **TruLens** | LLM 애플리케이션 모니터링 | Feedback, RAG triad | `pip install trulens-eval` |
| 7.4 | **Phoenix** | 실시간 관찰 + 평가 (오픈소스) | Retrieval quality, Hallucination | `pip install arize-phoenix` |
| 7.5 | **LangSmith** | LangChain 통합 평가 (프로덕션) | 추적, A/B 테스트, 피드백 | LangChain 내장 |
| 7.6 | **OpenLLM Leaderboard** | 모델 벤치마크 | 기본 모델 성능 | https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard |
| 7.7 | **Giskard** | AI 안전 평가 | 편향, 독성, 견고성 | `pip install giskard` |
| 7.8 | **WhyLabs** | 데이터/모델 모니터링 | 드리프트, 이상치 | `pip install whylogs` |

### RAGAS 평가 코드

```python
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_relevance,
    context_precision,
    context_recall,
    answer_similarity
)

# 평가 데이터셋
eval_dataset = {
    "questions": ["질문 1?", "질문 2?"],
    "ground_truths": [["정답 1"], ["정답 2"]],
    "contexts": [
        [["문맥 1"]],
        [["문맥 2"]]
    ],
    "answers": ["답변 1", "답변 2"]
}

# 평가 실행
results = evaluate(
    dataset=eval_dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_relevance,
    ]
)

print(results)
# 출력: {'faithfulness': 0.92, 'answer_relevancy': 0.88, ...}
```

---

## 8⃣ 캐싱 & 최적화 (Caching & Optimization)

| # | 도구명 | 설명 | 절감율 | 설치 명령 |
|---|--------|------|--------|---------|
| 8.1 | **Semantic Cache** | 의미 기반 캐싱 (LangChain 내장) | 30-50% 토큰 절감 | LangChain 내장 |
| 8.2 | **GPTCache** | LLM 응답 캐싱 | 90% 토큰 절감 | `pip install gptcache` |
| 8.3 | **Prompt Caching (Claude API)** | 프롬프트 캐싱 (1M 컨텍스트) | 90% 토큰·비용 절감 | Anthropic SDK 내장 |
| 8.4 | **Token Optimizer** | 토큰 수 자동 최적화 | 20-40% 감소 | 커스텀 구현 |
| 8.5 | **LiteLLM** | API 통합 + 캐싱 | 여러 제공자 지원 | `pip install litellm` |
| 8.6 | **Marqo** | 임베딩 캐싱 + 벡터 검색 | 75% 임베딩 비용 절감 | `pip install marqo` |
| 8.7 | **MiniRAG** | 경량 RAG (오프라인) | 99% 온라인 비용 절감 | 오픈소스 |

### Prompt Caching 코드 (Claude API)

```python
from anthropic import Anthropic

client = Anthropic()

# 긴 컨텍스트 (캐시 대상)
long_context = "..." * 10000  # 매우 긴 시스템 프롬프트

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "당신은 도움이 되는 어시스턴트입니다.",
        },
        {
            "type": "text",
            "text": long_context,
            "cache_control": {"type": "ephemeral"}  # 캐시 활성화
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "질문?"
        }
    ]
)

# 첫 요청: 캐시 작성 (비용 높음)
# 두 번째 요청부터: 캐시 히트 (토큰 90% 절감)
print(response.usage)
# input_tokens: 120 (캐시 히트)
# cache_creation_input_tokens: 12000 (첫 요청만)
# cache_read_input_tokens: 10800 (두 번째 요청부터)
```

---

## 9⃣ 그래프 & 지식 구조화 (Knowledge Graphs)

| # | 도구명 | 설명 | 설치 명령 | 가격 |
|---|--------|------|---------|------|
| 9.1 | **Neo4j** | 가장 성숙한 그래프 DB | `pip install neo4j` | 무료 (Community) + 유료 |
| 9.2 | **LlamaIndex KG Index** | LlamaIndex 통합 그래프 | `pip install llama-index` | 무료 |
| 9.3 | **GraphRAG (Microsoft)** | 지역 + 전역 그래프 검색 | `pip install graphrag` | 무료 (오픈소스) |
| 9.4 | **Knowledge Graphs (spaCy)** | NER 기반 엔티티·관계 추출 | `pip install spacy` | 무료 |
| 9.5 | **RxDB** | 분산 문서 DB + 그래프 | `npm install rxdb` | 무료 |
| 9.6 | **Nebula Graph** | 분산 그래프 DB (대규모) | Docker 또는 클라우드 | 무료 (오픈소스) |

### Neo4j + GraphRAG 코드

```python
from langchain.graphs import Neo4jGraph
from langchain_community.chains import GraphCypherQAChain
from langchain.llms import ChatOpenAI

# 1. 그래프 초기화
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# 2. 엔티티·관계 추출 후 그래프 구축
from langchain.chains import create_extraction_chain
extraction_prompt = """텍스트에서 엔티티와 관계를 추출:
{text}

JSON 형식:
{"entities": [...], "relationships": [...]}"""

# 3. Cypher QA
cypher_chain = GraphCypherQAChain.from_llm_and_graph(
    llm=ChatOpenAI(),
    graph=graph,
    verbose=True
)

result = cypher_chain.run("A와 B의 최단 경로는?")
```

---

## 🔟 유틸리티 & 통합 도구 (Utilities & Integration)

| # | 도구명 | 설명 | 설치 명령 |
|---|--------|------|---------|
| 10.1 | **Unstructured** | PDF, DOCX, HTML 등 자동 파싱 | `pip install unstructured` |
| 10.2 | **LangUI** | RAG UI 빌더 (Streamlit 기반) | `pip install langui` |
| 10.3 | **Cursor Composer** | IDE에서 RAG 통합 | VS Code 확장 |
| 10.4 | **JSONSchema** | 구조화 출력 강제 | LangChain 내장 |
| 10.5 | **Query Rewriting** | 쿼리 자동 개선 | 커스텀 LLM 프롬프트 |
| 10.6 | **Metadata Filtering** | 메타데이터 기반 검색 필터 | 벡터DB 기능 |
| 10.7 | **Caching Layer** | 요청 캐싱 (Redis) | `pip install redis` |
| 10.8 | **Async RAG** | 비동기 병렬 검색 | `asyncio` + `aiohttp` |
| 10.9 | **RAG Tracing** | 디버깅·모니터링 | LangSmith / Phoenix |

---

## 1⃣1⃣ 멀티모달 & 이미지 처리 (Multimodal & Vision)

| # | 도구명 | 설명 | 용도 | 설치 명령 |
|---|--------|------|------|---------|
| 11.1 | **CLIP** | 이미지-텍스트 쌍 임베딩 | 이미지 검색 | `pip install clip-by-openai` |
| 11.2 | **GPT-4V** | Vision 기능 (OpenAI) | 이미지 질문·분석 | OpenAI API |
| 11.3 | **Claude 3 Vision** | Vision 기능 (Anthropic) | 이미지 질문 | Anthropic API |
| 11.4 | **LLaVA** | 오픈소스 Vision LLM | 로컬 이미지 분석 | `pip install llava` |
| 11.5 | **Qwen-VL** | 멀티언어 Vision (Alibaba) | 한글 이미지 분석 | Hugging Face |
| 11.6 | **LayoutLM** | 문서 표/레이아웃 인식 | 스캔 문서 처리 | `pip install layoutlm` |
| 11.7 | **Tesseract** | OCR (텍스트 추출) | 스캔 이미지 → 텍스트 | Ubuntu: `apt install tesseract-ocr` |
| 11.8 | **EasyOCR** | 다국어 OCR | 한글 + 다국어 | `pip install easyocr` |

### Vision RAG 코드

```python
from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import HumanMessage

# GPT-4V 기반 이미지 분석
llm = ChatOpenAI(model="gpt-4-vision-preview")

# 로컬 이미지 처리
import base64
with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

message = HumanMessage(
    content=[
        {"type": "text", "text": "이미지에서 중요한 정보 추출"},
        {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{image_data}"
        }
    ]
)

response = llm.invoke([message])
print(response.content)
```

---

## 1⃣2⃣ 보안 & 규정 준수 (Security & Compliance)

| # | 도구명 | 설명 | 설치 명령 |
|---|--------|------|---------|
| 12.1 | **PII Masking** | 개인정보 자동 가림 | 커스텀 또는 `presidio` |
| 12.2 | **Data Privacy (Differential Privacy)** | 프라이버시 보존 | `pip install diffprivlib` |
| 12.3 | **Audit Trail** | 모든 쿼리·응답 로깅 | SQLite 또는 로그 서비스 |
| 12.4 | **Fairness Check** | 편향 탐지 | `pip install fairlearn` |
| 12.5 | **Poisoning Detection** | 적대적 입력 감지 | 커스텀 또는 `foolbox` |
| 12.6 | **SSL/TLS** | 전송 암호화 | HTTPS 설정 |

---

## 📋 빠른 선택 가이드 (Quick Decision Tree)

```text
Q1: 검색 데이터 크기는?
├─ < 10K 문서 → ChromaDB (가장 간단)
├─ 10K ~ 1M → Qdrant (고성능)
└─ > 1M → Pinecone (관리형 스케일)

Q2: 정확도 우선도는?
├─ 높음 (90%+) → Corrective RAG + Cohere Rerank
├─ 중간 (70-85%) → HyDE + BGE Reranker
└─ 속도 우선 → Naive RAG + FAISS

Q3: 구조화 정보 있는가?
├─ 네 → Graph RAG + Neo4j
├─ 혼합 → Hybrid RAG
└─ 아니오 → Multimodal or Adaptive RAG

Q4: 외부 도구 필요한가?
├─ 예 (웹 검색, DB 쿼리) → Agentic RAG
└─ 아니오 → 위 패턴들

Q5: 프라이버시 우선인가?
├─ 예 → 오프라인 (Verba, MiniRAG, Ollama)
└─ 아니오 → API 기반 (OpenAI, Cohere)
```

---

##  참고 자료 & 학습 순서

### 1단계: 기초 (1주)
1. Naive RAG (LangChain 튜토리얼)
2. ChromaDB 또는 Qdrant 설치
3. OpenAI 또는 open source 임베딩 시작

### 2단계: 중급 (2주)
1. HyDE, Corrective RAG 이해
2. Reranking (Cohere) 통합
3. RAGAS 평가 시작

### 3단계: 고급 (3주)
1. Graph RAG + Neo4j
2. Hybrid RAG (벡터 + 그래프)
3. Adaptive 라우팅 구현

### 4단계: 프로덕션 (4주)
1. Agentic RAG + MCP
2. Prompt Caching (Claude API)
3. LangSmith / Phoenix 모니터링

---

## 🔗 공식 문서 링크

| 도구 | 공식 문서 |
|------|---------|
| LangChain RAG | https://docs.langchain.com/use_cases/question_answering |
| LlamaIndex | https://docs.llamaindex.ai |
| RAGAS | https://docs.ragas.io |
| Pinecone | https://docs.pinecone.io |
| Cohere | https://docs.cohere.com/reference/rerank |
| Neo4j | https://neo4j.com/docs |
| Anthropic Claude API | https://docs.anthropic.com |

---

## 📝 최종 요약

**100+ 도구, 8 패턴, 3 레벨**:
- **Beginners**: Naive RAG + ChromaDB + OpenAI embeddings
- **Intermediate**: HyDE/Corrective + Hybrid retrieval + Reranking
- **Advanced**: Graph RAG + Agentic + Custom evaluation

**선택 기준**:
1. 데이터 크기 → Vector DB 선택
2. 정확도 필요도 → 패턴 선택
3. 구조 유무 → Graph 추가 여부
4. 도구 필요도 → Agentic 고려

**최종 팁**:
- 항상 Naive RAG 에서 시작 (기준점)
- RAGAS 로 평가 (객관적 메트릭)
- Prompt Caching 으로 비용 90% 절감
- MCP 통합으로 동적 도구 사용

---

**마지막 수정**: 2026-05-20
**작성자**: Claude (Orchestration Kit)
**라이선스**: MIT (공개 킷)
