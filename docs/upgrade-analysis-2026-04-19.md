# Upgrade Analysis — 2026-04-19

> 외부 자료 (docs/upgrade 이미지 6장 + Instagram 2 posts) 분석 + 이 킷 적용 방향

---

## 자료 1: docs/upgrade/*.jpg (카카오톡 캡처 6장)

### 이미지 1: 8 RAG Architectures (mcp.DailyDoseofDS.com)
8가지 RAG 패턴 시각 비교:
1. **Naive RAG** — Query → Embed → VectorDB → Prompt → LLM
2. **Multimodal RAG** — 이미지·텍스트 동시 검색
3. **HyDE** — Hypothetical Response 생성 후 검색
4. **Corrective RAG** — Grade → Query Analyzer → Web Search fallback
5. **Graph RAG** — Graph Generator → Graph DB
6. **Hybrid RAG** — Vector + Graph DB 동시 사용
7. **Adaptive RAG** — Multi-step Reasoning Chain
8. **Agentic RAG** — ReAct + CoT, 다중 에이전트, MCP 서버 연결

### 이미지 2: Classic vs Graph vs Agentic RAG (Brij Kishore Pandey)
- **Classic**: Retrieves · Fast · Simple · Single-hop
- **Graph**: Connects · Entity-rich · Relational · Multi-source
- **Agentic**: Reasons · Adaptive step · Self-correcting

### 이미지 3: $0 AI Architecture Stack 2026 (Brij)
무료·로컬 기반 AI 스택:
- Frontend: Next.js · Streamlit · Vercel(free tier)
- Orchestrator: **LangGraph · CrewAI**
- LLM: **Ollama**(로컬) · Gemma 4 E4B · Llama 3.3 70B · Mistral Small 4
- RAG: **LlamaIndex** · **ChromaDB · Qdrant**(local)
- Tool Use: **MCP**
- Code Agent: **Claude Code CLI** · Aider
- Data: SQLite · DuckDB · Supabase(free tier)
- Observability: **Phoenix** (self-hosted)
- Deployment: Docker · Cloudflare Workers · HuggingFace Spaces

### 이미지 4: How to Design a CLAUDE.md (Brij)
**3 Scopes**: Global (`~/.claude/CLAUDE.md`) → Project (`./CLAUDE.md`) → Folder (`./src/CLAUDE.md`). **Last scope wins on conflicts**.

**WHAT/WHY/HOW 프레임**:
- WHAT — Context (stack·purpose·dependencies·env)
- WHY — Principles (architecture·style·anti-patterns)
- HOW — Workflows (build·test·lint·commit·deploy)

**5 Rules**:
1. Run `/init` first
2. Stay under 500 lines
3. Use Hooks for 100% enforcement
4. Update monthly
5. Reference files, don't duplicate

### 이미지 5: Claude is Eating Up Everything (Ruben Hassid)
Claude 생태계 전체 맵:
- **Work Modes**: Claude Chat · Cowork · Code · Projects
- **For Teams**: Team Plan · Enterprise · Shared Projects · Markdown Files · AskUserQuestion · 1M Token Window · Global Instructions
- **Models**: Opus 4.7 · Sonnet 4.6 · Haiku 4.5 · Extended Thinking
- **Integrations**: Claude in Excel · Chrome · Connectors · Plugins
- **Create**: Artifacts · Skills · Prompt Templates

### 이미지 6: Claude Code Project Structure (Brij)
표준 디렉토리 구조 + CLAUDE.md Essentials:
```
my_project/
├── CLAUDE.md
├── .claude/{commands,skills,agents,hooks,rules}/
├── .mcp.json
├── docs/{architecture,api-spec,onboarding}/
├── src/
└── tests/
```

**Best Practices**:
- Iterative Development · Git workflow
- Modular Design (break into modules)
- **Regular Testing & Auditing**

---

## 자료 2: Instagram Posts

### Post 1: @aifornontechies "Cowork Essentials"
**50개 Claude Cowork 스킬 번들** — 직원 없이 사업 운영:
- 이메일 핸들링
- 영수증 스캔
- 슬라이드 덱 빌드
- 제안서 작성
- 주간 계획
- 계약 검토
- 아침 브리핑 초안

**시사점**: 우리는 **개별 플러그인 단위** — "Essentials bundle" 패키지 개념 없음. `plug_all` 이 있긴 하지만 MCP 설치 묶음일 뿐, 업무 워크플로우 번들은 부재.

### Reel 2: 8 AI Architectures
**LLMs ≠ 모든 AI 모델**:
1. **LCM** (Large Concept Models) — Meta SONAR, 개념 단위 임베딩
2. **VLM** (Vision-Language) — 멀티모달
3. **SLM** (Small Language Models) — 엣지·로컬
4. **MoE** (Mixture of Experts) — 선택적 활성화
5. **MLM** (Masked Language Models) — 양방향 컨텍스트
6. **LAM** (Large Action Models) — 시스템 조작
7. **SAM** (Segment Anything) — 픽셀 세그먼트
8. **LLM** — 텍스트 처리·추론

**시사점**: `route_dispatch` 의 AI 매트릭스가 **LLM 위주**. VLM·SLM·MoE 를 포함한 아키텍처별 라우팅 로직 부재.

---

## 이 킷에 부족한 것 (전체 gap 분석)

| 영역 | 상태 | 권장 |
|------|------|------|
| RAG 파이프라인 | ❌ 없음 | `ai_rag` 스펙 (8 패턴) — 로드맵 Phase 3 → Phase 2 승급 검토 |
| 8 AI 아키텍처 인지 | ❌ LLM only | `ai_models` or `ai_arch` 신규 스펙 |
| 로컬 LLM ($0) | ❌ API만 | `exec_offline` — Ollama·Phoenix 통합 |
| CLAUDE.md 5 Rules | ⚠ 일부 | ✅ CLAUDE.md 재구성 완료 (오늘) |
| Workflow Essentials 번들 | ❌ 없음 | `bundles_cowork` 같은 패키지 |
| Observability | ⚠ 기본만 | Phoenix 통합 검토 |
| Extended Thinking 가이드 | ❌ 없음 | CLAUDE.md 또는 guide.txt 에 섹션 |
| 1M Token Window 활용 | ⚠ 명시 안 됨 | guide.txt 에 가이드 추가 |

---

## 즉시 반영한 것 (오늘 세션)

1. ✅ **CLAUDE.md 재구성** — Brij 5 Rules + WHAT/WHY/HOW + 3 Scopes
2. ✅ **`.claude/rules/claude-md-design.md`** — CLAUDE.md 규칙 박제
3. ✅ **`.claude/rules/best-practices.md`** — Best Practices + Extended Thinking + 1M + Artifacts/Skills/Plugins 구분
4. ✅ **`plugins/ai_rag/`** — 8 RAG 패턴 신규 (이미지 1·2) — 기존에 없던 영역
5. ✅ **`plugins/exec_offline/`** — 로컬 $0 스택 신규 (이미지 3) — 기존에 없던 영역
6. ✅ **`plugins/_template/.mcp.json.example`** — MCP 표준 예시 (이미지 6)
7. ✅ **`route_dispatch.md § Step 2.6`** — 8 AI 아키텍처 인지 섹션 (IG Reel 2 통합)

## 삭제된 것 (중복 — 기존 플러그인과 겹쳐 제거)

- ❌ **`plugins/ai_arch/`** — `route_dispatch` 와 개념 중복 → route_dispatch 에 Step 2.6 섹션으로 통합
- ❌ **`plugins/bundles_cowork/`** — 7개 커맨드 모두 기존 플러그인 호출 wrapper:
  - email → `mcp_collab` (Gmail)
  - receipt → `mcp_docs` (OCR)
  - deck → `design_ppt/make-ppt`
  - proposal → `design_word/word-make`
  - contract → `design_pdf/pdf-sign`
  - plan → `exec_scheduler`
  - briefing → Claude 직접 (세션 요약 `/summarize` 유사)
  → 각 기존 플러그인에서 조합 호출 (wrapper 불필요)

## 원칙: "기존 건드리지 않고 신규만, 있으면 보완"

사용자 지시 반영:
- 신규 영역만 **신규 플러그인** (ai_rag, exec_offline)
- 개념 중복이면 **기존 스킬에 섹션 추가** (ai_arch → route_dispatch)
- 커맨드 wrapper 는 **불필요** (Claude 가 기존 커맨드 조합 호출)

---

## 다음 세션 후보

- `plugins/ai_rag/` 스펙 스켈레톤 (8 RAG 커맨드)
- `plugins/ai_arch/` 스펙 (8 아키텍처 라우팅)
- `plugins/exec_offline/` — Ollama·Phoenix $0 스택
- `route_dispatch v3` — 모델 아키텍처 인지 라우팅
- `bundles_cowork` — 50 스킬 번들 개념 연구

---

## 출처

- docs/upgrade/KakaoTalk_20260419_133731661_*.jpg (6장)
- https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies)
- https://www.instagram.com/reel/DUrAxgmDa9p/

본 문서: `docs/upgrade-analysis-2026-04-19.md`
