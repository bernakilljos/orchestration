# Plugin-Centric Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `.claude/` 하위 자산을 plugin-centric 구조로 재정리 — 기능 유지, 중복 제거, 명명 규칙 통일, plugin.json + hooks.json 도입

**Architecture:** 기존 `.claude/` 구조는 Claude Code 실행 요구사항이므로 유지하되, `.claude-plugin/` 을 새 canonical 레이어로 추가. 명명 규칙(exec_/design_/review_/route_/state_/hook_ 접두사)을 신규 파일에 적용하고 기존 파일은 legacy alias로 남긴다. 기존 orca-* 상태 파일은 `.claude/` 루트에 유지(호환성), `.claude/state/` 는 신규 상태 파일 전용.

**Tech Stack:** Markdown (skill/agent/command), JSON (plugin.json, hooks.json), Windows .bat, bash .sh

---

## Inventory 분석

### 현재 자산 현황

| 카테고리 | 파일 수 | 경로 | 비고 |
|---------|--------|------|------|
| agents | 6 | `.claude/agents/agent-0N-*.md` | 번호 접두사 |
| commands | 21 | `.claude/commands/*.md` | 슬래시 커맨드 |
| hook markdown | 9 | `.claude/hooks/hook-0N-*.md` | 명세 문서 |
| hook scripts | 9 | `.claude/hooks/*.py/.sh` | 실제 실행 |
| scripts | 18 | `.claude/scripts/*.bat/.sh` | 실행 스크립트 |
| skills | 38 | `.claude/skills/skill-NN-*.md` | 번호 접두사 |
| root workers | 2 | `codex-auto.bat`, `gemini-auto.bat` | 프로젝트 루트 |
| settings | 2 | `.claude/settings*.json` | hooks 등록 |

### 유지 / 이동 / 신규 판단

| 구분 | 대상 | 처리 방법 |
|------|------|---------|
| **유지** | `.claude/skills/skill-*.md` (38개) | 경로·내용 그대로 유지 (레거시 alias) |
| **유지** | `.claude/agents/agent-*.md` (6개) | 경로·내용 그대로 유지 |
| **유지** | `.claude/scripts/codex-auto.bat`, `gemini-auto.bat` | 루트 래퍼 유지 |
| **유지** | `codex-auto.bat`, `gemini-auto.bat` (루트) | 루트 진입점 유지 |
| **유지** | `.claude/settings.json` hooks | 현행 hooks 설정 유지 |
| **신규** | `.claude-plugin/plugin.json` | 플러그인 메타 + 진입점 선언 |
| **신규** | `.claude-plugin/docs/migration-map.md` | old→new 매핑 문서 |
| **신규** | `.claude/hooks/hooks.json` | 훅 등록 manifest |
| **신규** | `.claude/state/` | 상태 파일 전용 디렉터리 |
| **신규** | `.claude/skills/exec_orca-auto.md` | orcauto 로직을 skill로 승격 |
| **신규** | `.claude/skills/state_session.md` | 세션 상태 관리 skill |
| **신규** | `.claude/skills/route_dispatch.md` | AI 라우팅/판단 skill |
| **슬림화** | `.claude/commands/orcauto-start.md` | exec_orca-auto skill 참조 wrapper로 교체 |
| **슬림화** | `.claude/commands/orcauto-stop.md` | exec_orca-auto skill 참조 wrapper로 교체 |
| **슬림화** | `.claude/commands/vibe-loop.md` | route_dispatch skill 참조 wrapper로 교체 |
| **슬림화** | `.claude/commands/check-agents.md` | state_session skill 참조 wrapper로 교체 |

---

## 최종 디렉터리 트리

```
project-root/
├── .claude-plugin/
│   ├── plugin.json                    ← 플러그인 메타데이터
│   └── docs/
│       └── migration-map.md           ← old→new 매핑
├── .claude/
│   ├── agents/                        ← 유지 (기존 agent-0N-*.md)
│   ├── commands/                      ← 슬림 wrapper만
│   │   ├── orcauto-start.md           ← exec_orca-auto 참조
│   │   ├── orcauto-stop.md            ← exec_orca-auto 참조
│   │   ├── vibe-loop.md               ← route_dispatch 참조
│   │   ├── check-agents.md            ← state_session 참조
│   │   └── ... (나머지 21개 유지)
│   ├── hooks/
│   │   ├── hooks.json                 ← 신규: 훅 등록 manifest
│   │   ├── hook-00-init.md … hook-08-ai-handoff.md  ← 유지
│   │   └── *.py / *.sh               ← 유지
│   ├── scripts/                       ← 유지 (기존 이름 유지)
│   ├── skills/
│   │   ├── skill-01-research.md … skill-38-token-watchdog.md  ← 유지
│   │   ├── exec_orca-auto.md          ← 신규: orcauto 로직 skill
│   │   ├── state_session.md           ← 신규: 세션 상태 관리
│   │   └── route_dispatch.md          ← 신규: AI 라우팅 판단
│   ├── state/                         ← 신규 디렉터리
│   │   ├── .gitkeep
│   │   └── README.md
│   ├── learning/                      ← 유지
│   ├── tasks/                         ← 유지
│   ├── context-cache/                 ← 유지
│   ├── settings.json                  ← 유지
│   └── settings.local.json            ← 유지
```

---

## 명명 규칙 (신규 파일 적용)

| 접두사 | 용도 | 예시 |
|-------|------|------|
| `exec_` | 실행 계열 | `exec_orca-auto.md`, `exec_deploy.md` |
| `design_` | 디자인/PPT | `design_ui.md`, `design_theme.md` |
| `review_` | 검증/리뷰 | `review_code.md`, `review_quality.md` |
| `route_` | 라우팅/판단 | `route_dispatch.md`, `route_team-lead.md` |
| `state_` | 상태 저장 | `state_session.md`, `state_token.md` |
| `hook_` | 훅 관련 | `hook_pre-task.md` |

기존 파일(`skill-NN-*.md`, `agent-0N-*.md`)은 레거시 alias로 유지.

---

## Task 1: `.claude-plugin/` 디렉터리 + plugin.json 생성

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/docs/` (dir)

- [ ] **Step 1: 디렉터리 생성**

```bash
mkdir -p .claude-plugin/docs
```

- [ ] **Step 2: plugin.json 작성**

```json
{
  "schema_version": "1.0",
  "name": "orchestration-kit",
  "display_name": "Multi-AI Orchestration Kit",
  "version": "3.0.0",
  "description": "Claude + Codex + Gemini 멀티AI 오케스트레이션 킷 — 설계·구현·검증 파이프라인 자동화",
  "author": "bernakilljos",
  "repository": "https://github.com/bernakilljos/orchestration",
  "entry_points": {
    "session_start": "exec_orca-auto",
    "task_route": "route_dispatch",
    "state_save": "state_session"
  },
  "skills": {
    "prefix_convention": {
      "exec_": "실행 계열 — 작업 수행",
      "design_": "디자인/PPT/UI 계열",
      "review_": "검증/리뷰 계열",
      "route_": "라우팅/판단 계열",
      "state_": "상태 저장/복구 계열",
      "hook_": "훅 관련 계열"
    },
    "new": [
      "exec_orca-auto",
      "state_session",
      "route_dispatch"
    ],
    "legacy": [
      "skill-01-research",
      "skill-02-implement",
      "skill-03-review",
      "skill-04-context-summary",
      "skill-05-deploy",
      "skill-06-test",
      "skill-07-rollback",
      "skill-08-design",
      "skill-09-memory-reset",
      "skill-10-quality-verify",
      "skill-11-personas",
      "skill-12-domain-detect",
      "skill-13-parallel-dispatch",
      "skill-14-auto-detail",
      "skill-15-theme-factory",
      "skill-16-brand-guidelines",
      "skill-17-debugging-canvas",
      "skill-18-web-artifacts",
      "skill-19-skill-creator",
      "skill-20-claude-seo",
      "skill-21-marketing",
      "skill-22-remotion",
      "skill-23-owasp-security",
      "skill-24-ai-handoff",
      "skill-25-media-enhance",
      "skill-26-file-protection",
      "skill-27-mandatory-verify",
      "skill-28-changelog",
      "skill-29-api-tester",
      "skill-30-docker",
      "skill-31-i18n",
      "skill-32-db-migration",
      "skill-33-github-actions",
      "skill-34-code-docs",
      "skill-35-performance-profiler",
      "skill-36-data-viz",
      "skill-37-error-tracker",
      "skill-38-token-watchdog"
    ]
  },
  "agents": {
    "roles": {
      "route": ["agent-01-team-lead", "agent-04-architect"],
      "exec": ["agent-02-implementer"],
      "review": ["agent-03-reviewer"],
      "monitor": ["agent-05-monitor"],
      "design": ["agent-06-designer"]
    }
  },
  "hooks": {
    "config": ".claude/hooks/hooks.json",
    "scripts_dir": ".claude/hooks/"
  },
  "state": {
    "dir": ".claude/state/",
    "orca_flags": ".claude/",
    "notes": "orca-* 플래그 파일은 하위 호환성을 위해 .claude/ 루트에 유지"
  },
  "workers": {
    "codex": "codex-auto.bat",
    "gemini": "gemini-auto.bat",
    "task_dir": ".claude/tasks/"
  }
}
```

- [ ] **Step 3: plugin.json 파일 생성 (Write tool 사용)**

- [ ] **Step 4: 검증**

```bash
cat .claude-plugin/plugin.json | python -m json.tool
```
Expected: JSON 파싱 성공, 오류 없음

---

## Task 2: `.claude/hooks/hooks.json` 생성

**Files:**
- Create: `.claude/hooks/hooks.json`

- [ ] **Step 1: hooks.json 작성**

기존 `.claude/settings.json` 의 hooks 설정을 manifest 형태로 문서화.

```json
{
  "schema_version": "1.0",
  "description": "Claude Code 훅 등록 manifest — settings.json의 hooks와 동기화",
  "hooks": [
    {
      "id": "protect-critical-files",
      "event": "PreToolUse",
      "matcher": "Edit|Write",
      "script": ".claude/hooks/protect-critical-files.sh",
      "description": "CLAUDE.md, settings.json 등 보호 파일 수정 차단"
    },
    {
      "id": "block-visible-windows",
      "event": "PreToolUse",
      "matcher": "Bash",
      "script": ".claude/hooks/block-visible-windows.sh",
      "description": "GUI 윈도우를 띄우는 명령 차단 (Windows headless 환경)"
    },
    {
      "id": "check-korean-only",
      "event": "PostToolUse",
      "matcher": "Edit|Write",
      "script": ".claude/hooks/check-korean-only.sh",
      "description": "파일 저장 후 한글 전용 규칙 검사"
    },
    {
      "id": "orca-heartbeat",
      "event": "PostToolUse",
      "matcher": ".*",
      "command": "bash -c 'test -d .claude && date +%Y-%m-%dT%H:%M:%S > .claude/orca-heartbeat'",
      "description": "모든 툴 사용 후 orca heartbeat 갱신 (워커 생존 신호)"
    }
  ],
  "disabled": [],
  "notes": "실제 실행 등록은 .claude/settings.json 에서 관리. 이 파일은 manifest + 문서 역할."
}
```

- [ ] **Step 2: hooks.json 파일 생성 (Write tool 사용)**

- [ ] **Step 3: 검증**

```bash
cat .claude/hooks/hooks.json | python -m json.tool
```
Expected: JSON 파싱 성공

---

## Task 3: `.claude/state/` 디렉터리 + README 생성

**Files:**
- Create: `.claude/state/.gitkeep`
- Create: `.claude/state/README.md`

- [ ] **Step 1: state 디렉터리 생성**

```bash
mkdir -p .claude/state
```

- [ ] **Step 2: .gitkeep 생성**

빈 파일로 Git 추적 보장.

- [ ] **Step 3: README.md 작성**

```markdown
# .claude/state/ — 상태 파일 저장소

## 용도
신규 상태 파일 전용 디렉터리.
기존 orca-* 플래그 파일은 하위 호환성을 위해 `.claude/` 루트에 유지.

## 파일 분류

| 파일 | 위치 | 설명 |
|------|------|------|
| `orca-enabled` | `.claude/` (루트) | 자동 시작 활성화 플래그 |
| `orca-stopped` | `.claude/` (루트) | 자동 시작 비활성화 플래그 |
| `orca-heartbeat` | `.claude/` (루트) | 마지막 활동 시각 (워커 생존 신호) |
| `orca-workers` | `.claude/` (루트) | 워커 수 설정 |

## 신규 상태 파일 (이 디렉터리 사용)
- `retry-count.json` — 재시도 횟수 추적
- `last-task-id.txt` — 마지막 처리된 태스크 ID
- `worker-status.json` — 워커별 상태 스냅샷

## 마이그레이션 계획
향후 orca-* 파일도 이 디렉터리로 이동 예정.
이동 시 CLAUDE.md + command 파일의 경로 참조 일괄 업데이트 필요.
```

- [ ] **Step 4: 파일 생성 (Write tool 사용)**

---

## Task 4: 신규 Skill — `exec_orca-auto.md` (orcauto 로직 승격)

**Files:**
- Create: `.claude/skills/exec_orca-auto.md`

기존 `.claude/commands/orcauto-start.md`, `orcauto-stop.md` 의 실제 오케스트레이션 로직을 이 skill로 이동.

- [ ] **Step 1: exec_orca-auto.md 작성**

```markdown
# exec_orca-auto — Orca Auto Worker 관리

> **분류:** exec_ (실행 계열)
> **레거시 커맨드:** /orcauto-start, /orcauto-stop

## 목적
codex-auto / gemini-auto 워커를 시작·중단·상태 조회한다.
세션 시작 시 자동 호출되며, `/orcauto-start` / `/orcauto-stop` 커맨드의 실제 로직을 담당한다.

## 상태 파일 (`.claude/` 루트 — 하위 호환 유지)

| 파일 | 의미 |
|------|------|
| `orca-enabled` | 자동 시작 활성화 |
| `orca-stopped` | 비활성화 플래그 |
| `orca-heartbeat` | 마지막 활동 시각 |
| `orca-workers` | 워커 수 (없으면 기본값 1) |

## 액션: START

```
1. orca-stopped 삭제: del .claude\orca-stopped 2>nul
2. orca-enabled 생성: echo enabled > .claude\orca-enabled
3. orca-heartbeat 갱신: date +%Y-%m-%dT%H:%M:%S > .claude/orca-heartbeat
4. 워커 수 결정:
   - .claude/orca-workers 있으면 그 값
   - 없으면 1
5. codex-auto 가용 시:
   start "Codex-Worker-1" cmd /c "cd /d %CD% && codex-auto [N]"
6. gemini-auto 가용 시:
   start "Gemini-Verifier-1" cmd /c "cd /d %CD% && gemini-auto [N]"
7. 결과 보고 (표 형식)
```

## 액션: STOP

```
1. orca-stopped 생성: echo disabled > .claude\orca-stopped
2. orca-enabled 삭제: del .claude\orca-enabled 2>nul
3. 프로세스 종료:
   powershell: Get-Process cmd | Where MainWindowTitle -match 'Codex-Worker|Gemini-Verifier' | Stop-Process -Force
4. 종료 결과 보고
```

## 액션: STATUS

```
where codex-auto → AVAILABLE / NOT FOUND
where gemini-auto → AVAILABLE / NOT FOUND
type .claude\orca-heartbeat → 마지막 갱신 시각
type .claude\orca-workers → 워커 수
```

## 자동 종료 규칙
- Claude 종료 후 5분 → heartbeat 갱신 없음 → 워커 자동 종료
- 이 규칙은 codex-auto.bat / gemini-auto.bat 내부 타임아웃으로 구현됨
```

- [ ] **Step 2: 파일 생성 (Write tool 사용)**

---

## Task 5: 신규 Skill — `state_session.md` (세션 상태 관리)

**Files:**
- Create: `.claude/skills/state_session.md`

기존 `skill-09-memory-reset.md` 의 snapshot 로직 + `check-agents.md` 의 상태 조회를 통합한 새 canonical skill.

- [ ] **Step 1: state_session.md 작성**

```markdown
# state_session — 세션 상태 관리

> **분류:** state_ (상태 저장 계열)
> **통합 레거시:** skill-09-memory-reset, check-agents command

## 목적
세션 스냅샷 저장·복구 + 에이전트 상태 조회를 단일 skill로 처리한다.

## 액션: SNAPSHOT (저장)

트리거: 컨텍스트 80% 이상, 파이프라인 단계 완료, 사용자 요청

저장 경로: `.claude/context-cache/session-snapshot.md`

```markdown
## Session Snapshot - [YYYY-MM-DD HH:MM]

### Current Task
- Title: [task title]
- Goal: [목표]
- Status: [research | implementing | reviewing | deploying]

### Completed Steps
- [x] SKILL-01 research
- [ ] SKILL-02 implement

### Next Command
codex-auto [N]  ← 또는 gemini-auto [N]

### Modified Files
- path/to/file1
- path/to/file2

### Key Decisions
- [결정 사항 1]
```

## 액션: RESTORE (복구)

트리거: 세션 시작 시 `.claude/context-cache/session-snapshot.md` 존재 확인

```
1. 파일 존재 → 요약 출력:
   [Recovery] 이전 세션 스냅샷 발견
     Task:      [title]
     Completed: [steps]
     Next:      [command]
   계속하시겠습니까?
2. 사용자 승인 → snapshot의 next command 실행
3. 파일 없음 → 조용히 스킵
```

## 액션: STATUS (에이전트 현황)

```
| Agent | 설치 | 프로세스 | 비고 |
|-------|------|---------|------|
| codex-auto  | where codex-auto | tasklist grep | ... |
| gemini-auto | where gemini-auto | tasklist grep | ... |
| claude-auto | where claude-auto | tasklist grep | ... |

pending tasks: ls .claude/tasks/task-*.md | wc -l
heartbeat: cat .claude/orca-heartbeat
```
```

- [ ] **Step 2: 파일 생성 (Write tool 사용)**

---

## Task 6: 신규 Skill — `route_dispatch.md` (AI 라우팅 판단)

**Files:**
- Create: `.claude/skills/route_dispatch.md`

기존 CLAUDE.md의 `Multi-Agent Auto-Detection` 로직 + `vibe-loop.md` 판단 로직을 skill로 승격.

- [ ] **Step 1: route_dispatch.md 작성**

```markdown
# route_dispatch — AI 라우팅 · 판단

> **분류:** route_ (라우팅/판단 계열)
> **통합 레거시:** vibe-loop command, CLAUDE.md Multi-Agent Auto-Detection

## 목적
태스크 규모와 가용 AI 도구를 자동 감지해 최적 실행 경로를 결정한다.
사용자에게 묻지 않고 자동으로 결정한다.

## 감지 순서

```
1. codex-auto 가용 확인: where codex-auto
   CODEX_AVAILABLE = true / false

2. gemini-auto 가용 확인: where gemini-auto
   GEMINI_AVAILABLE = true / false

3. 태스크 규모 판단:
   - 예상 코드 500줄+ → LARGE
   - 검증/문서/리서치 → VERIFY
   - 500줄 미만 구현 → SMALL
```

## 라우팅 결정표

| CODEX | GEMINI | 태스크 | 실행 경로 |
|-------|--------|--------|---------|
| ✅ | ✅ | LARGE | task-instruction.md → codex-auto → Claude 보완 → gemini-auto |
| ✅ | ✅ | VERIFY | task-instruction.md → gemini-auto (--verify) |
| ✅ | ❌ | LARGE | task-instruction.md → codex-auto → Claude 검증 |
| ❌ | ✅ | VERIFY | task-instruction.md → gemini-auto |
| ❌ | ❌ | ANY | Claude 직접 구현 + 검증 |

## Vibe Loop 모드 (양쪽 모두 가용 시)

```
1. .claude/tasks/stop 파일 없는지 확인
2. 터미널 안내:
   codex-auto    ← 구현 워커 (터미널 1)
   gemini-auto   ← 검증 워커 (터미널 2)
3. 중단: /loop-stop 또는 .claude/tasks/stop 파일 생성
```

## 단독 모드 (codex-auto만 가용)

```
codex-auto 1   ← 단일 워커
Claude가 검증 담당
```

## 직접 모드 (둘 다 없음)

```
Claude가 구현 + 검증 모두 직접 처리
task-instruction.md 불필요
```
```

- [ ] **Step 2: 파일 생성 (Write tool 사용)**

---

## Task 7: Commands 슬림화 — wrapper로 교체

**Files:**
- Modify: `.claude/commands/orcauto-start.md`
- Modify: `.claude/commands/orcauto-stop.md`
- Modify: `.claude/commands/vibe-loop.md`
- Modify: `.claude/commands/check-agents.md`

기존 로직을 제거하고 해당 skill을 참조하는 wrapper만 남긴다.

- [ ] **Step 1: orcauto-start.md 슬림화**

```markdown
---
description: codex-auto / gemini-auto 자동 시작 활성화 + 지금 즉시 워커 시작
allowed-tools: Bash(where:*), Bash(echo:*), Bash(del:*), Bash(powershell:*), Bash(start:*)
---

> **[Wrapper]** 실제 로직: `.claude/skills/exec_orca-auto.md` (exec_orca-auto)

## Context

- codex-auto 가용: !`where codex-auto 2>nul && echo YES || echo NO`
- gemini-auto 가용: !`where gemini-auto 2>nul && echo YES || echo NO`
- orca-stopped 플래그: !`if exist .claude\orca-stopped (echo STOPPED) else (echo OK)`
- 워커 수 설정: !`if exist .claude\orca-workers (type .claude\orca-workers) else (echo 1)`

## Your task

`exec_orca-auto` skill의 **START 액션**을 실행한다.
상세 로직: `.claude/skills/exec_orca-auto.md` 참조.
```

- [ ] **Step 2: orcauto-stop.md 슬림화**

```markdown
---
description: codex-auto / gemini-auto 자동 시작 비활성화 + 실행 중인 워커 종료
allowed-tools: Bash(powershell:*), Bash(echo:*)
---

> **[Wrapper]** 실제 로직: `.claude/skills/exec_orca-auto.md` (exec_orca-auto)

## Your task

`exec_orca-auto` skill의 **STOP 액션**을 실행한다.
상세 로직: `.claude/skills/exec_orca-auto.md` 참조.
```

- [ ] **Step 3: vibe-loop.md 슬림화**

```markdown
---
description: Vibe Coding 멀티에이전트 루프 시작 — codex-auto/gemini-auto 가용 여부 자동 감지 후 루프 시작
allowed-tools: Bash(where:*), Bash(powershell:*)
---

> **[Wrapper]** 실제 로직: `.claude/skills/route_dispatch.md` (route_dispatch)

## Context

- codex-auto available: !`where codex-auto 2>/dev/null && echo YES || echo NO`
- gemini-auto available: !`where gemini-auto 2>/dev/null && echo YES || echo NO`
- current tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | head -10 || echo "(none)"`
- stop file exists: !`ls .claude/tasks/stop 2>/dev/null && echo YES || echo NO`

## Your task

`route_dispatch` skill의 **Vibe Loop 모드**를 실행한다.
가용 도구를 자동 감지해 최적 루프를 시작한다.
상세 로직: `.claude/skills/route_dispatch.md` 참조.
```

- [ ] **Step 4: check-agents.md 슬림화**

```markdown
---
description: codex-auto / gemini-auto / claude-auto 가용 여부 + 실행 중인 작업 현황 확인
allowed-tools: Bash(where:*), Bash(powershell:*), Bash(tasklist:*)
---

> **[Wrapper]** 실제 로직: `.claude/skills/state_session.md` (state_session)

## Context

- codex-auto: !`where codex-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- gemini-auto: !`where gemini-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- claude-auto: !`where claude-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- pending tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | wc -l || echo 0`
- heartbeat: !`cat .claude/orca-heartbeat 2>/dev/null || echo "no heartbeat"`

## Your task

`state_session` skill의 **STATUS 액션**을 실행한다.
상세 로직: `.claude/skills/state_session.md` 참조.
```

- [ ] **Step 5: 각 command의 로직이 skill 참조로 대체되었는지 확인**

---

## Task 8: `migration-map.md` 작성

**Files:**
- Create: `.claude-plugin/docs/migration-map.md`

- [ ] **Step 1: migration-map.md 작성**

전체 old→new 매핑 테이블 포함.

- [ ] **Step 2: 파일 생성 (Write tool 사용)**

---

## Task 9: CLAUDE.md Loading Order 업데이트

**Files:**
- Modify: `CLAUDE.md`

새 skill 3개를 Loading Order 섹션에 추가.

- [ ] **Step 1: Loading Order에 신규 skill 추가**

기존 `.claude/skills/skill-38-token-watchdog.md` 뒤에 추가:
```
.claude/skills/exec_orca-auto.md
.claude/skills/state_session.md
.claude/skills/route_dispatch.md
```

- [ ] **Step 2: plugin.json 경로도 언급 (참조용)**

- [ ] **Step 3: 변경 후 로딩 순서 검증 (파일 존재 확인)**

```bash
for f in exec_orca-auto state_session route_dispatch; do
  ls .claude/skills/${f}.md && echo "OK: $f"
done
```

---

## Task 10: 커밋

- [ ] **Step 1: 변경 파일 스테이징**

```bash
git add .claude-plugin/ .claude/hooks/hooks.json .claude/state/ \
        .claude/skills/exec_orca-auto.md \
        .claude/skills/state_session.md \
        .claude/skills/route_dispatch.md \
        .claude/commands/orcauto-start.md \
        .claude/commands/orcauto-stop.md \
        .claude/commands/vibe-loop.md \
        .claude/commands/check-agents.md \
        CLAUDE.md
```

- [ ] **Step 2: 커밋**

```bash
git commit -m "feat: plugin-centric 구조 도입 — plugin.json + hooks.json + 신규 skills 3개 + command wrapper 슬림화"
```

- [ ] **Step 3: 최종 검증**

```bash
git log --oneline -3
git show --stat HEAD
```

---

## 깨질 수 있는 부분 & 수동 확인 포인트

| 위험 | 원인 | 확인 방법 | 대처 |
|------|------|---------|------|
| orcauto-start/stop 동작 변화 | command가 skill 참조 wrapper로 교체됨 | `/orcauto-start` 실행 후 워커 시작 확인 | exec_orca-auto.md 내용 확인 |
| check-agents 출력 형식 변화 | state_session 통합 후 포맷 차이 | `/check-agents` 실행 후 표 형식 확인 | state_session.md STATUS 섹션 수정 |
| CLAUDE.md Loading Order 순서 | 신규 파일 추가 위치 | 목록 끝 3줄 추가로 기존 순서 미영향 | 별도 조치 불필요 |
| settings.json hooks 경로 | 기존 경로 `.claude/hooks/` 유지 | hooks.json은 manifest 전용 (실행 미영향) | 별도 조치 불필요 |
| state/ 디렉터리 빈 파일 | .gitkeep으로 추적됨 | git status 확인 | 별도 조치 불필요 |
