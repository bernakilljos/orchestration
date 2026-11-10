---
description: "대기 중인 모든 승인 task 한 눈에 — 위험 카테고리·age·명령 preview"
allowed-tools: Bash(python:*)
---

## Context

전체 대기 list:
!`PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=[p for p in ([pathlib.Path(e)] if e else [])+[w,*w.parents] if not any(a=='.claude' and b=='backups' for a,b in zip(p.parts,p.parts[1:]))];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" approval-gate.py list`

## Your task

위 JSON 을 한글 표로 보고:

| task_id | 위험 카테고리 | age (분) | 명령 preview |
|---|---|---|---|

각 row 별로 `/approve <id>` / `/reject <id>` 권장.

대기 0건이면 "현재 대기 중 승인 없음. 시스템 정상."

## 위험 카테고리

| category | 의미 |
|---|---|
| **data_loss** | DROP TABLE / TRUNCATE / rm -rf / force push |
| **security** | sudo / curl \| bash / runas / setuid |
| **cost** | Batch API 1000+ / daily limit 100+ USD |
| **system** | setx / registry / DB migration / systemctl |
| **irreversible** | npm publish / docker push prod / gh release / terraform apply |
