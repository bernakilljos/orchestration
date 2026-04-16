---
description: codex-auto / gemini-auto / claude-auto 가용 여부 + 실행 중인 작업 현황 확인
allowed-tools: Bash(where:*), Bash(powershell:*), Bash(tasklist:*)
---

## Context

- codex-auto: !`where codex-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- gemini-auto: !`where gemini-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- claude-auto: !`where claude-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- codex processes: !`tasklist 2>/dev/null | grep -ic "codex" || echo 0`
- gemini processes: !`tasklist 2>/dev/null | grep -ic "gemini" || echo 0`
- claude processes: !`tasklist 2>/dev/null | grep -ic "claude" | head -1 || echo 0`
- pending tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | wc -l || echo 0`
- locked tasks: !`ls .claude/tasks/locks/*.lock 2>/dev/null | wc -l || echo 0`
- completed tasks: !`ls .claude/tasks/done/*.md 2>/dev/null | wc -l || echo 0`
- stop signal: !`ls .claude/tasks/stop 2>/dev/null && echo STOP ACTIVE || echo running`
- heartbeat: !`cat .claude/orca-heartbeat 2>/dev/null || echo "no heartbeat"`
- orca-workers: !`cat .claude/orca-workers 2>/dev/null || echo "default (10)"`

> **[Wrapper]** 실제 로직: `.claude/skills/state_session.md` (`state_session` · STATUS 액션)

## Your task

`state_session` skill의 **STATUS 액션**을 실행한다.
에이전트 가용 여부, 실행 중인 태스크 현황, heartbeat 상태를 표로 출력한다.
자세한 실행 절차는 `.claude/skills/state_session.md` 참조.
