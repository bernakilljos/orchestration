---
description: codex-auto / gemini-auto 자동 시작 활성화 + 지금 즉시 워커 시작
allowed-tools: Bash(where:*), Bash(echo:*), Bash(del:*), Bash(powershell:*), Bash(start:*)
---

## Context

- codex-auto 가용: !`where codex-auto 2>nul && echo YES || echo NO`
- gemini-auto 가용: !`where gemini-auto 2>nul && echo YES || echo NO`
- orca-stopped 플래그: !`if exist .claude\orca-stopped (echo STOPPED) else (echo OK)`
- 워커 수 설정: !`if exist .claude\orca-workers (type .claude\orca-workers) else (echo 1)`

> **[Wrapper]** 실제 로직: `.claude/skills/exec_orca-auto.md` (`exec_orca-auto` · START 액션)

## Your task

`exec_orca-auto` skill의 **START 액션**을 실행한다.
자세한 실행 절차는 `.claude/skills/exec_orca-auto.md` 참조.
