---
description: "대기 중인 위험 task 거부 — `/reject <task_id> [reason]`"
allowed-tools: Bash(python:*)
---

## Context

대기 중인 승인 list:
!`PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" list`

## Your task

입력 `$ARGUMENTS` = `<task_id> [reason]`.

1. task_id 없으면 list 에서 선택 안내.
2. task_id + reason 있으면:
   ```bash
   PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" reject <task_id> user "<reason>"
   ```
3. 결과 보고 — rejected state · reason 기록.
4. rejected task 는 status=cancelled 로 archive.

## 사용 예

```text
/reject 42 force push 위험 너무 큼
→ task_id 42 rejected by user, reason: "force push 위험 너무 큼"
```
