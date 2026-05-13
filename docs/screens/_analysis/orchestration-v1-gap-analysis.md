# Orchestration_v1 Gap Analysis — vs Global SOTA (2026-05-13)

> **Methodology**: Full codebase survey (CLAUDE.md, architecture-patterns, 26 plugins, 12 lib modules, 24 hooks) + global reference comparison (Anthropic engineering, LangGraph, CrewAI, AutoGen, Anthropic Skills spec).
>
> **Conclusion**: Orchestration_v1 **exceeds educational tooling** (single-LLM LangChain) in 6 areas (routing, state, plugin architecture, cost observation, failure modes, teaching format). **Gaps vs production SOTA**: streaming events, human-in-the-loop gates, distributed tracing, multi-agent group chat, vector search, execution sandbox. Ranked by **impact × implement ease** below.

---

## Executive Summary (250 words)

**orchestration_v1 is strategically strong in AI orchestration infrastructure** (5-tier routing, SQLite state, quota/budget management, 24/7 watchdog) but **missing 3 critical production features** blocking enterprise deployment:

1. **Human-in-the-loop approval gates** (Impact: Safety/Compliance, Ease: MEDIUM)
   - Global SOTA (Anthropic agents, CrewAI, AutoGen) all include approval workflows
   - Current: No task pause/resume mechanism; missing `/approve` command
   - Gap: Users cannot interrupt execution for human review (risky for financial/legal changes)
   - Add: Task state `waiting_approval` in orca.db + skill-approval-gate

2. **Distributed observability layer** (Impact: Visibility/Debugging, Ease: MEDIUM)
   - LangGraph, LangChain, AutoGen ship with Langfuse/Phoenix integration
   - Current: Logs to `.claude/logs/` files; no structured tracing across AI calls
   - Gap: Cannot see which AI chose which path, token-level cost attribution, anomaly detection invisible
   - Add: Langfuse SDK hook + dashboard integration

3. **Vector semantic search** (Impact: RAG quality, Ease: EASY)
   - Anthropic skills, LangChain RAG, CrewAI all use vector stores (Pinecone, FAISS, Supabase)
   - Current: `ai_rag` plugin has BM25 keyword search only
   - Gap: Cannot retrieve semantically similar docs; falls back to naive keyword matching
   - Add: `ai_rag_vector` plugin with FAISS/Supabase + embedding cache

**Secondary gaps** (not blocking enterprise use): state time-travel (nice-to-have), group chat (niche), batch API optimization (marginal savings), code sandbox (Linux only).

**Why now**: Phase 1 roadmap (exec_scheduler, mcp_social, cost_youtube, design_web) assumes these 3 exist. Without them, production use cases fail: approval loops for compliance, observability for debugging, RAG for knowledge bases.

---

## Honest Scorecard (12 Categories, 1-10 Scale)

| Category | Score | Rationale |
|----------|-------|-----------|
| **Agent Patterns** | 8 | Prompt chaining ✓, routing ✓, parallelization ✓, orchestrator-workers ✓. Missing: evaluator-optimizer loops (eval_quality exists but not iterative) |
| **State & Memory** | 7 | SQLite state ✓, quota/budget ✓. Missing: episodic memory (session history), semantic memory (vector store), time-travel snapshots |
| **Streaming & UX** | 4 | No intermediate event streaming. Hooks exist but no callback chains or progress bars. Missing: token-level progress, intermediate tool results |
| **Human-in-the-Loop** | 3 | No approval gates, no interrupt-and-resume, no edit-then-continue. Critical gap for compliance |
| **Tool Use** | 7 | MCP servers ✓, parallel tool calls (Codex×4) ✓. Missing: result validation, fallback chains documented, computer-use (screenshot/click) |
| **Multi-Agent Coordination** | 5 | Orca auto-spawn workers ✓, task queue ✓. Missing: group chat, agent-to-agent delegation, message routing, conflict resolution |
| **Evaluation** | 6 | eval_quality plugin ✓, failure modes ✓. Missing: golden dataset regression testing, A/B prompt comparison, behavioral metrics |
| **Observability** | 3 | File logs ✓, metrics DB ✓. Missing: distributed tracing, token-level attribution, Langfuse/Phoenix integration, anomaly detection dashboard |
| **Safety** | 8 | Secret scanning ✓, prompt injection blocks ✓, jailbreak detection ✓, sandbox isolation (via MCP). Missing: output filtering, adversarial testing |
| **Deployment** | 7 | Worker pools ✓, graceful shutdown ✓, 24/7 VPS ✓. Missing: blue-green, autoscaling, canary rollouts, load balancing |
| **Developer Experience** | 8 | Plugin scaffolding ✓, hot reload via sync ✓, CLAUDE.md discipline ✓. Missing: VSCode debugger integration, local testing framework |
| **Documentation** | 9 | CLAUDE.md, architecture-patterns, 21-rule failure modes, teaching-doc format (8 sections). Runnable examples ✓. Missing: auto-gen API docs from plugin.json |

**Overall: 6.5/10** — Strong infrastructure, critical production features missing.

---

## Detailed Gap Analysis (12 Categories × Status)

### 1. Agent Patterns (8/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Prompt chaining | ✅ | `route_dispatch.md` | None — fully implemented | Anthropic "Building Effective Agents" |
| Routing | ✅ | `router.py` (5-tier decision tree) | None — sophisticated | Anthropic |
| Parallelization | ✅ | `route.py` (Codex×4, Haiku×2) | None | Anthropic |
| Orchestrator-workers | ✅ | `exec_orca-auto.md` + `.claude/state/orca.db` | None | Anthropic |
| Evaluator-optimizer | ⚠️ | `eval_quality/` plugin | **Missing: iterative loops**. Has 1-shot eval, not 3-5 refinement cycles | LangChain, CrewAI |
| Planning transparency | ❌ | `auto-planner.md` (5-step) | **Missing: show reasoning steps to user**. Currently silent internal state | Anthropic (explicit steps) |

**Gap Summary**: eval_quality needs multi-round refinement loops. auto-planner should emit visible step progress.

---

### 2. State & Memory (7/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Short-term scratchpad | ✅ | Task instruction in memory | ✓ | LangGraph |
| Long-term episodic | ⚠️ | `exec_learning/` plugin (failure patterns) | **Missing: session history retrieval**. Has pattern accumulation, not indexed search | CrewAI memory |
| Semantic memory | ❌ | — | **MISSING ENTIRELY**. No vector store for knowledge | LangGraph, CrewAI |
| Procedural memory | ⚠️ | `skill-*.md` (procedures as skills) | Partial. Skills are static, not learned/adapted | AutoGen reflection |
| State snapshots | ✅ | `exec_session_guard.md` | ✓ Saves state on shutdown | LangGraph |
| Time-travel (rewind) | ❌ | — | **Missing entirely**. No way to undo & redo | LangGraph state graph |

**Gap Summary**: Add vector store (FAISS/Supabase) for semantic memory. Implement state branching for time-travel.

---

### 3. Streaming & UX (4/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Token streaming | ❌ | — | **Missing**. No intermediate token output | Anthropic API |
| Event callbacks | ⚠️ | Hooks (PreToolUse, PostToolUse) | Hooks exist but **not exposed to user** as progress callbacks | LangGraph |
| Progress bars | ❌ | — | **Missing**. No visual progress | LangChain |
| Partial output rendering | ❌ | — | **Missing**. Cannot show incomplete results | Streaming APIs |
| Intermediate tool results | ⚠️ | Tool output in logs | **Missing: streaming tool results back to user** | LangChain, AutoGen |

**Gap Summary**: Implement streaming event channel (WebSocket or Server-Sent Events) for real-time progress.

---

### 4. Human-in-the-Loop (3/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Approval gates | ❌ | — | **CRITICAL MISSING**. No `/approve` or `waiting_approval` state | All SOTA (Anthropic, CrewAI, AutoGen) |
| Interrupt-resume | ❌ | — | **MISSING**. Cannot pause mid-task for human input | LangGraph suspend |
| Edit-then-continue | ❌ | — | **MISSING**. Cannot modify intermediate output and re-run | LangChain agents |
| Time-bound timeouts | ⚠️ | Route.py backoff | Has exponential backoff but not approval timeout | |

**Gap Summary**: Add task state machine (pending → awaiting_approval → resumed) + approval skill.

---

### 5. Tool Use (7/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Parallel tool calls | ✅ | Codex×4 parallel workers | ✓ | Anthropic |
| Tool result validation | ⚠️ | `pre_task_check.py` | **Partial**. Validates input, not tool output | Anthropic patterns |
| Fallback chains | ✅ | `router.py` (fallback_chain) | ✓ | |
| Tool documentation | ⚠️ | MCP servers have schemas but **no examples in frontmatter** | Anthropic recommends detailed examples | Anthropic tool design |
| Computer-use (vision) | ❌ | — | **Missing**. No screenshot/click automation | Anthropic computer-use |
| MCP quality standard | ⚠️ | 6 MCP plugins exist | **No validation schema for MCP servers** | MCP spec |

**Gap Summary**: Add tool examples to frontmatter. Computer-use requires model upgrade (needs Claude 4.x vision).

---

### 6. Multi-Agent Coordination (5/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Handoff protocols | ⚠️ | Task routing exists | **Missing: explicit agent-to-agent message passing** | CrewAI delegation |
| Message passing | ⚠️ | Task queue (orca.db) | **Queue-based, not actor-model RPC** | AutoGen |
| Shared context | ⚠️ | Task instruction + context_reducer | **Missing: shared knowledge base** accessible by all agents | |
| Conflict resolution | ❌ | — | **Missing**. No voting, consensus, or conflict detection | AutoGen |
| Manager-worker hierarchy | ⚠️ | Orca auto is flat pool | **Missing: explicit hierarchy**. Could add manager role | CrewAI |
| Group chat | ❌ | — | **Missing**. No multi-turn agent dialogue | AutoGen group chat |

**Gap Summary**: Implement message-passing abstraction. Add group chat skill for multi-turn scenarios.

---

### 7. Evaluation (6/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| LLM-as-judge | ✅ | `eval_quality/` plugin | ✓ Basic scoring | Anthropic |
| Golden dataset | ❌ | — | **Missing**. No test fixtures or regression suite | LangChain, LangSmith |
| A/B prompt testing | ❌ | — | **Missing**. No systematic comparison framework | Anthropic recipes |
| Behavioral evaluation | ⚠️ | Failure modes tracked | **Partial**. Tracks failures, not behavioral metrics | LangSmith |
| Iterative refinement | ⚠️ | eval_quality exists | **Missing: feedback loop back to prompt/model choice** | Anthropic agents |

**Gap Summary**: Add golden dataset management. Implement A/B testing framework. Close feedback loop.

---

### 8. Observability (3/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Distributed tracing | ❌ | — | **CRITICAL MISSING**. No trace ID propagation | Langfuse, Phoenix |
| Token-level attribution | ❌ | Metrics in orca.db | **Missing: per-API-call breakdown**. Only aggregate | |
| Anomaly detection | ❌ | — | **Missing**. No cost/latency spikes detected | Langfuse dashboards |
| Cost dashboards | ❌ | CSV export (route.py) | **Missing: real-time visualization** | Anthropic console |
| Latency profiling | ❌ | — | **Missing**. No P50/P95/P99 metrics | |
| Error tracking | ⚠️ | Logs + failure_modes | **Missing: error aggregation & alerts** | |

**Gap Summary**: Integrate Langfuse SDK. Add dashboard for cost/latency/errors.

---

### 9. Safety (8/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Secret scanning | ✅ | `block-tricks.py` hook | ✓ Detects PAT/API keys | CLAUDE.md § 7 |
| Prompt injection defense | ✅ | `block_dangerous_bash.py` | ✓ Detects shell commands | |
| Jailbreak detection | ✅ | `failure-mode.md` (fabrication ban) | ✓ Enforces confidence threshold | |
| Output filtering | ❌ | — | **Missing**. No content policy enforcement | OpenAI moderation API |
| Sandbox isolation | ⚠️ | MCP servers only | **Code execution not isolated** (Codex can run arbitrary Python) | AutoGen Docker |
| Input validation | ✅ | `pre_task_check.py` | ✓ | |

**Gap Summary**: Add output content moderation. Code execution needs container isolation.

---

### 10. Deployment (7/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Worker pools | ✅ | `exec_orca-auto.md` | ✓ Configurable worker count | |
| Graceful shutdown | ✅ | Watchdog + session_guard | ✓ Saves state on exit | |
| 24/7 operation | ✅ | `exec_remote` plugin + VPS | ✓ Remote deployment | |
| Blue-green deployment | ❌ | — | **Missing**. No zero-downtime updates | Kubernetes patterns |
| Autoscaling | ❌ | — | **Missing**. Workers fixed count, not dynamic | Cloud platforms |
| Canary rollouts | ❌ | — | **Missing**. No gradual feature roll | |
| Load balancing | ⚠️ | Queue-based (fair distribution) | **Simple FIFO, not weighted** | |

**Gap Summary**: Implement canary deployment. Add dynamic autoscaling based on queue length.

---

### 11. Developer Experience (8/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Plugin scaffolding | ✅ | `plugins/_template/` | ✓ | |
| Hot reload | ✅ | `sync-plugins.sh` + watch hooks | ✓ | |
| CLAUDE.md discipline | ✅ | `.claude/rules/*` + validation | ✓ 21 rules enforced | |
| Local testing | ⚠️ | Dry-run flags exist | **Missing: test harness** (pytest fixtures for tasks) | |
| Debugger integration | ❌ | — | **Missing**. No VSCode debugger for `.claude/scripts/` | |
| Error messages | ✅ | Detailed failure-mode docs | ✓ | |
| Runnable examples | ✅ | Plugin README.md | ✓ | |

**Gap Summary**: Add pytest fixtures. Create VSCode debugger config.

---

### 12. Documentation (9/10)

| Concept | Status | Our File | Gap | Reference |
|---------|--------|----------|-----|-----------|
| Architecture guide | ✅ | `architecture-patterns.md` (9 patterns) | ✓ | |
| API reference | ⚠️ | plugin.json schema + README | **Missing: auto-gen from frontmatter** | |
| Runnable examples | ✅ | Plugin README.md | ✓ | |
| Decision records (ADRs) | ✅ | CLAUDE.md (explicit decisions) | ✓ | |
| Teaching format | ✅ | `teaching-doc.md` (8-section format) | ✓ Exceeds SOTA | |
| Failure patterns | ✅ | `failure-mode.md` (9 killers) | ✓ Exceeds SOTA | |
| Contributor guide | ⚠️ | `guide.txt` (14 sections) | **Missing: onboarding video or interactive tour** | |

**Gap Summary**: Auto-generate API docs from plugin.json. Add video tutorials.

---

## Top 10 Prioritized Recommendations

**Ranked by Impact × Implement Ease (1 = do first):**

| # | Recommendation | Impact | Ease | Effort | Phase |
|---|---|---|---|---|---|
| 1 | **Human-in-loop approval gates** (`/approve` skill + `waiting_approval` DB state) | HIGH (safety, compliance) | MEDIUM | 1-2 weeks | Phase 1 |
| 2 | **Distributed observability** (Langfuse SDK hook + dashboard) | MEDIUM (visibility, debugging) | MEDIUM | 2-3 weeks | Phase 1 |
| 3 | **Vector semantic search** (`ai_rag_vector` plugin + FAISS/Supabase) | MEDIUM (RAG quality) | EASY | 1 week | Phase 1 |
| 4 | **State time-travel** (SQLite journal snapshots + rewind/redo) | MEDIUM (debugging) | HARD | 4-6 weeks | Phase 2 |
| 5 | **Group chat skill** (multi-agent dialogue, agent routing) | MEDIUM (complex tasks) | HARD | 3-4 weeks | Phase 2 |
| 6 | **Output schema validation** (Pydantic plugin + structured output enforcement) | MEDIUM (reliability) | EASY | 1-2 weeks | Phase 1 |
| 7 | **Batch API optimization** (route.py enhancement for batch calls) | LOW (cost savings) | MEDIUM | 1 week | Phase 2 |
| 8 | **Code execution sandbox** (Docker container for Codex execution) | MEDIUM (safety) | HARD | 4-6 weeks | Phase 2 |
| 9 | **Knowledge summarization on overflow** (context_reducer enhancement) | LOW (token savings) | EASY | 1 week | Phase 1 |
| 10 | **Agent reflection loops** (evaluator-optimizer skill for iterative improvement) | MEDIUM (quality) | MEDIUM | 2-3 weeks | Phase 1 |

---

## Next-3-PR Concrete Roadmap

### PR#1: Human-in-Loop Approval (Phase 1 — Week 1-2)

**Files to add/modify**:
- `plugins/exec_orch/commands/approve.md` — `/approve` command (interactive approval)
- `plugins/exec_orch/skills/approval-gate.md` — Skill to pause task, wait for approval
- `.claude/scripts/lib/state_db.py` — Add `task_state` column (pending/awaiting_approval/resumed/rejected)
- `.claude/scripts/approval-worker.py` — Daemon checking for approval responses
- `docs/approval-workflow.md` — User guide

**Entry point**: `exec_orch` plugin
**Test**: Mock approval delay, verify task pause/resume in orca.db

---

### PR#2: Observability Integration (Phase 1 — Week 2-3)

**Files to add/modify**:
- `.claude/hooks/hook-06-telemetry.py` — Langfuse SDK initialization (new hook)
- `.claude/scripts/lib/telemetry.py` — Trace ID generation, logging wrapper
- `.claude/scripts/route.py` — Add `--telemetry-enable` flag
- `docs/observability-setup.md` — Langfuse account setup, dashboard guide
- `.claude/settings.json` — Add `telemetry_api_key` environment variable

**Entry point**: Hooks system (PreToolUse + PostToolUse)
**Test**: Send traces to Langfuse staging, verify dashboard shows calls

---

### PR#3: Vector Semantic Search (Phase 1 — Week 1)

**Files to add/modify**:
- `plugins/ai_rag_vector/plugin.json` — New plugin (prefix: `ai_rag_`)
- `plugins/ai_rag_vector/commands/index.md` — `/rag-index` (build vector DB)
- `plugins/ai_rag_vector/commands/search.md` — `/rag-search` (semantic search)
- `plugins/ai_rag_vector/skills/retrieval.md` — RAG skill with embedding cache
- `.claude/scripts/lib/vector_store.py` — FAISS or Supabase wrapper
- Update `docs/2026-04-19/로드맵.md` Phase 1 section

**Entry point**: New plugin under `ai_rag` category
**Test**: Index sample docs, verify similarity search returns correct results

---

## Key Metrics to Track (Post-Implementation)

1. **Approval workflow**: % of tasks requiring human approval, approval latency (goal: <5min)
2. **Observability**: % of tasks with complete trace coverage (goal: 100%)
3. **RAG quality**: Retrieval precision@5 (goal: >85% for domain docs)
4. **Safety**: Failed rejections/approvals (goal: 0 false positives)

---

## Conclusion

**orchestration_v1 is ahead of educational tools, at parity with open-source frameworks (LangChain, CrewAI), behind closed-source (OpenAI agents, Anthropic internal).** The gap is **not architectural** (routing, state, plugins are solid) but **operational** (approval gates, observability, semantic search for production use). Implementing PR#1-3 closes the gap for enterprise deployments (compliance, debugging, knowledge systems). PR#4-10 are nice-to-have or research directions.

**Next action**: Start PR#1 (approval gates) this week — it's the blocking prerequisite for Phase 1 roadmap (exec_scheduler, cost_youtube, etc.) which assume approval workflows exist.

---

**Analysis by**: Claude Opus 4.7 (extended thinking)
**Date**: 2026-05-13
**Methodology**: Full codebase + WebFetch global references
**Confidence**: 8.5/10 (based on file inspection + architectural patterns, not runtime execution)
