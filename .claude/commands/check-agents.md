---
description: codex-auto / gemini-auto / claude-auto 가용 여부 + 실행 중인 작업 현황 확인
allowed-tools: Bash(where:*), Bash(powershell:*)
---

## Context

- codex-auto: !`where codex-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- gemini-auto: !`where gemini-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- claude-auto: !`where claude-auto 2>/dev/null && echo AVAILABLE || echo NOT FOUND`
- pending tasks: !`ls .claude/tasks/task-*.md 2>/dev/null | wc -l || echo 0`
- locked tasks: !`ls .claude/tasks/locks/*.lock 2>/dev/null | wc -l || echo 0`
- completed tasks: !`ls .claude/tasks/done/*.md 2>/dev/null | wc -l || echo 0`
- stop signal: !`ls .claude/tasks/stop 2>/dev/null && echo STOP ACTIVE || echo running`

## Your task

Report the status in a clean table format:

| Agent | 상태 | 비고 |
|-------|------|------|
| codex-auto | ... | ... |
| gemini-auto | ... | ... |
| claude-auto | ... | ... |

Then show task stats and give a recommendation:
- If agents available + tasks pending → "vibe-loop 시작 권장: /vibe-loop"
- If no agents → "Claude 직접 처리 모드"
- If stop signal active → "루프 중단 상태 — 재시작: /vibe-loop"
