# CLAUDE.md — Multi-AI Orchestration Kit v1

> **목적**: Claude Code 가 이 프로젝트에서 **어떻게 일해야 하는지** 정의.
> **대상**: AI 에이전트 (Claude 우선). 사람용 가이드는 `guide.txt`.
> **유지 원칙**: 500줄 이하 · WHAT/WHY/HOW 프레임 · 참조 중심 (내용 중복 금지).

---

## 1. WHAT — 이 프로젝트는 무엇인가

**멀티AI 오케스트레이션 킷** (Claude + Codex + Gemini).
- **핵심**: `exec_orch` 엔진 + 26개 플러그인 (16 stable + 10 spec-only, `_template` 제외)
- **경계**: 이 저장소 = **킷**. 실구현·비즈니스 로직은 **install 후 각 플랫폼**에서.
- 전체 플러그인 목록: `docs/2026-04-19/플러그인.txt`
- 로드맵 (미래 26개): `docs/2026-04-19/로드맵.md`
- 최신 추가: `exec_remote` (4주차 VPS 24/7 원격 운영, 2026-05-07)

---

<!-- AUTO-STATS -->
> **현재 상태** (2026-09-02): plugins 36 stable + 0 spec-only · rules 30 · hooks 31 · scripts 118
<!-- AUTO-STATS -->

## 2. WHY — 왜 이 구조인가

- **다AI 협업**: 단일 모델 한계 극복 (Claude 설계 → Codex 구현 → Gemini 검증)
- **SoT 규칙**: `plugins/` 원본 → `.claude/` sync 결과물 (드리프트 방지)
- **스코프 분리**: 킷은 인프라만, 응용은 플랫폼에서 (스코프 폭주 방지)
- **비용 관측**: plugin.json `precedence` + `token_estimate` (세션 로드 우선순위)

상세 원칙: `docs/architecture-patterns.md` (9개 패턴)

---

## 3. HOW — 어떻게 작업하는가

### 3.0 대상 확정 0순위 (매 사용자 지시)
사용자가 작업·감사·수정 지시 시 **첫 응답 첫 줄에 대상 명시** → 유지·정정 확인 → 실행. 대상 확정 전 grep·Read·Edit·Bash 착수 = 룰 위반.

**형식**: `대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정`

**4갈래 후보**:
1. `C:\pjt\orchestration_v1\` — kit 자체 감사·룰·hook 축약
2. `C:\pjt\orchestration_v1\setup\templates\` (+ `setup/modules/`) — install 배포용 template
3. install 대상 실운영 프로젝트 (경로 확인 필요) — "실운영"·"하드코딩 실측"·"재발 방지 헌장"·비즈니스 지표
4. `~/.claude/` — 글로벌 설정

**강제**: `.claude/statusline.sh` (매 turn 표시) + `.claude/hooks/user-prompt-auto-planner.sh` (매 지시 systemMessage 주입) + `plugins/exec_orch/hooks/hook-00-init.sh` (SessionStart 노출).

상세: `.claude/rules/direction-first.md` · `feedback_confirm_target_first.md`.

### 3.1 Session Start (순서 고정)
1. **Orca Auto** — `.claude/skills/exec_orca-auto.md` 실행 (워커 spawn)
2. **First-Run** — `docs/CLAUDE_SETUP_GUIDE.md` 있으면 처리 후 삭제
3. **Resume** — `.claude/context-cache/session-snapshot.md` 있으면 복구 제안
4. **신규 changelog 알림 확인 (필수)** — `.claude/state/changelog-new.md` 있으면 **첫 응답 전 반드시 Read** → `feedback_official_features_auto_check.md` 매트릭스로 평가 (⭐⭐ 이상 자율 반영, ⭐ 이하 보고) → 처리 후 파일 삭제. Hook 가 만들어둔 알림을 안 읽는 것 = `feedback_official_features_auto_check.md` 위반
5. **세션 히스토리 자동 로드 (2026-09-02 신설)** — `.claude/hooks/load-recent-conversations.sh` 가 `orca.db.session_summary` 최근 3 세션 요약을 systemMessage 로 주입 → 새 세션이 이전 문맥 자동 인지 · UserPromptSubmit·Stop·SessionEnd 는 대화·요약을 `conversations` / `session_summary` 자동 저장. 상세: `.claude/rules/conversation-history.md`

### 3.2 AI 역할 (규모·특성 기반, **Opus 5 신규 default 2026-07-24** · Opus 4.8 병존 · Fable 5 초난도 · Sonnet 5 균형)
| 태스크 | AI | 방법 |
|--------|-----|------|
| **설계·복잡추론 (default)** | **Claude Opus 5 [NEW 2026-07-24]** | `claude-opus-5` · **1M context 기본+최대** · 128k 출력 · thinking on-by-default · effort ladder (low/medium/high/xhigh/max) · **breaking**: `thinking:{"type":"disabled"}` + effort `xhigh`/`max` = 400 error (4.8 는 허용) · $5/$25 (4.8 동일) |
| 설계·복잡추론 (호환/저비용 fallback) | Claude Opus 4.8 | Extended Thinking + `/effort xhigh` · 1M context 800k 제한 · thinking disable 자유 (Opus 5 호환 안 되는 코드에서 fallback) |
| 초난도·다각 검증 | Claude Opus 5 + ultracode | `/effort ultracode` → Dynamic Workflows (기본 medium ≤15 agents, `workflowSizeGuideline` settings 로 조정) · **sub-agent 가 sub-agent spawn depth 3 default** (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` 로 nesting 비활성) · v2.1.206+ findings quality 개선 |
| **Mythos-class (Opus 가 fail / long-running / vision-heavy)** | **Claude Fable 5 [RESTORED 2026-07-01]** | 2026-06-12 US export-control 로 suspend 되었다가 2026-07-01 Anthropic 이 restored (공식 statement). `/effort mythos` 호출 시 정상 라우팅. route.py `SUSPEND_MODELS = set()`. 30일 data retention 요구. **참고: Anthropic 내부 `Model 2` (Mythos 5 초과, 2026-08-14 RSP disclosed) 외부 release X — 승격 대상 아님** |
| 로컬·오픈웨이트 (오프라인 대량·edge) | **Qwen 3.8-27B [NEW 2026-08-14]** / Llama 4 / Llama 3.3 | `/exec_offline-model` (Ollama). **Qwen 3.8-27B**: Apache 2.0 · 27.78B params · **262K context** · 멀티모달(text/image/video) · SWE-bench Pro **61.7%** (Claude Opus 4.6 Max 53.4%) · Alibaba 자체 평가. 로컬 우선 라우팅 매트릭스에서 코드·추론 top 후보. Llama 4 는 10M context 강점 (초장기 컨텍스트 로컬 recall) |
| 균형형 (Sonnet 대체·차세대) | Claude Sonnet 5 | 2026-07-02 출시 · Opus 4.7 tokenizer 사용 (텍스트당 ~30% 더 많은 토큰) · harness reminder mid-conversation 제거 (v2.1.201) · 마이그레이션은 [Prompting Claude Sonnet 5](https://docs.claude.com/) 참고 |
| 단순구현 <200줄 | Claude Sonnet 4.6 | 직접 (저비용, Sonnet 5 로 승격 검토 중 — 토큰 30%↑ 비용 재산정 필요) |
| 코드 500줄+ | Codex (×4 병렬) | `task-instruction.md` → `codex-auto` |
| 검증 (기본) | Haiku 4.5 (×2 병렬) | `haiku-auto` (Prompt caching 90% 절감) |
| 검증 (초장문/멀티모달) | Gemini Flash | >500k 토큰만 `gemini-auto` |
| 가벼운·빠른 응답 (대량) | Grok | `route.py --check grok` (Perplexity Computer 패턴, API key 필요 시만 활성) |
| 초장기 컨텍스트 recall (2M+) | GPT-5.2 | `route.py --check gpt-5.2` (Perplexity Computer 패턴, API key 필요 시만 활성) |
| 보안 패턴 검사 | security-guidance plugin | Anthropic 공식 `/plugin install security-guidance@claude-plugins-official` — Write/Edit/MultiEdit pre-hook, 모델 호출 0회 |
| 데이터 시각화·차트·대시보드 | `/dataviz` (v2.1.198 내장) | color-palette validator 포함 · 우리 arch-*/chart 스킬과 병존 (built-in 우선) |
| PPT·디자인 | Claude + MCP | Gamma/Canva/Figma |

**가격** (2026-07-24 기준):
- **Opus 5** (신규 default): $5/$25 per MTok · `claude-opus-5` · 1M context 기본+최대 · 128k 출력 · thinking on-by-default · Claude API·Bedrock·Vertex·Foundry 모두 GA
- **Opus 4.8** (호환 fallback): $5/$25 per MTok · Fast $10/$50 (2.5× 속도) · Opus 5 breaking (thinking disable) 안 되는 코드에서 fallback
- **Opus 4.7**: **fast mode 제거 (2026-07-24 breaking)** — fast 는 4.8 또는 Opus 5 로 마이그레이션. Opus 4.7 표준 속도만 유지
- **Fable 5** (Mythos-class, 2026-07-01 RESTORED): $10/$50 per MTok · 128k 출력 · `claude-fable-5` · 30-day data retention 요구
- **Sonnet 5** (2026-07-02): 새 tokenizer (Opus 4.7 계열) → 텍스트당 ~30% 토큰 증가. **가격 $2/$10 per MTok 확정 (2026-08-10)** — 원래 9/1 예정된 $3/$15 인상 취소.

**Claude Code v2.1.241** (2026-08-25 기준 최신):
- **2.1.241 · 2.1.240 (8/24, 8/23)**: Bug fixes and reliability improvements
- **2.1.239 (8/22 · BIG RELEASE)**: **`ANTHROPIC_DEFAULT_MODEL` env var** (신 세션 시작 모델 지정) · **Fullscreen renderer** Bedrock/Vertex/Foundry 확장 · **`/claude-api upgrade`** (anthropic Python 0.x→1.x 마이그레이션 command) · **Cloud sessions synced plugins** (`name@synced` 표시 · enable/disable 지원) · **Alpine/musl** native image paste·clipboard·audio-capture · **Usage-limit reset 표시** (세션·주간) · **Bedrock streaming Content-Type strip fix** (silent doubled billing 방지 — 우리 budget 룰 정합) · **`awsAuthRefresh`** HTTPS proxy + Bedrock SSO hang fix · **Edit/Write JetBrains IDE 5초 pause fix** · **WebFetch 15-min cache respect** (expired page content 재사용 fix) · **`/resume` cross-directory + all-projects fix** (deleted directory 처리) · **`.worktreeinclude` `**/` fix** · **UTF-8 BOM agents/skills/commands 무시 fix** (우리 no-mojibake 룰 정합) · **Vim mode Escape NORMAL + text 보존** · **OpenTelemetry trace fragmentation** (deferred tool executions) fix · **Persistent retry mode**: spend-limit + out-of-credits 즉시 fail (기존 재시도 X · 우리 budget 시스템 정합) · **Claude in Chrome**: `/clear` = 세션 Chrome tab group 닫기 · **Windows cross-session messaging** (`SendMessage` cross-session Windows 지원 · 우리 다중 세션 격리 룰 정합) · **`ListAgents` live teammates + 자기 이름 반환** · **`keybindingFlavor: "readline"` Bash 매치** · Remote sessions mobile-uploaded images path 포함 · VSCode "View usage" inline · `/goal` 재개 시 active goal 복원 · `/insights` `<message>` 태그 echo fix · `claudeMdExcludes` symlink 처리 fix
- **2.1.238 (8/22)**: **`keybindingFlavor` 설정** — `"readline"` 로 Bash-style Ctrl+W (word delete) · Alt+F · Option+→ · **Plugin marketplace `headersHelper`** (HTTP 헤더 dynamic 생성 · install/update 시 user confirmation · 우리 MCP OAuth 룰 확장) · **`claude self-hosted-runner --defer-shutdown-max-min`** (graceful shutdown) · Proxy authorization command (egress proxy 헤더 refresh) · 장기 세션 unbounded memory growth fix (subagent 결과 release) · Custom output styles 대화 중 default 복귀 fix · Worktree isolation 강화
- **2.1.237 (8/21)**: **Built-in "Concise" output style** — 결과 먼저 답 · preamble skip (우리 사용자 짧은 응답 선호 정합 — statusline·hook 로 자동 활성 가능) · **LLM gateway/custom base URL 세션 prompt caching fix**
- **2.1.236 (8/20)**: **`ANTHROPIC_DEFAULT_MODEL` env var** (첫 등장) · **Cross-session `SendMessage` + `notify_when_idle`** (다른 세션 idle 시 1회 notice — 우리 orca 워커 idle 감지 정합) · Sandbox macOS wildcard read-deny 규칙이 allowed read region 안에서 우선 · 디렉토리 제거 후 clipboard·background sessions 깨짐 fix · Fullscreen renderer 단일 실패 후 영구 실패 fix · `/model` picker terminal 초과 시 스크롤 · Malformed 닫는 태그로 인한 `SendMessage` reject fix
- **2.1.235 (8/18)**: **Inline spellcheck** — 옵션형 `spellcheck` 설정 · aspell/hunspell/ispell 사용 · 오타 실시간 underline · **Prompt-cache invalidation fix** (LSP disconnect/reconnect 중 whole-prompt-cache 무효화 방지) · Markdown nested list depth 3+ 정렬 fix + wrapped list hanging indent · Vim mode transcript toggle (Ctrl+O) NORMAL mode + cursor 보존 · `SendMessage` oversized 메시지 upfront reject (silent drop X) · Remote Control (`claude rc`) enterprise-gateway 가용성 체크 · context-limit 에러 메시지 auto-compact off 여부 표시 · Shift+Tab permission comment 안 동작 fix · Agent tool 미가용 agent 에러 처리 fix
- **2.1.234 (8/17)**: **Session auto-continuation** (usage limits reset 시 자동 재개, `/config` 로 disable) · **GitLab MR support** — footer/statusline MR badge, agents view `!N` notation · `CLAUDE_CODE_PROJECT_DIR_NAME` (per-project transcript dir 이름) · **Security: Windows NT-namespace (`\??\`) 경로 거부** (remote file read·session restore·CLAUDE.md include·workflows·file upload — NTLM credential-leak 방어) · session-scoped permission 답변이 background subagent prompt 중 drop 안 됨
- **2.1.233 (8/14)**: **GitLab worktree flag + agents view** (`!N` merge request URL) · **Linux cgroup memory limit** (`CLAUDE_CODE_TOOL_MEMORY_LIMIT` — 런어웨이 빌드 방지) · MCP v2 endless stream reopening fix · **BREAKING: Todo/task tools 제거 from Opus 4.8+ · Sonnet 5+ · Fable 5+ · Mythos 5+** — 우리 kit `TaskCreate/Get/Update/List`·`TodoWrite` 사용 다수. 복원: `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` env
- **2.1.232 (8/13)**: **Subagent forking default** — `subagent_type: "fork"` = 전체 대화+prompt cache 상속, 비-teammate agent 는 background · **`@` cross-session mention** — prompt 에 `@name` 으로 다른 세션 호출, `SendMessage` 로 direct · session 이름 unique 유지 (dup 시 `name-word-word` 변형) · **subagent nesting depth 3+ default** (이전 depth 1) · Security: PowerShell variable-write parameter bypass 폐쇄, Git Bash symlink-following permission bypass fix
- **2.1.231 (8/13)**: MCP OAuth sign-in redirect URI mismatch fix (pre-registered OAuth clients, Slack 등)
- **2.1.229 (8/12)**: **Server-supplied hooks for self-hosted runner** · SSE keepalive pings (Vertex/Bedrock long thinking idle-timeout 방지) · plugin marketplace `command` source type · `ListAgents` 에 Remote Control offline / cloud session 표시
- **2.1.225 (8/8)**: **Spend limit** UI (reset time + operator message 표시) · `claude agents` workspace trust prompt (untrusted dir) · Remote Control 사진 direct 표시 · **BREAKING: `SendMessage` — Remote Control 세션 대화 시작 시 name 사용**
- **2.1.224 (8/7)**: **Self-hosted runner** — `claude self-hosted-runner` (Team/Enterprise 자체 머신 세션) · **Archive plugin source** — HTTPS zip install + optional SHA-256 pinning · macOS/Linux `SendMessage` + `ListAgents` cross-session · sandbox credential masking (`extract`·`decode: "jwt"`·`awsPairs`·`sigv4` — `network.tlsTerminate` 필요) · **BREAKING: 긴 project path 세션 dir 분리** + `strictKnownMarketplaces` SCP validation 강화
- **2.1.223 (8/6)**: Marketplace wildcard (`"owner/*"` in `strictKnownMarketplaces`/`blockedMarketplaces`) · Workflow/forked skill/command restricted model warning · **BREAKING: permission mode `bypass` 가 org disable policy 존중** (우리 kit `bypassPermissions` 강제 영향 가능 — org 정책 확인 필요) · workflow dynamic `import()` sandboxed
- **2.1.222 (8/4)**: **Worktree isolation 강화** — isolated session 은 main checkout 대상 destructive git 실행 불가 · **BREAKING: `/review` = `/code-review` alias** · Background session commit/push (작업 보존) · PreToolUse auto-allow hook 이 background task tool restriction bypass 못함
- **2.1.221 (8/4)**: **VSCode Focus view** (`Ctrl+Alt+F` — tool activity 접기) · Linux/WSL sandbox credential file masking (`mode: "mask"` — sentinel copy 읽기, egress 시 실제 값 치환) · Bash permission check zsh `[[ ]]` regex 조건 hidden command 감지 강화
- **2.1.219~226 (7/24~28)**: Opus 5 launch + default 승격, subagent nesting depth 3 default, Opus 4.7 fast mode 제거, `sandbox.network.strictAllowlist`, dangerous-rm shell 캡, sandbox 명령 restriction
- **2.1.207~218 (7/9~22)**: screen reader mode, `/fork` vs `/subtask`, WebSearch/subagent 200 상한, `sandbox.filesystem.disabled`, `/verify` `/code-review` 자동 실행 중단, Windows PS 5.1 permission fix, MCP tool output 누수 fix
- **2.1.198~206 (요약)**: Fable 5 RESTORED, subagent 기본 background, Explore agent opus 상속, Dynamic workflow size, `.claude/rules/` symlink 로딩 fix
- 상세: [[claude-code-changelog-august]] (memory) · Anthropic 공식 changelog

**API 신규 (2026-07-08 이후)**:
- **8/18: Workbench → Playground** — Claude Console UI 개편 (`platform.claude.com/playground`). 모든 Messages API parameter 지원 + code execution·web search 데모 템플릿 + full SDK request/response 표시. legacy Workbench 는 8/17 sunset (예정대로 완료)
- **8/14: Anthropic Risk Report v2 (RSP v3.4)** — catastrophic-misalignment `very low → low` 상향 (cybersecurity eval 불확실성 근거) · **`Model 2` 내부 프론티어 disclosed** — Mythos 5 초과 성능 · 외부 release 계획 X · Mythos 5 대비 새/추가 misalignment 프로파일 X · 커버 기간 2026-02-24 ~ 07-15
- **8/7: Managed Agents 관리 컨트롤 4종** — ① **Session budgets** (hard cap, `budget_reached` stop_reason, list-rate pricing — 우리 route.py budget 시스템 정합) · ② **Advisor tool** (`{"type":"advisor"}` in multiagent roster — mid-turn 다른 모델 상담, 우리 Claude 설계→Codex 구현→Gemini 검증 협업과 유사) · ③ **Inference geo pinning** (`model.inference_geo` — data residency) · ④ **GitHub-hosted skills** (repo mount 시 `.claude/skills` 자동 discovery — install 워크플로우 정합)
- **8/5: Inference hooks (Enterprise beta)** — 조직 AI security server 로 각 prompt hold + allow/deny 판정 · claude.ai·Cowork·Claude Code 통합 · 요청 signed·failure handling 구성 가능·denial 은 Compliance Activity Feed 기록 · **우리 approval-gate-rules.md 정합** (kit 는 SQLite 로컬, 이건 조직 서버) · Claude Opus 4.1 retired (같은 날)
- **8/11: Compliance API — 로컬 Cowork/Claude Code 세션 지원** (Enterprise beta) — `GET /v1/compliance/apps/sessions/local[/{id}[/messages]]`. `read:compliance_user_data` scope. 사용자 머신에서 돌아간 세션 감사 가능
- **8/11: `anthropic-workspace-id` response header** — `wrkspc_` prefix 로 요청 workspace 식별 (Default Workspace 포함)
- **8/10: Sonnet 5 가격 확정 $2/$10 per MTok** — 원래 9/1 예정된 $3/$15 인상 취소. Sonnet 5 승격 재검토 트리거 (Sonnet 4.6 대비 tokenizer 30%↑ 이지만 단가 $2/$10 = 실비용 비교 필요)
- **7/24: Claude Opus 5 launched** — `claude-opus-5`, $5/$25 (4.8 동일), 1M context 기본+최대, 128k 출력, thinking on-by-default. Effort 가 primary control (low/medium/high/xhigh/max). Claude API·Bedrock·Vertex·Foundry 모두 GA. **Breaking**: `thinking:{"type":"disabled"}` + effort `xhigh`/`max` → 400 error (4.8 는 fallback 됐음). Opus 4.7 fast mode 제거 (400 error) — fast 는 4.8 또는 Opus 5 로 마이그레이션
- **7/24 beta 3종**: mid-conversation tool changes · server-side fallback · MCP tool 100k+ auto-spill (sandbox 파일 저장 + preview)
- **7/22 Managed Agents 3종**: session thread event streams · webhooks (`environment.*`·`memory_store.*`) · effort 지정
- **7/8~17**: legacy Workbench 2026-08-17 종료 · mid-conversation system messages (beta header 없이) · Enterprise Admin API user management · Dreams (Fable 5/Sonnet 5) · API key expiration · `agent-memory-2026-07-22` beta header

Fable 5 활용 전략·승격 트리거·예산 게이트 상세: `~/.claude/projects/C--pjt-orchestration-v1/memory/project_fable_5_usage_strategy.md`

라우팅 로직: `plugins/exec_orch/skills/route_dispatch.md` (AI 단가·특성·quota 매트릭스)
프롬프트 강화 (12 기법): `plugins/exec_orch/skills/prompt-techniques.md` + template `plugins/exec_orch/codex/task-instruction-template.md` (Role·Negative·Context·Few-shot·CoT·Prompt-chain·Meta·Self-consistency·ToT·ReAct·Zero-shot-CoT·RAG)

### 3.3 API 한도 + Budget Fallback
SQLite 기반 quota·budget 관리 → 자동 fallback + 지수 backoff.
- 감지: `.claude/state/orca.db` (quota·budget 테이블)
- Quota 초과: 10m→20m→40m→2h 지수 backoff
- Budget 초과: 일일 상한 (기본 무제한, `route.py --set-daily-limit` 설정 가능)
- **절대 금지**: 빈 task 를 `done/` 으로 이동 (위장 완료)

**Agent SDK / `claude -p` billing 변화 (2026-06-15 → PAUSED)**:
- 2026-06-15 예정이었던 dollar credit 전환이 Anthropic 에 의해 **일시 보류** (digitalapplied 보도 6/17+)
- 현재 (2026-06-19): 기존 "unlimited" subsidy 유지 — programmatic 루프 (codex-auto·gemini-auto·haiku-auto·vibe-loop) 가 interactive 가격으로 동작
- 재개 일정 미정. route.py `--check` 의 SDK credit 게이트는 코드만 준비, 실제 활성화는 Anthropic 공지 후

### 3.4 Orca Auto 규칙
- 활성: `.claude/orca-enabled` 있고 `.claude/orca-stopped` 없음
- 로컬 워커 수: `.claude/orca-workers-config.json`
- 전역 상한: `~/.claude/orca/workers-config.json` `max_workers`
- 종료: `/orcauto-stop` 또는 Claude 종료 후 5분

상세: `.claude/skills/exec_orca-auto.md`

### 3.5 전역 오케스트레이션 (멀티 프로젝트)
- 진입: `orca-dispatch <task_file> [codex|gemini|claude]`
- 워커: `codex-auto-global`, `gemini-auto-global` (`~/.claude/orca/` 폴링)
- 중단: `touch ~/.claude/orca/stop`

상세: `plugins/exec_orch/skills/route_dispatch.md § Step 4`

### 3.6 MCP 설치 규칙
1. **실제 npm 존재 확인**: `npm view <package>` 로 검증 후만 커맨드에 기록 (404 방지)
2. **Windows npx 래퍼**: `cmd /c npx <package>` 필수 (shell 교차호환성)
3. **OAuth/인증도구**: 실제 값은 환경변수만, 개발자 콘솔 URL + 변수 이름 명시
4. **각 plug_<category> 준수**: design·dev·data·web·collab·docs·media 모두 위 규칙 따름
5. **통합 MCP (2026-09 채택)**:
   - **Headroom** (Apache 2.0 · 10k+ ⭐ · `pip install "headroom-ai[all]"` + `headroom mcp install`) — 프롬프트 압축 프록시 60~95% 절감 · MCP 도구 `headroom_compress`·`retrieve`·`stats` · 프록시 127.0.0.1:8787 · `ANTHROPIC_BASE_URL` 세팅 시 최대 효과
   - **claude-mem** (오픈소스 · `npx -y claude-mem install --provider claude`) — 자동 세션 관측·복원 · SessionStart / UserPromptSubmit / PostToolUse / Stop / SessionEnd 5 hook 자동 등록 · SQLite + Chroma 저장 (`~/.claude-mem`) · Worker 127.0.0.1:37777 · Cloud sync OFF (local)
   - **task-observer** (오픈소스 Skill · `npx -y skills add rebelytics/one-skill-to-rule-them-all --skill task-observer --agent claude-code`) — 태스크 실행 관측 · 패턴·사용자 수정·재사용 스킬 기회 캡처 · `.claude/skills/task-observer/` · description matching 자동 활성 · 우리 orca.db 관측과 병행 (skill 개선 축)
   - **자동 시작**: `.claude/scripts/mcp-autostart.sh` (SessionStart hook · Headroom proxy + claude-mem worker 백그라운드 spawn · 이미 돌면 skip)
   - **역할 분리**: 우리 `route.py`·`orca.db`·명시 memory 유지 · Headroom·claude-mem 은 병행 (라우팅·룰·도메인은 우리 kit · 압축·자동 관측은 오픈소스)
   - 상세: `.claude/rules/mcp-integration.md`

상세: `guide.txt` § 8 · `docs/upgrade-notes-2026-04-23.md`

### 3.7 24/7 자동화 필수 설정
1. **SQLite 초기화**: `python .claude/scripts/init-state-db.py` (`.claude/state/orca.db` 생성)
2. **Watchdog 백그라운드**: `.claude/scripts/watchdog-start.bat` (워커 heartbeat 체크)
3. **예산 상한** (선택): `python .claude/scripts/route.py --set-daily-limit 50` (USD)

상세: `guide.txt` § 7 · `docs/routing-policy.md` · `docs/caching-strategy.md` · `docs/metrics-guide.md`

---

## 4. 핵심 경로 (참조 전용 — 내용은 해당 파일에)

| 경로 | 용도 | 편집 |
|------|------|------|
| `plugins/` | **원본** (14 stable + 7 spec-only + `_template`) | ✅ 여기만 |
| `.claude/commands,skills/` | sync 결과물 | ❌ 자동 생성 |
| `.claude/rules/` | 공유 규칙 (plugin-structure·frontmatter·file-naming·sync·indentation) | ✅ |
| `.claude/scripts/` | sync·validate·install·orca-status·worker-health·route·watchdog·metrics 등 | ✅ |
| `.claude/scripts/lib/` | state_db·router·pricing·prompt_cache·watchdog_helpers (10개) | ✅ |
| `.claude/hooks/` | PreToolUse·PostToolUse·SessionEnd 훅 스크립트 | ✅ |
| `.claude/state/orca.db` | **SQLite 통합 상태** (workers·tasks·metrics·quota·budget·session) | 자동 |
| `.claude/tasks/` | task-instruction.md, locks/, done/ | 자동 |
| `~/.claude/orca/` | **전역 큐** (멀티 프로젝트) | 자동 |
| `.claude-plugin/` | plugin.json + schema + marketplace.json | ✅ |
| `docs/architecture-patterns.md` | 설계 원칙 9가지 | ✅ |
| `docs/caching-strategy.md` | Prompt caching TTL 전략 | ✅ |
| `docs/routing-policy.md` | 4.8 라우팅 결정 트리 상세 | ✅ |
| `docs/metrics-guide.md` | Metrics DB 스키마·쿼리 | ✅ |
| `docs/2026-04-19/로드맵.md` | Phase 1~3 스펙 (미래 26개) | ✅ |
| `guide.txt` | 사람용 전체 가이드 (섹션 1~14) | ✅ |
| `.env` / `.env.example` | 환경변수 (하드코딩 금지) | .env 는 gitignore |
| `.vscode/settings.json` | VS Code 워크스페이스 최적화 (file watcher exclude·인터프리터 동적 지정·메모리 절감) | 자동 (setup/templates + SessionStart hook 가 idempotent 배포) |
| `setup/templates/vscode-settings.template.json` | 머신 독립 template (`__PYTHON_PATH__` placeholder) | ✅ |

---

## 5. 5 Rules (Brij Kishore Pandey, 2026)

이 CLAUDE.md 가 **실제로 작동하려면**:

1. **`/init` 먼저** — 새 환경 세팅 시 `bash .claude/scripts/install.sh` (scaffold 검증·sync·env 초기화)
2. **500줄 이하 유지** — 길면 무시됨. 세부는 참조 파일로 분리.
3. **Hooks 사용** — 자동 실행 필요한 건 메모리·프롬프트 X, `.claude/settings.json hooks` ✓
4. **월간 업데이트** — 구조 변경 시 이 파일도 갱신. 고정 문서 아님.
5. **참조만, 중복 금지** — `guide.txt`, `docs/architecture-patterns.md`, `.claude/rules/*` 에 있는 건 여기서 반복 X

---

## 6. 3 Scopes (우선순위: Folder > Project > Global, Last wins)

- **Global**: `~/.claude/CLAUDE.md` — 모든 프로젝트 공통 (코딩 스타일·개인 선호)
- **Project**: 이 파일 (`./CLAUDE.md`) — 프로젝트 규칙
- **Folder**: `./src/CLAUDE.md` 등 — 모듈 국소 규칙 (필요 시)

같은 규칙 충돌 시 **Folder가 이긴다**.

---

## 7. 재발 방지 헌장 (A / B / C / D / E / F)

> **원칙**: 재발 방지 조항을 6 카테고리로 통합. 각 조항 = 1줄 규칙 + 근거·상세. 상세는 `.claude/rules/*.md`.

### A. 하드코딩·폴백 금지
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| A1 | API 키·경로·시크릿·사용자명·OS 절대경로·Python 버전 하드코딩 X — `.env` + 런타임 동적 검색 (`where`/`tempfile`/`%USERPROFILE%`). Task Scheduler 는 wrapper 거쳐 동적화 | 배포 대상 머신 다양 · `best-practices.md § 하드 경로` |
| A2 | 산식 없는 %·등급·상수 값 화면 표시 X — 파이프 없으면 "미측정/집계 전/기록 없음" 정직 표기 | 폴백 값 (confidence=0.5) 이 평균 오염 사례 |
| A3 | 표시만 있고 배선 없는 설정·기능 X — 이미 있으면 잠금+미배선 명시 | `bridge_llm_model` 소비자 0곳 "1.0 상속" 거짓 hint 사례 |
| A4 | 임계·색·규격 값은 정본 1곳 (토큰·`ui_constants`·SPEC 블록) — 화면에서 직접 `if p>=50` X | `bar_tone` docstring 금지 예시와 글자까지 같은 우회 재발 사례 |
| A5 | 새 지표·저장소·검색 만들기 전 기존 자산 (RAG·벡터·mem0·evaluation_history·ocr_history) 재사용 실측 우선 | 개선규칙 확신도가 기존 이력 안 타고 자체 상수 사례 |

### B. 검증 원칙
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| B1 | 검사 0건 = 통과 X — 표본 하한 (expected × 0.8) 필수 | 빈 입력·404·로그인 누락 오판 |
| B2 | 화면 스크래핑 스크립트는 `scan_common` 헬퍼 경유 (응답코드·로그인·표본 검증 내장) — 임시 스크립트도 예외 X | |
| B3 | 가시성 사양 (테두리·구분선) computed 통과 X — 캡처+픽셀, 안쪽·바깥 대비 둘 다 + 육안 | 팝업 테두리 4차례 재개정 · (가)안 수치 통과·육안 실패 |
| B4 | 검사기 신설 시 위반 주입 역검증 필수 · 사양 문서 파싱 (SELECTSPEC·AXISSPEC·AGGRIDSPEC·POPUP 25속성) — 코드에 숫자 하드코딩 X | |
| B5 | 판정 (yn) 영향 변경 = 표본 20건 전후 회귀 (변동 0 통과) · 소급 매핑·재생성 X (봉인 불변) | |
| B6 | 수정·빌드 후 자동 검증 후 보고 — "수정했습니다"만 X · FAIL max 3 재시도 후 보고 | PNG=verify-image-fit · docx=verify-docx-structure · pptx=verify-ppt-overflow · `best-practices.md § 검증 후 보고` |
| B7 | 화면·기능 검증 사용자 떠넘김 X (Smoke Test 의무) — SQL→endpoint curl · controller→null·NPE 검사 · 프론트→Playwright + console.error | `screen-verify.md` · `smoke-test-screen.sh` |
| B8 | 산출물 페이지 fit 사전검증 (docx · pptx · pdf) — PIL 로 PNG 비율 측정 → 페이지 비율 (docx 1.46/0.69, pptx 0.54/0.71, pdf 1.41/0.71) 과 fit | `teaching-doc.md § 페이지 fit` · `verify-image-fit.py` + hook-09 |
| B9 | 페이지 전체 콘텐츠 fit — H1+callout+이미지+표 모든 요소 height 합산 (PageLayoutTracker 의무) | 빈 여백·짤림·글씨 작음 = 같은 문제 · `auto-layout-fit` skill |
| B10 | docx 구조 검증 (빈 paragraph 5+ 연속·중복 page_break) — `verify-docx-structure.py` hook-09 자동 | |
| B11 | 거짓 PASS 보고 X (False-Report 차단) — agent PASS 만으로 사용자 전달 X · 이중 검증 (raw Read + mojibake 6 카테고리 grep + 백업 폴더 `.bak`/`_backup`/`_v2`) | `no-false-report.md` · `verify-no-mojibake.py` |

### C. 운영 안전
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| C1 | 운영 동작 변경 (.env·라우팅·판정 로직·닷넷 계약·기동 스크립트) 적용 전 판정 (네트워크 무관) | `OCR_LANG` 선적용 후판정 사례 |
| C2 | 출처 불명 지시 실행 전 확인 | 세션 혼입 문장·무단 .env 변경 사례 |
| C3 | 고객 실데이터 저장소 commit X — `local_data/` 격리 후 보고 | PI20R05C06 5건 사례 |
| C4 | 미커밋 누적 X — 논리 단위 즉시 commit · 항목 번호 명기 | 77파일 6일치 뒤엉킴 · `verify_ui.py` `.gitignore` 사례 |
| C5 | 아카이브 복원 정본 = 삭제 커밋 이력 · 이동 시 해시 기록 | |
| C6 | 위험 작업 승인 없이 실행 X (HITL Approval Gate) — `DROP TABLE`·`rm -rf`·`git push --force`·`sudo`·`curl\|bash`·`npm publish`·`docker push prod`·`terraform apply -auto-approve`·Batch 1000+ | 5 카테고리 (data_loss·security·cost·system·irreversible) · `approval-gate-rules.md` · `approval-gate.py detect` |
| C7 | 멈춤 방지 — 파일 잠금·네트워크·권한 fail 시 즉시 `sys.exit` X · 60초 폴링·지수 backoff·대안 도구 | 사용자 노동 떠넘김 X · `best-practices.md § 멈춤 방지` |
| C8 | 같은 파일 동시 수정 X (Writer=1) | 다중 워커 race condition · `file-locking-policy.md` |
| C9 | 오염 파일 자동 정리 — `nul`·nested `.claude/.claude/`·3일+ bak/tmp/orig·14일+ logs·30일+ done · SessionStart hook 매 세션 | `cleanup-policy.md` · `cleanup-pollution.sh` |
| C10 | install 순서 강제 — kit 편집 → commit → sync → install → 검증 (Phase 1~3 미완 = Phase 4 위반) | `pre-install-lock.sh` 감지 · `best-practices.md § install 순서` |

### D. 조사·보고 규율
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| D0 | **대상 확정 0순위** — 매 사용자 지시 첫 응답 첫 줄 `대상: <path> (kit/설정/target/글로벌)` 명시 · 확정 전 grep·Read·Edit·Bash X | `direction-first.md` · `statusline.sh` · `user-prompt-auto-planner.sh` |
| D1 | 전제가 실측과 다르면 진행 X · 보고 (수석 지시여도) | 사이드바 폭 실측 반증 사례 |
| D2 | 조사와 구현 분리 · 조사 지시에 "수정 금지" | |
| D3 | 에러는 본문 끝까지 읽고 분류 — HTTP 코드·메시지 다르면 다른 사고 | 401·422 뭉뚱그림 사례 |
| D4 | 함수 한 줄로 판단 X — 전체 읽기 | 4416 라벨 함수 오독 사례 |
| D5 | 완료 보고 = 재발 전례 의심 시 재실측 · "사람이 할 일" 완료 보고 X | |
| D6 | 중간 확인 X — 큐 끝까지 · 완료 시 1회 항목별 (완료/커밋/실측/근거) · 멈춤 = ①운영 ②데이터 ③원칙 3가지만 | |
| D7 | **전수조사 = 100% Read** — grep·wc·ls 는 후보 좁히기용 · 결론은 각 파일 처음~끝 Read (100page = Read 100회+) · subagent 병렬 활용 | `failure-mode.md § 전수조사 위반` · `feedback_full_survey_read_all.md` |
| D8 | **고집 금지 (결정 존중)** — 수석 결정 시 그 방식 안에서 즉시 실행 · 우려·리스크·대안은 결정 전 최초 1회만 3줄 이내 · 결정 후 재우려·재제안·"하지만/그래도/차라리" 우회 설득 X · "못한다/안 된다" 는 실측 근거 (에러 원문·파일:라인) 없이 X · 예외 = 결정 시점에 없던 새 중대 사실 (데이터 손실·운영 장애·보안) 실측 확인 시 1회 보고, 그 후에도 결정 유지되면 그대로 실행 · 위반 시 SWEEP_LOG 기록 | `d8-no-stubborn.md` |
| D9 | task-instruction.md 없이 codex 호출 X | `codex-rules.md` |
| D10 | Gemini 리뷰 자동 채택 X (Claude 결정) | `gemini-review-policy.md` |
| D11 | 거짓 npm 패키지명 커맨드 X — `npm view` 검증 필수 · Windows npx 래퍼 `cmd /c npx` | `mcp-install-rules.md` |
| D12 | 회피·딴말 X — 직접 답 (yes/no/숫자) → 부연 → 행동 · "그건 그렇지만"·"여러 옵션" = 회피 | `failure-mode.md § 회피 안티패턴` |
| D13 | 기준 일관성 (Standards Drift Prevention) — 같은 카테고리 = 같은 기준 매번 · "이번엔 예외" 자기 판단 X · 룰 변경 시 명시 사유 + SoT 갱신 | `consistency.md` |
| D14 | 빈 task `done/` 이동 X (위장 완료) | codex hallucination 검출 (empty commit) |
| D15 | **환경 의존 결함** — 간헐적 실패·테스터별 결과 다름·자동 실행만 실패 등 신호 시 조작자 행동·환경 상태 (탭 포커스·visibilityState·OS 상태·시간·다른 세션) 를 조사 변수에 넣기 · 실패 만든 결함 vs 못 막은 결함 구분 | `environment-dependent-bug.md` · 2026-08-20 postmortem claude web 첨부 사례 |
| D16 | **계측 3 축** — ① 관측 직후 즉시 보고 (긴 작업·답 대기 뒤 X) ② 파일 append 보존 (메모리 dict X) ③ 증분 vs 증분 비교 (누적을 증분 기대값과 비교 X) · 세 축 모두 지켜야 계측이 살아있음 | `measurement-two-deaths.md` · 같은 postmortem |
| D17 | **관측 후 한 번 더 질문** — 「A 가 아니다」 는 결론이 아니라 다음 질문의 시작 · "상대가 안 받는다" 에서 멈추지 말고 "왜 안 받나" 던지기 | `investigation-discipline.md` · 같은 postmortem |
| D18 | **실물 채널 우선** — 새 채널 (새 창·새 프로세스·새 세션·Playwright 새 브라우저) 만들기 전 이미 실물에 닿아 있는 채널 (Bash·Grep·기존 확장·기존 MCP·기존 subagent) 먼저 · 새 채널은 새 문제 (재인증·상태 로드·race) 만듦 | `investigation-discipline.md` · 같은 postmortem |
| D19 | **이력 먼저** — 가설 세우기 전 재현 가능한 기록 (git log · .claude/logs · state · tasks/done · SWEEP_LOG) 훑기 · 1분 조회가 3시간 헛짚기 예방 | `investigation-discipline.md` · 같은 postmortem |
| D20 | **30초 실측 > 30분 추론** — 코드 읽기·spec·정황으로 결론 X · bash·curl·Playwright headed·브라우저 F12 로 실제 재현 후 결론 | `investigation-discipline.md` · 같은 postmortem |

### E. UI/UX 표준
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| E1 | LAYOUTSPEC 골격 (타이틀+1줄 설명 접힘 → 정본 필터바 4슬롯 → 카드 → 페이저) · 검색은 필터바 1곳 | 4종 SPEC 제작 중 |
| E2 | CONTENTSPEC 표현 (KPI·미니표·리스트막대·차트·각주·안내박스) — 라벨-값 세로 나열·본문 각주 X | |
| E3 | CHARTSPEC 6종 어휘 · MOTIONSPEC (진입 1회·hover·reduced-motion 존중·무한 반복 X) | |
| E4 | 같은 목적 컴포넌트 2개 X (정본 1곳) · 만들기 전 grep | `.hkpi` KPI 별도 구현·팝업 정의 3곳·min-width 5곳 사례 |
| E5 | 교재/강의 doc = 8섹션 (핵심·표·흐름·강점·약점·강추·우리매핑·점검) + 다이어그램 (SVG/HTML + 화살표) · 외국어 이미지 = 한글로 대체 (영어+한글 X) | `teaching-doc.md` |
| E6 | 산출물 자동 `-v2`/`-v3` X · `.bak` 백업 후 원본 덮어쓰기 · 원본 잠기면 사용자 알림 | `teaching-doc.md § 산출물 명명` |

### F. kit 고유 (orchestration_v1)
| # | 규칙 | 근거 · 상세 |
|---|---|---|
| F1 | `.claude/` 직접 편집 X (sync 덮어씀) — `plugins/` 원본만 | SoT 원칙 · `sync-workflow.md` |
| F2 | `~/.claude/` 직접 수정 X · 다른 프로젝트 폴더 직접 수정 X — `setup/templates/` + `setup/modules/` 거쳐 install 배포 | Template kit 원칙 · `best-practices.md § Template kit` |
| F3 | 사용자 액션 요구 X (Zero-touch) — 알림 크리티컬 5가지만 (시크릿·데이터손실·보안·비용·시스템손상) | `best-practices.md § Zero-touch` |
| F4 | 누락 의존성 사용자에게 X — `nohup` 백그라운드 자동 install (`auto-install-deps.sh` SessionStart hook 1h throttle) · 사용자 명시 거부 시만 skip | `feedback_auto_install_no_ask.md` |
| F5 | 사용자 요청 받자마자 auto-planner 5단계 (전수조사·분석·실행·확인·보고) + 30+ rule 자가 점검 + 막히면 codex/gemini 위임 | `plugins/exec_orch/skills/auto-planner.md` |
| F6 | **함수·훅·룰·skill·command 중복 X** — 새로 만들기 전 grep · A/B/C 접두사만 다른 동일 함수 X · `_v2`/`_new`/`_final` 접미사 X · 정본 덮어쓰기 + `.bak` | `consistency.md § 함수·훅·룰 중복` · `feedback_no_duplicate_function.md` |
| F7 | **감정·상황 자동 대응 매핑** — 답답→fast · 짜증→시스템 결함 진단 · 반복→loop · design→command 수정 · 방향→direction-first · 하드코딩→grep · 전수조사→100% Read · 망각→hook 등재 · install→순서 | `user-emotion.md` · `detect-user-emotion.sh` · `user-emotion-auto-response.md` skill |
| F8 | 자산 생성 감지 (PreToolUse Write) — 새 rule/hook/skill/command/agent/memory 생성 시 유사 파일 grep + 자매 파일 (bash↔PowerShell) 검사 | `detect-asset-creation.sh` · `asset-creation-workflow.md` skill |
| F9 | 반복 요청 감지 → `/loop` 발동 · 최근 5 프롬프트 키워드 3+ 겹치면 시스템 결함 신호 | `detect-repeat-request.sh` |
| F10 | optional chaining (`?.`) X · 코드 주석에 "owner(주인)" X | 이전 브라우저 호환 + 문화적 표현 회피 |

### 룰·메모리 빠른 검색 (RAG 인덱스)
룰·메모리·스크립트 누적 → grep 비효율 → 의미 기반 lookup. AI 가 먼저 활용.
```bash
python .claude/scripts/lookup-rule.py "검증 후 보고"   # 의미 기반 top-K
python .claude/scripts/lookup-rule.py --status        # 인덱스 상태
python .claude/scripts/lookup-rule.py --rebuild       # 강제 재구성
```
- 대상: `.claude/rules/*.md` · `~/.claude/projects/<proj>/memory/*.md` · `.claude/scripts/*` · `.claude/hooks/*` · CLAUDE.md § 7 (현재 252 entries)
- 자동 rebuild: PostToolUse Edit/Write 시 (룰·메모리·CLAUDE.md 변경 감지)
- 의존성 0 (TF 점수화 fallback) · chromadb 설치 시 벡터 검색 자동 전환 (예정)

---

## 8. 플러그인 편집 → 배포 플로우

```bash
vim plugins/exec_orch/commands/godmode.md      # 1. 원본 편집
bash .claude/scripts/sync-plugins.sh --dry     # 2. 미리보기
bash .claude/scripts/sync-plugins.sh           # 3. 실제 sync
python .claude/scripts/validate-plugin-schema.py  # 4. 검증
git add plugins/ .claude/ && git commit -m "..."  # 5. 커밋
```

---

## 9. 참조 (상세는 각 파일에)

- 사람용 가이드: `guide.txt`
- 설계 원칙 9가지: `docs/architecture-patterns.md`
- 로드맵 (Phase 1~3): `docs/2026-04-19/로드맵.md`
- 공유 규칙: `.claude/rules/*.md`
- plugin.json 스키마: `.claude-plugin/plugin-schema.json`
- 업그레이드 노트: `docs/upgrade-analysis-2026-04-19.md`
