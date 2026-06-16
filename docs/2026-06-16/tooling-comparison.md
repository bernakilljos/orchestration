# 외부 도구 vs orchestration_v1 비교 (2026-06-16)

> **목적**: 우리 kit 보다 좋은·차별점 있는 외부 도구 식별 + 적용 후보 분류.
> **결론**: 우리 kit 의 self-hosted full source + plugin·rule·hook 체계는 강점. 약점은 (1) subagent 카탈로그 부족 (2) 공식 marketplace 미통합 (3) multi-harness (Cursor·Copilot) 미확장.

## 1. 비교 매트릭스

| 도구 | 강점 | 우리 kit 와 차이 | 통합 후보 |
|---|---|---|---|
| **Perplexity Computer** (SaaS, 2026-02) | 19 모델 자동 라우팅 (Claude/Gemini/Grok/GPT-5.2) | 우리는 self-hosted, 3 모델 (Claude+Codex+Gemini) + Haiku | Grok/GPT-5.2 추가 검토 (⭐⭐) |
| **VoltAgent awesome-claude-code-subagents** (MIT) | 154+ subagents · 10 카테고리 (core dev, lang, infra, security, data/AI, DX, domain, biz, meta, research) | 우리 32 plugins — 카테고리 일부 누락 | reference doc + 선별 vendoring (⭐⭐⭐) |
| **wshobson/agents** (multi-harness) | Claude/Codex/Cursor/OpenCode/Copilot/Gemini CLI 동시 | 우리 = Claude/Codex/Gemini 만 | Cursor/Copilot wrapper (⭐⭐) |
| **Anthropic 공식 Skills** (151k stars) | 16 skill (algorithmic-art, canvas-design, docx/pdf/pptx/xlsx, claude-api, mcp-builder, web-artifacts-builder, webapp-testing, skill-creator 등) | 우리 design_*·claude-api 일부 중복 — 공식이 더 검증됨 | `/anthropic-skill <name>` wrapper (⭐⭐⭐) |
| **LangGraph** | stateful graph orchestration · 멀티 노드 | 우리 task-instruction = linear | exec_graph plugin 별도 (⭐ 복잡도) |
| **OpenAI Agents SDK** | minimal handoff + MCP | 우리 task-instruction 와 유사 | 패턴 차용 (⭐) |
| **Cursor Composer** | 풀 IDE + 자율 step-by-step | 우리 CLI only · Claude Code 활용 | 통합 X (다른 패러다임) |
| **Windsurf Cascade** ($15/m) | SWE-1.5 (13x speed) + Fast Context (10x) | 우리는 모델 단가 직접 관리 | 비교만 |
| **Cline** (VSCode 확장, $0) | API key 만 있으면 무료, 모델 선택 자유 | 우리는 Claude Code 전용 워크플로우 | 통합 X |
| **Aider** (terminal, git-aware) | CLI + clean git history + auto-commit | 우리 commit-push-pr 와 비슷 | 패턴 차용 |

## 2. 우리 kit 의 절대 강점 (외부 도구가 못 함)

- **self-hosted full source** — SaaS 의존 0, 데이터·룰 우리 소유
- **SQLite quota/budget 통합 관리** — route.py + budget/quota/metrics 한 DB
- **post-codex-verify hallucination 차단** — pre/post snapshot + empty commit
- **approval-gate 5 카테고리** — data_loss·security·cost·system·irreversible
- **smoke-test-screen NPE auto-detect** — DB/API/프론트 변경 시 자동 curl·Playwright·console error
- **verify-image-fit, verify-no-mojibake, verify-docx-visual** — 산출물 visual 검증 자동
- **Task Scheduler 자동 등록** (2026-06-16) — claude 세션 안 열어도 OS daily 실행
- **exec_remote VPS 24/7** — Oracle Free Tier 4 OCPU·24GB
- **/effort xhigh/ultracode/mythos** — multi-tier 라우팅 + Fable 5 SUSPEND 대응
- **19 rules + 28 hooks + 115 scripts + 32 plugins** — 통합 관리 (sync-plugins · validate · drift 감지)

## 3. 적용 후보 (우선순위)

### ⭐⭐⭐ 자율 진행 가능
1. **VoltAgent reference doc** — `plugins/exec_orch/references/external-subagents.md` 에 154+ subagent 카탈로그 link + 우리 plugins 매핑
2. **Anthropic Skills wrapper** — `/anthropic-skill <name>` command 신설 (`/plugin install <name>@anthropic-agent-skills` 자동 호출)
3. 이 비교 문서 (`docs/2026-06-16/tooling-comparison.md`)

### ⭐⭐ 사용자 결정 (큰 변경)
4. **Grok / GPT-5.2 라우팅 추가** — `route_dispatch.md` 매트릭스 확장 (Perplexity Computer 패턴). API key·비용·정책 영향
5. **Cursor / Copilot CLI multi-harness 확장** — wshobson 패턴. 별도 plugin `exec_harness_cursor`·`exec_harness_copilot` 신설
6. **VoltAgent 154+ subagent 선별 vendoring** — 우리 plugins/ 부족 카테고리 (security audit·infra automation·domain specialist) 만 선별 vendoring

### ⭐ 보류 (복잡도)
7. **LangGraph stateful graph orchestration** — 별도 plugin `exec_graph`. 우리 linear task-instruction 패러다임과 다름. 큰 작업.

## 4. 우리 kit 가 흉내 낼 수 없는 외부 도구 (의도적 제외)

- **Cursor Composer / Windsurf Cascade** — 풀 IDE + GUI. 우리는 CLI only 패러다임 (Claude Code 의 확장).
- **Cline** — VSCode 확장. 우리 Claude Code 워크플로우와 다름.

## 5. 결론

| 영역 | 결정 |
|---|---|
| 우리 강점 (self-hosted, plugin/rule/hook 체계, SQLite 통합) | **유지** |
| 자율 적용 (reference doc, wrapper command, 비교 doc) | **이번 commit** |
| 사용자 결정 후보 (Grok/GPT-5.2, multi-harness, VoltAgent vendoring, LangGraph) | **사용자 보고** |

## 참조

- [Perplexity Computer](https://www.langchain.com/resources/ai-agent-frameworks) (Feb 2026 launch)
- [VoltAgent awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) (MIT, 154+ subagents)
- [wshobson/agents multi-harness](https://github.com/wshobson/agents)
- [anthropics/skills 공식](https://github.com/anthropics/skills) (151k stars, 16 skills)
- [LangGraph](https://www.langchain.com/langgraph)
- [Cursor vs Windsurf vs Cline 2026 비교](https://memstate.ai/blog/cursor-vs-windsurf-vs-cline-vs-kilo-code-2026)
