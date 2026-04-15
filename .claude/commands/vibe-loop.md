---
description: Vibe Coding 멀티에이전트 루프 시작 — codex-auto/gemini-auto 가용 여부 자동 감지 후 루프 시작
allowed-tools: Bash(where:*), Bash(powershell:*)
---

## Context

- codex-auto available: !`where codex-auto 2>/dev/null && echo YES || echo NO`
- gemini-auto available: !`where gemini-auto 2>/dev/null && echo YES || echo NO`
- current tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | head -10 || echo "(none)"`
- stop file exists: !`ls .claude/tasks/stop 2>/dev/null && echo YES || echo NO`

> **[Wrapper]** 실제 로직: `.claude/skills/route_dispatch.md` (`route_dispatch` · Vibe Loop 모드)

## Your task

`route_dispatch` skill의 **Vibe Loop 모드**를 실행한다.
가용 도구를 자동 감지해 최적 루프를 시작한다.
자세한 실행 절차는 `.claude/skills/route_dispatch.md` 참조.
