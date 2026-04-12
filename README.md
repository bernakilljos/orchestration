# Orchestration Kit v3 - Multi-AI Automation Framework

Claude(Team Lead) + Codex(Implementation) + Gemini(Review) — 3 AI 역할 분담 오케스트레이션

---

## Quick Start

### 방법 1: setup.exe (추천)
[Releases](https://github.com/bernakilljos/orchestration/releases) 에서 **OrchestrationKit-Setup.exe** 다운로드 → 더블클릭 → 경로 선택 → 설치 끝

### 방법 2: git clone
```bat
git clone https://github.com/bernakilljos/orchestration.git
cd orchestration
setup\setup.bat C:\work\myproject
```

### 방법 3: 사일런트 설치
```bat
OrchestrationKit-Setup.exe /VERYSILENT /DIR="C:\work\myproject"
```

### 설치 후
Claude Code 실행 → 자동으로 환경 구성 완료

---

## 포함 항목

| 카테고리 | 수량 | 내용 |
|---------|------|------|
| Skills | 25개 | research, implement, review, deploy, test, design, theme-factory, brand-guidelines, debugging-canvas, web-artifacts, skill-creator, claude-seo, marketing, remotion, owasp-security, ai-handoff, media-enhance 등 |
| Hooks | 8개 | init, pre-task, post-impl, post-review, pre-deploy, post-deploy, notify, layout-lock, ai-handoff |
| Agents | 6개 | team-lead, implementer, reviewer, architect, monitor, designer |
| Plugins | 8개 | superpowers, ui-ux-pro-max, everything-claude-code, awesome-claude-code, get-shit-done, code-review, commit-commands, claude-md-management |
| MCP | 7+6개 | context7, playwright, thinking, gemini, excel, n8n, light-rag + Figma, Gamma, Gmail, Calendar, HuggingFace, Mermaid |
| Tools | 2개 | video-restore (CodeFormer+Real-ESRGAN), media-enhance (동영상/오디오/이미지/PDF/PPT) |
| Advisor | Sonnet+Opus | claude-auto에서 자동 사용 |

---

## AI Roles

| AI | Role | How |
|----|------|-----|
| Claude | Team Lead: design, judge, approve, 보완/고도화 | Direct in session |
| Codex | Implementer: 500+ line 1차 구현 | `codex-a --auto` |
| Gemini | Reviewer: verify, search, docs | `gemini-a --verify` |

### Handoff Protocol (강제)
```
Claude → task-instruction.md + handoff-log.md → Codex
Codex  → implementation-report.md → Claude (보완)
Claude → verify-*.md → Gemini
Gemini → review-result.md → Claude (채택/수정)
```

---

## Pipeline

```
Request → init → research → team-lead → task-instruction.md
  → Codex 1차 구현 → Claude 보완 → Gemini 검증
  → Claude 채택 → deploy → monitor
```

---

## Setup Modules (11단계)

| # | Module | 내용 |
|---|--------|------|
| 01 | core | .claude 폴더 + CLAUDE.md 복사 |
| 02 | defender | Windows Defender 예외 |
| 03 | settings | Claude 글로벌 설정, PS UTF-8 |
| 04 | commands | codex-a, gemini-a 글로벌 설치 |
| 05 | services | status-push, remote-agent |
| 06 | prereqs | Node.js, Claude Code, Cloudflared |
| 07 | github | Git 초기화, GitHub repo 생성 |
| 08 | plugins | 플러그인 8개 자동 설치 |
| 09 | finalize | init, npm install, Claude 실행 |
| 10 | video-restore | CodeFormer + Real-ESRGAN |
| 11 | media-enhance | 오디오/PDF/PPT 의존성 |

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `codex-a --auto` | Codex가 task-instruction.md 읽어서 구현 |
| `gemini-a --verify` | Gemini가 구현 결과 검증 |
| `claude-auto` | Claude 병렬 워커 (Sonnet + Opus advisor) |
| `codex-auto N` | Codex N개 병렬 워커 |
| `gemini-auto N` | Gemini N개 병렬 워커 |

---

## Extend

```
New skill:  .claude/skills/skill-26-name.md
New agent:  .claude/agents/agent-07-name.md
New hook:   .claude/hooks/hook-09-name.md
→ CLAUDE.md Loading Order에 추가
```
