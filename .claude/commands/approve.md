---
description: "대기 중인 위험 task 승인 — `/approve <task_id>`"
allowed-tools: Bash(python:*)
---

## Context

대기 중인 승인 list:
!`PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" list`

## Your task

입력 `$ARGUMENTS` = task_id.

1. task_id 없으면 위 list 에서 가장 오래된 거 자동 선택 후 사용자에게 확인.
2. task_id 있으면:
   ```bash
   PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" approve $ARGUMENTS
   ```
3. 결과 보고 — risk_category · risk_detail · 다음 실행 작업.
4. approved 후 그 task 실제 실행 (router 가 받음).

## 사용 예

```text
/approve 42
→ task_id 42 (data_loss / git push --force) 승인 완료 by user
→ 자동 실행 시작
```
