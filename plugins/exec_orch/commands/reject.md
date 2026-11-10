---
description: "대기 중인 위험 task 거부 — `/reject <task_id> [reason]` (사용자가 직접 입력할 때만 기록)"
allowed-tools: Bash(python:*)
---

## Context

대기 중인 승인 list:
!`PYTHONIOENCODING=utf-8 python "${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/approval-gate.py" list`

## Your task

입력 `$ARGUMENTS` = `<task_id> [reason]`.

거부 기록은 사용자가 이 명령을 입력한 순간 UserPromptSubmit 훅 (`.claude/hooks/prompt/user_approval.py`) 이 한다.
Claude 는 거부 명령을 실행하지 않는다 (명령줄 거부 비활성 · 도구 호출로 부르면 차단).

1. 훅 메시지 `[사용자 승인] ... 거부 기록됨` 또는 처리 안 됨 사유를 보고.
2. 상태 확인만: `PYTHONIOENCODING=utf-8 python "${CLAUDE_PROJECT_DIR:-.}/.claude/scripts/approval-gate.py" status <task_id>`

## 사용 예

```text
/reject appr-1a2b3c4d5e6f force push 위험 너무 큼
→ rejected by user-prompt, reason: "force push 위험 너무 큼"
```
