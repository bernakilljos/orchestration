---
description: "대기 중인 위험 task 승인 — `/approve <task_id>` (사용자가 직접 입력할 때만 기록)"
allowed-tools: Bash(python:*)
---

## Context

대기 중인 승인 list:
!`PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" list`

## Your task

입력 `$ARGUMENTS` = task_id.

승인 기록은 **이미 끝났거나 거절됐다** — 사용자가 이 명령을 입력한 순간 UserPromptSubmit 훅
(`.claude/hooks/prompt/user_approval.py`) 이 기록한다. Claude 는 승인 명령을 실행하지 않는다
(명령줄 승인은 비활성 · 도구 호출로 부르면 차단).

1. 훅 메시지 `[사용자 승인] ...` 를 그대로 보고 (승인됨 / 처리 안 됨 + 사유).
2. 상태 확인만: `PYTHONIOENCODING=utf-8 python "$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py" status <task_id>`
3. task_id 가 없거나 처리 안 됨이면 list 를 보여 주고, 사용자가 `/approve <id>` 를 다시 입력하도록 안내. 대신 승인하지 않는다.
4. 승인된 `appr-*` 는 같은 명령을 같은 폴더에서 30분 안에 **1회** 실행할 수 있다. `push-*` 는 워커 push-approved 가 처리.

## 사용 예

```text
/approve appr-1a2b3c4d5e6f
→ [사용자 승인] appr-1a2b3c4d5e6f 승인 기록됨 → 같은 명령 1회 실행
```
