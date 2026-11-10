---
description: "대기 중인 위험 task 거부 — `/reject <task_id> [reason]` (사용자가 직접 입력할 때만 기록)"
allowed-tools: Bash(python:*)
---

## Context

대기 중인 승인 list:
!`PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=([pathlib.Path(e)] if e else [])+[w,*w.parents];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" approval-gate.py list`

## Your task

입력 `$ARGUMENTS` = `<task_id> [reason]`.

거부 기록은 사용자가 이 명령을 입력한 순간 UserPromptSubmit 훅 (`.claude/hooks/prompt/user_approval.py`) 이 한다.
Claude 는 거부 명령을 실행하지 않는다 (명령줄 거부 비활성 · 도구 호출로 부르면 차단).

1. 훅 메시지 `[사용자 승인] ... 거부 기록됨` 또는 처리 안 됨 사유를 보고.
2. 상태 확인만: `PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=([pathlib.Path(e)] if e else [])+[w,*w.parents];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" approval-gate.py status <task_id>`

## 사용 예

```text
/reject appr-1a2b3c4d5e6f force push 위험 너무 큼
→ rejected by user-prompt, reason: "force push 위험 너무 큼"
```
