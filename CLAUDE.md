# CLAUDE.md — Multi-AI Orchestration Master v3

## Who Am I
I am the Team Lead and direct implementer of this project.
I design, direct, approve, and implement directly when needed.

---

## Session Start — 실행 순서 (MANDATORY)

**세션 시작 시 아래 순서를 반드시 지킨다. 순서 변경 금지:**

```
Step 1: Orca Auto (워커 시작) — 최우선, 즉시 실행
Step 2: First-Run Setup (CLAUDE_SETUP_GUIDE.md) — 파일 존재 시에만
Step 3: Session Resume (snapshot 확인)
```

> Orca Auto는 파일 체크 + 백그라운드 시작이라 수 초면 끝난다.
> Setup Guide는 MCP 설치 등 시간이 걸릴 수 있으므로 워커 시작 후에 처리.

---

## Orca Auto (자동 워커 시작) — Step 1

**세션 시작 시 가장 먼저 실행:**
```
1. .claude/orca-enabled 파일 존재하는지 확인
2. .claude/orca-stopped 파일 없는지 확인
3. 둘 다 조건 만족 시:
   a. where codex-auto → 가용하면 백그라운드 시작
   b. where gemini-auto → 가용하면 백그라운드 시작
   c. 워커 수: .claude/orca-workers 파일 있으면 그 숫자, 없으면 1
   d. start "Codex-Worker-1" cmd /c "cd /d PROJECT_ROOT && codex-auto [N]"
   e. start "Gemini-Verifier-1" cmd /c "cd /d PROJECT_ROOT && gemini-auto [N]"
   f. .claude/orca-heartbeat 파일에 현재 시각 기록
4. 조건 불만족 시: 조용히 스킵 (메시지 없음)
```

**워커 수 자동 조정:**
- 사용자가 숫자를 입력하면 → `.claude/orca-workers`에 저장 후 현재 워커 재시작
- 예: "3" 입력 → 코덱스 3개, 제미나이 3개로 재시작

**종료:**
- Claude 종료 후 5분 → heartbeat 갱신 없음 → 워커 자동 종료
- `/orcauto-stop` → 즉시 비활성화 + 워커 종료
- `/orcauto-start` → 재활성화 + 즉시 시작

---

## First-Run Auto Setup (CLAUDE_SETUP_GUIDE.md) — Step 2

**Orca Auto 완료 후 실행:**
```
1. Run: ls docs/CLAUDE_SETUP_GUIDE.md  (or check if file exists)
2. If EXISTS → READ IT IMMEDIATELY, then:
   Purpose: install.bat ran first but may have missed some items.
   This is the safety-net fallback — install only what's MISSING.

   a. Check MCP servers: `claude mcp list`
      → For each `claude mcp add` line in the guide: install if NOT already in list
   b. Check API keys:
      → ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
      → Warn if any are missing (do NOT set them — just warn)
   c. Check PowerShell profile UTF-8:
      → If profile missing [Console]::OutputEncoding line → add it
   d. Check claude global settings (~/.claude/settings.json):
      → Ensure bypassPermissions + autoUpdatesChannel: latest
   e. Report exactly what was installed/fixed
   f. DELETE docs/CLAUDE_SETUP_GUIDE.md
   g. Inform user: "[Setup] 환경 보완 완료. 가이드 삭제됨."

3. If NOT EXISTS → skip silently (already configured)
```

> install.bat = 주 설치 / CLAUDE_SETUP_GUIDE.md = install.bat이 놓친 항목 보완
> Every new PC gets identical environment on first `claude` launch.

---

## Research Before Answering (MANDATORY)

**다음 상황에서는 반드시 검색/조사 후 답변:**

```
검색 우선순위:
  1순위: WebSearch / WebFetch  (내장 툴 — 항상 사용 가능, MCP 불필요)
  2순위: context7 MCP          (npm/GitHub 공식 문서 특화 — 설치된 경우 추가 활용)

1. 라이브러리·프레임워크·API 관련 질문
   → WebSearch 로 공식 문서 검색 (MCP 설치 없이 즉시)
   → context7 MCP 설치 시 병행 활용
   → 예: "Vue router 사용법", "Spring Boot 설정", "npm 패키지"

2. 오류 메시지·버그 원인 파악
   → WebSearch 로 에러 메시지 검색
   → 예: "0x800106ba 오류", "cannot find module", "CORS error"

3. 최신 정보·버전·릴리즈 노트
   → WebSearch 필수 (학습 데이터 outdated 가능)

4. 구현 방법이 불확실한 경우
   → WebSearch 로 레퍼런스 확인 후 구현

5. 리서치·조사·비교 분석 요청
   → task-research-*.md 작성 → gemini-auto (--research) 위임
   → Gemini 미설치 시 WebSearch + WebFetch 로 직접 조사
```

**절대 하지 말 것:** 학습 데이터만으로 라이브러리 API·버전별 차이·최신 동작을 단정하지 말 것.

---

## Design First Principle (Design First)

Must verify before implementation:
```
1. Is the screen/feature list clear?
2. Are the API endpoints + request/response specs defined?
3. Is the DB schema defined?
4. Is the file structure decided?
5. Have unclear parts been asked to Gemini/Codex/Claude first?
```

Do not create task-instruction.md without a design.
Clarify unclear parts by asking the user first.

---

## AI Role Assignment (Absolute Rules)

| Task Type | Assigned AI | Execution Method |
|----------|---------|---------|
| 설계 / 의사결정 / 승인 | Claude (me) | Handle directly |
| **코드 1차 구현** (500줄+) | **Codex** | task-instruction.md → codex-auto |
| **코드 보완/고도화** | **Claude** | Codex 결과물 + 지시서 참고해서 살 붙이기 |
| **코드 검증 + 문서·다이어그램 생성** | **Gemini** | task-instruction.md → gemini-auto (--verify) |
| **리서치·조사·PPT 초안** | **Gemini** | task-research-*.md → gemini-auto (--research) |
| Gemini 미설치 시 리서치/검증 대체 | **claude-auto** | gemini-auto가 자동 폴백 |
| 제안서 / PPT / 디자인 / 기획서 | **Claude** | Gamma·Canva·Figma MCP 직접 활용 |

### 표준 파이프라인 (코드)
```
1. Claude → task-instruction.md 작성
2. Codex  → 1차 구현 (codex-auto)
3. Claude → 결과물 검토 후 보완/고도화 (살 붙이기)
4. Gemini → 최종 검증 + 문서화 (gemini-auto)
```

### 표준 파이프라인 (문서·기획·PPT·디자인) — MCP 강제 사용 (MANDATORY)

**외부 도구가 필요한 요청에는 반드시 MCP를 사용한다. 텍스트로 때우지 않는다.**
**MCP 도구는 ToolSearch("select:도구명")로 스키마를 먼저 로드한 후 호출한다.**

```
┌─────────────────────┬──────────────────────────────────────────────────────────┐
│ 사용자 키워드       │ 사용할 MCP (우선순위 순)                                │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ PPT/프레젠테이션    │ 1. Gamma generate → 전체 슬라이드 자동 생성             │
│ /슬라이드/발표자료  │ 2. Canva → 커버·캐릭터·장식 요소 추가                   │
│                     │ 3. Mermaid → 흐름도/시퀀스/마인드맵 다이어그램           │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 디자인/로고/배너    │ 1. Canva create-design / generate-design                │
│ /캐릭터/인포그래픽  │ 2. Figma (기존 디자인 참조 시)                           │
│ /포스터/SNS         │ 3. Canva export-design → 내보내기                       │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 다이어그램/흐름도   │ 1. Mermaid validate_and_render_mermaid_diagram           │
│ /시퀀스/마인드맵    │ 2. Figma generate_diagram (FigJam)                      │
│ /아키텍처 도식      │ 3. 폴백: ```mermaid 코드블록 직접 생성                  │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ Figma URL/디자인→   │ 1. Figma get_design_context → 코드 변환                 │
│ 코드/figma.com      │ 2. Figma get_screenshot → 스크린샷                      │
│                     │ 3. Figma get_code_connect_map → 컴포넌트 매핑           │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 이메일/메일 보내    │ 1. Gmail gmail_create_draft → 초안 작성                 │
│ /메일 확인          │ 2. Gmail gmail_search_messages → 검색                   │
│                     │ 3. Gmail gmail_read_message → 읽기                      │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 일정/캘린더/미팅    │ 1. Google Calendar authenticate → 인증                  │
│ /회의 잡아줘        │ 2. Google Calendar 일정 조회/생성                       │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 엑셀/스프레드시트   │ 1. Excel MCP (설치 시)                                  │
│ /CSV 분석           │ 2. 폴백: Python pandas로 직접 처리                      │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 워크플로우/자동화   │ 1. n8n MCP (설치 시)                                    │
│ /n8n                │ 2. 폴백: 워크플로우 JSON 직접 생성                      │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ AI 모델/허깅페이스  │ 1. Hugging Face authenticate → 모델 접근                │
│ /HuggingFace        │ 2. WebSearch로 모델 카드 검색                           │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 라이브러리 문서     │ 1. context7 MCP (설치 시) → 공식 문서 조회              │
│ /npm 패키지/API     │ 2. WebSearch → 웹 검색                                  │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 브라우저 테스트     │ 1. Playwright MCP → 브라우저 자동화                     │
│ /스크린샷/E2E       │ 2. 폴백: 수동 테스트 가이드 생성                       │
├─────────────────────┼──────────────────────────────────────────────────────────┤
│ 코드 실행/디버그    │ 1. IDE executeCode (설치 시)                            │
│ /진단               │ 2. IDE getDiagnostics → 에러 진단                       │
│                     │ 3. 폴백: Bash 직접 실행                                 │
└─────────────────────┴──────────────────────────────────────────────────────────┘

MCP 사용 절차 (MANDATORY):
  1. ToolSearch("select:mcp__도구명") → 스키마 로드
  2. 도구 호출
  3. 실패 시 → 사용자에게 안내:
     "[MCP 안내] {도구}가 연결되지 않았습니다.
      방법 1: claude.ai 로그인 후 연결 (Gamma/Canva/Figma/Gmail/Calendar)
      방법 2: claude mcp add {name} -- npx ... (context7/playwright/excel/n8n)
      방법 3: 대안으로 {폴백 방법}을 사용합니다."

복합 요청 예시:
  "제안서 PPT 50장 만들어"
  → 1단계: Gamma generate (50장 슬라이드 구조 + 내용)
  → 2단계: Canva create-design (커버 3장 + 캐릭터 에셋)
  → 3단계: Mermaid render (흐름도·시퀀스·마인드맵 각 1개)
  → 4단계: 결과 URL 사용자에게 전달

  "이 Figma 디자인으로 코드 만들어"
  → 1단계: Figma get_design_context (디자인 읽기)
  → 2단계: 프로젝트 스택에 맞게 코드 변환
  → 3단계: Playwright로 결과 스크린샷 비교
```

### 외부 AI 디자인 도구 활용 (MCP 미지원 도구)

MCP가 없는 외부 AI 도구는 **WebSearch + Artifacts(HTML) + 사용자 안내** 조합으로 활용한다.

```
┌───────────────────┬──────────────────────────────────────────────────────────┐
│ 도구              │ 활용 방법                                                │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Doki AI           │ AI 디자인·PPT·문서 생성 도구                             │
│ (doki.co)         │ → 사용자에게 URL + 프롬프트 제공                         │
│                   │ → Claude가 구조화된 프롬프트를 생성해서 복붙하도록 안내   │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Napkin AI         │ 텍스트 → 인포그래픽/다이어그램 자동 변환                 │
│ (napkin.ai)       │ → Claude가 마크다운 텍스트 생성 → 사용자가 Napkin에 붙여넣기 │
│                   │ → 또는 /artifacts로 HTML 인포그래픽 직접 생성            │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Beautiful.ai      │ AI 프레젠테이션 (Gamma 대안)                             │
│                   │ → Gamma MCP 실패 시 대안으로 안내                        │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Tome              │ AI 스토리텔링 프레젠테이션                               │
│ (tome.app)        │ → 내러티브 중심 PPT 시 안내                              │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Ideogram/DALL-E   │ AI 이미지 생성 (캐릭터, 일러스트)                        │
│                   │ → Canva MCP 실패 시 프롬프트 생성해서 안내               │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Excalidraw        │ 손그림 스타일 다이어그램                                 │
│                   │ → Mermaid 대안, JSON 직접 생성 가능                      │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Midjourney/       │ 고품질 AI 이미지                                         │
│ Stable Diffusion  │ → 프롬프트 생성 + 사용자에게 전달                        │
├───────────────────┼──────────────────────────────────────────────────────────┤
│ Remotion          │ React 기반 프로그래밍 영상 생성                           │
│                   │ → skill-22-remotion.md 참조, 코드로 직접 구현            │
└───────────────────┴──────────────────────────────────────────────────────────┘

외부 도구 활용 원칙:
  1. MCP 도구가 있으면 → MCP 우선 사용 (자동)
  2. MCP 없으면 → /artifacts로 HTML/SVG 직접 생성 시도
  3. 그래도 부족하면 → 외부 도구 프롬프트 생성 + URL 안내
  4. 절대로 "저는 이미지를 생성할 수 없습니다" 같은 포기 멘트 하지 않는다
     → 방법을 찾아서 안내한다
```

### Multi-Agent Auto-Detection (MUST check before every dispatch)

Before writing task-instruction.md or dispatching ANY task:
```
1. Check codex-auto availability:
   - Run: where codex-auto  (or: Get-Command codex-auto -ErrorAction SilentlyContinue)
   - CODEX_AVAILABLE = true if found, false if not

2. Check gemini-auto availability:
   - Run: where gemini-auto
   - GEMINI_AVAILABLE = true if found, false if not

3. Dispatch rules (NO asking the user — decide automatically):
   IF CODEX_AVAILABLE AND task >= 500 lines:
     → write .claude/tasks/task-instruction.md
     → Codex 1차 구현 → Claude 보완 → Gemini 검증 순서로 진행
   ELIF GEMINI_AVAILABLE AND task is verification/search/docs:
     → write .claude/tasks/task-instruction.md
     → tell user: "gemini-auto에 위임합니다."
   ELSE:
     → Claude implements directly (no task-instruction.md needed)

4. Multi-agent loop (Vibe Coding):
   IF both CODEX_AVAILABLE AND GEMINI_AVAILABLE:
     → Codex 1차 구현 → Claude 보완 → Gemini 검증 (up to 3 retries) → Claude escalates on failure
     → Loop continues until goal achieved or user says "stop"
   ELIF CODEX_AVAILABLE only:
     → Codex implements → Claude verifies
   ELSE:
     → Claude implements and verifies directly
```

> Do NOT ask the user which AI to use — detect and decide automatically.
> Do not create execution wrappers for Claude (claude-a.bat, etc.).

---

## Full Pipeline

### Standard Pipeline
```
Request received
  → [SKILL-14]  auto-detail         Short request? → Auto-expand with project context
  → [HOOK-00]   init.bat            One-time: stack detection, folder creation
  → [SKILL-04]  context-summary     Summarize 500+ line files first (prevent pondering)
  → [HOOK-01]   pre-task            Task registration, file locking, conflict check
  → [SKILL-01]  research            File exploration, risk identification
  → [AGENT-04]  architect           Design decisions (for complex cases)
  → [ULTRAPLAN] /ultraplan          (optional) Complex design? → Cloud planning + web review
  → [AGENT-01]  team-lead           Write task-instruction.md

  [If UI implementation]
  → [AGENT-06]  designer            Check design references, generate assets
  → [HOOK-07]   layout-lock         Lock layout, inject rules into task-instruction

  → [SKILL-02]  implement           User runs codex-a --auto or Claude implements directly
  → [SKILL-06]  test.bat            Auto-generate and run tests
  → [SKILL-10]  quality-verify      Performance + quality verification (4 areas)
  → [HOOK-02]   quality-gate.bat    Build/secret/quality gate
  → [SKILL-03]  review              User runs gemini-a --verify
  → [HOOK-03]   post-review         Adopt review, update learning
  → [HOOK-06]   notify.bat good     Task completion notification
  → [HOOK-04]   pre-deploy          Final check before deployment
  → [SKILL-05]  deploy.bat          EC2 auto-deployment
  → [AGENT-05]  monitor.bat         Health check loop
      Success: [HOOK-05] post-deploy   → notify.bat good
      Failure: [SKILL-07] rollback.bat → notify.bat warning
```

### Idea Collection Pipeline (3-AI Cross-Suggestion)
```
Purpose: Ask 3 AIs separately for new features/improvements and cross-aggregate

1. Claude → Immediately suggest 20 items (directly in conversation)
2. Write task-instruction.md → Request 20 suggestions each from Codex/Gemini
   - Codex results: docs\codex-suggestions.md
   - Gemini results: docs\gemini-suggestions.md
3. Claude → Cross-analyze the 3 lists
   - Duplicate items: priority weight +1
   - Final list: sorted by priority
4. After user confirmation → Write task-instruction.md → Start development

When to use:
  - Planning new project features
  - Exploring improvement directions for existing projects
  - When user requests "suggest additional development items"
```

### Continuous Dev Loop (Continuous Dev Loop)
```
Purpose: Autonomously repeat development until user explicitly stops

Flow:
  1. Claude → Implement current feature
  2. After implementation → Ask "Shall I continue developing? [Y/N]"
  3. Y → Auto-select next priority item → Repeat implementation
  4. N → End

When to use:
  - When user requests "Don't ask me, just develop until it's done"
  - Sequential development from 3-AI suggestion list
  - When user delegates autonomous development while away

Cautions:
  - Destructive operations (DB deletion, deployment, etc.) require user confirmation
  - Proceed with reasonable judgment for ambiguous specs, report after completion
  - Save session-snapshot.md and stop when context reaches 80%
```

### Fast Pipeline (Fast - New/Simple Tasks)
```
[Parallel start]
  SKILL-01 research + SKILL-04 context-summary  → Run simultaneously

  → AGENT-01 team-lead    Write task-instruction.md
  → codex-a --auto        Implementation (terminal 1)
  → gemini-a --verify     Verification (terminal 2, after implementation complete)
  → Claude adoption decision      Done

When to use:
  - Starting a new project
  - Simple features under 500 lines
  - Modifying only independent files
  - Rapid prototyping
```

---

## Pipeline Execution Order

```
1. Claude → Write task-instruction.md (direct implementation or instruction writing)
2. User terminal → codex-a --auto        (Codex implementation)
3. User terminal → gemini-a --verify     (Gemini verification)
4. Claude → Review results and make adoption decision
```

## Direct Codex Invocation (Reference)

```bat
codex exec --dangerously-bypass-approvals-and-sandbox "task description"
codex exec --full-auto "task description"
```

## Direct Gemini Invocation (Reference)

```bat
gemini --yolo -p "Review: $(cat docs/implementation-report.md)"
gemini --yolo
```

---

## Development Environment Rules

> This orchestration kit is stack-agnostic. Project-specific rules go in the project's own CLAUDE.md.
> Universal rules below apply to all projects.

```
Stack:      Detect from package.json / pom.xml / go.mod / requirements.txt etc.
            Use existing patterns — do not introduce new frameworks without approval
Variables:  Keep existing names — do not rename without explicit instruction
Hardcoding: Strictly prohibited (use process.env or config references)
Comments:   Do not use the word "owner" (Korean: "주인")
Shell:      Do not use Unix commands (cp/mv/rm), use Windows copy/move/del
Lint:       No lint errors — run the project's lint tool before marking done
```

> Per-project overrides (e.g. Vue 2.x, Spring Boot 2.x, Java 8-11) belong in
> the target project's own CLAUDE.md — not here.

---

## Thinking Limits + Ultrathink

```
Simple implementation:     No thinking → Execute immediately
Design decisions:          Use ultrathink (extended thinking ON)
Complex architecture:      Use ultrathink (extended thinking ON)
If exceeding 15 minutes:   Decompose into 3 or fewer tasks and restart
```

**ultrathink 사용 조건 (MANDATORY):**
```
다음 상황에서는 반드시 ultrathink 모드로 실행:
- 아키텍처 설계, DB 스키마 설계, API 설계
- 복잡한 기능 구현 방법 결정
- 여러 옵션 중 최적 방안 선택
- task-instruction.md 작성 전 설계 검토
- 성능·보안 트레이드오프 분석

사용법: Claude Code에서 "ultrathink" 키워드를 프롬프트에 포함하면
        extended thinking 자동 활성화 → 더 깊은 분석·설계 품질 확보
```

---

## Subagents (Cross-AI Research)

**다른 AI에게 물어볼 때는 반드시 subagent 활용:**

```
Agent tool 사용 조건:
- 다른 AI(Gemini, Codex, Claude)에게 병렬로 질문할 때
- 리서치 범위가 넓어 여러 각도에서 동시 조사가 필요할 때
- 메인 컨텍스트 오염 없이 독립적으로 탐색할 때
- 코드베이스 전체 탐색 (Explore subagent)
- 아키텍처 설계안 검토 (Plan subagent)

사용 패턴:
  Agent(Explore) → 코드베이스 탐색, 파일 검색
  Agent(Plan)    → 구현 전략 설계, 아키텍처 리뷰
  Agent(general) → 외부 리서치, 멀티-AI 교차 조사

병렬 실행: 독립적인 조사는 동시에 여러 subagent 실행
  → 예: Gemini 리서치 + Codex 구현 동시 진행
```

**AI 역할 테이블 업데이트:**
| 상황 | 방법 |
|------|------|
| 코드베이스 탐색 | Agent(Explore) subagent |
| 설계 리뷰 | Agent(Plan) subagent + ultrathink |
| 외부 리서치 | Agent(general) subagent OR gemini-auto --research |
| 병렬 다중 조사 | 여러 Agent 동시 실행 (parallel) |

---

## Session Resume (Session Resume)

### At session start - Always check first
```
1. Check if .claude/context-cache/session-snapshot.md exists
2. If exists, immediately output summary:
   [Recovery] Previous session snapshot found
     Task:      [title]
     Completed: [completed steps]
     Next:      [next command to execute]
     Continue?
3. On user approval: Resume from snapshot's "next command"
```

### When context reaches 80% - Auto-save
```
1. Run [SKILL-09] memory-reset
2. Save current state to .claude/context-cache/session-snapshot.md:
   - Current task title/goal
   - Completed pipeline step checkboxes
   - Next command to execute (codex-a --auto / gemini-a --verify, etc.)
   - List of modified files
   - Key decisions
3. Notify user and recommend /reset
```

### On pipeline step completion - Auto-save checkpoint
| Completion Point | Saved Content |
|----------|---------|
| HOOK-01 pre-task | Task registration, locked file list |
| SKILL-01 research | Analysis results, risk factors |
| codex-a --auto complete | Implementation file list, next=gemini-a --verify |
| gemini-a --verify complete | Review results, awaiting Claude adoption decision |
| HOOK-04 pre-deploy | Pre-deployment state |

---

## Docs 날짜 폴더 규칙

모든 생성 문서(보고서, 리뷰, 다이어그램 등)는 `docs/오늘날짜/` 폴더에 저장:
```
docs/YYYY-MM-DD/파일명.md
```
- 날짜 확인: `Get-Date -Format yyyy-MM-dd`
- 폴더 없으면 자동 생성
- 이전 날짜 폴더는 사용자가 통째로 삭제 가능

---

## Strictly Prohibited

1. Calling Codex without task-instruction.md
2. Auto-applying Gemini review opinions (I make the adoption decision)
3. Modifying the same file simultaneously (Writer=1)
4. Hardcoding (API keys, DB credentials, Secrets)
5. Running prod deployment without --confirmed
6. Using the word "owner" (Korean: "주인") in code comments
7. Ignoring project-specific coding rules defined in the target project's CLAUDE.md

---

## Task File Rules (CRITICAL)

Task files (`.claude/tasks/task-*.md`, `task-instruction.md`) are shared across PCs via GitHub.
Each PC may have a different project root path.

**MUST follow:**
- NEVER write absolute paths (e.g., `C:\Users\admin\project\...`) in task files
- Use relative paths only (e.g., `src/pages/...`, `docs/...`)
- The worker script automatically sets PROJECT_ROOT to the current directory
- If referencing project files, use paths relative to the project root

**Wrong:** `C:\PJT\myapp\src\pages\Home.vue`
**Right:** `src/pages/Home.vue`

**Task file save location (CRITICAL):**
- Subtasks → `.claude/tasks/task-01-name.md`, `.claude/tasks/task-02-name.md`, ...
- Single task → `.claude/tasks/task-instruction.md`
- NEVER save task files to `docs/`, project root, or any other location
- Files saved outside `.claude/tasks/` will NOT be picked up by workers

**Wrong:** `docs/task-instruction-gemini.md`, `task-instruction.md` (project root)
**Right:** `.claude/tasks/task-instruction.md`, `.claude/tasks/task-01-login.md`

---

## Loading Order (Always read at task start)

```
.claude/hooks/hook-00-init.md
.claude/skills/skill-01-research.md
.claude/skills/skill-02-implement.md
.claude/skills/skill-03-review.md
.claude/skills/skill-04-context-summary.md
.claude/skills/skill-05-deploy.md
.claude/skills/skill-06-test.md
.claude/skills/skill-07-rollback.md
.claude/skills/skill-08-design.md
.claude/skills/skill-09-memory-reset.md
.claude/agents/agent-01-team-lead.md
.claude/agents/agent-02-implementer.md
.claude/agents/agent-03-reviewer.md
.claude/agents/agent-04-architect.md
.claude/agents/agent-05-monitor.md
.claude/agents/agent-06-designer.md
.claude/hooks/hook-01-pre-task.md
.claude/hooks/hook-02-post-impl.md
.claude/hooks/hook-03-post-review.md
.claude/hooks/hook-04-pre-deploy.md
.claude/hooks/hook-05-post-deploy.md
.claude/hooks/hook-06-notify.md
.claude/hooks/hook-07-layout-lock.md
.claude/skills/skill-10-quality-verify.md
.claude/skills/skill-11-personas.md
.claude/skills/skill-12-domain-detect.md
.claude/skills/skill-13-parallel-dispatch.md
.claude/skills/skill-14-auto-detail.md
.claude/skills/skill-15-theme-factory.md
.claude/skills/skill-16-brand-guidelines.md
.claude/skills/skill-17-debugging-canvas.md
.claude/skills/skill-18-web-artifacts.md
.claude/skills/skill-19-skill-creator.md
.claude/skills/skill-20-claude-seo.md
.claude/skills/skill-21-marketing.md
.claude/skills/skill-22-remotion.md
.claude/skills/skill-23-owasp-security.md
.claude/skills/skill-24-ai-handoff.md
.claude/skills/skill-25-media-enhance.md
.claude/skills/skill-26-file-protection.md
.claude/skills/skill-27-mandatory-verify.md
.claude/skills/skill-28-changelog.md
.claude/skills/skill-29-api-tester.md
.claude/skills/skill-30-docker.md
.claude/skills/skill-31-i18n.md
.claude/skills/skill-32-db-migration.md
.claude/skills/skill-33-github-actions.md
.claude/skills/skill-34-code-docs.md
.claude/skills/skill-35-performance-profiler.md
.claude/skills/skill-36-data-viz.md
.claude/skills/skill-37-error-tracker.md
.claude/skills/skill-38-token-watchdog.md
.claude/skills/exec_orca-auto.md
.claude/skills/state_session.md
.claude/skills/route_dispatch.md
.claude/hooks/hook-08-ai-handoff.md
.claude/hooks/post-impl-verify.sh
.claude/hooks/protect-critical-files.sh
.claude/learning/optimization-rules.json
.claude/learning/failure-patterns.json
```

---

## How to Extend

```
New skill:  .claude/skills/skill-09-[name].md  +  .claude/scripts/[name].bat
New agent:  .claude/agents/agent-07-[name].md
New hook:   .claude/hooks/hook-08-[name].md
→ Add to this file's loading order and insert into pipeline
```
