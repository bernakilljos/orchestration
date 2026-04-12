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

## Your task

Report the status in a clean table format:

| Agent | 설치 | 프로세스 | 비고 |
|-------|------|---------|------|
| codex-auto | ... | N개 실행 중 | ... |
| gemini-auto | ... | N개 실행 중 | ... |
| claude-auto | ... | N개 실행 중 | ... |

Then show:
- Task stats (대기/실행/완료)
- Heartbeat 시각 (마지막 갱신)
- Worker 설정값

Recommendations:
- agents available + tasks pending → "vibe-loop 시작 권장: /vibe-loop"
- no agents → "Claude 직접 처리 모드"
- stop signal active → "루프 중단 상태 — 재시작: /vibe-loop"
- process 0개인데 lock 있으면 → "stale lock 감지 — 정리 필요"
- heartbeat 5분+ 전이면 → "heartbeat 오래됨 — 워커 종료되었을 수 있음"
