---
description: Vibe Coding 멀티에이전트 루프 시작 — codex-auto/gemini-auto 가용 여부 자동 감지 후 루프 시작
allowed-tools: Bash(where:*), Bash(powershell:*)
---

## Context

- codex-auto available: !`where codex-auto 2>/dev/null && echo YES || echo NO`
- gemini-auto available: !`where gemini-auto 2>/dev/null && echo YES || echo NO`
- current tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | head -10 || echo "(none)"`
- stop file exists: !`ls .claude/tasks/stop 2>/dev/null && echo YES || echo NO`

## Your task

Check the context above and decide:

**IF both codex-auto AND gemini-auto are available:**
- Remove stop file if it exists: `del .claude\tasks\stop`
- Inform user: "codex-auto + gemini-auto 루프를 시작합니다. 터미널 두 개를 열어 각각 실행하세요:"
  ```
  codex-auto    ← 구현 워커
  gemini-auto   ← 검증 워커
  ```
- Remind: 중단하려면 `/loop-stop` 또는 `.claude\tasks\stop` 파일 생성

**IF only codex-auto available:**
- Inform user: "codex-auto만 사용 가능합니다. gemini 검증은 Claude가 직접 수행합니다."
- Start loop: run `codex-auto 1` (single worker)

**IF neither available:**
- Inform user: "멀티에이전트 도구 없음 → Claude가 직접 모든 작업을 순차 처리합니다."
- Ask user for the first task to start

Do NOT ask the user for permission — decide automatically based on availability.
