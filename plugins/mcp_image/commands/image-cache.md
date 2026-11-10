---
description: "이미지 캐시 관리 — list / stats / clean"
allowed-tools: Bash(python:*)
---

## Context

캐시 통계:
!`PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=([pathlib.Path(e)] if e else [])+[w,*w.parents];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" lib/pollinations_client.py --stats`

## Your task

입력 `$ARGUMENTS`:
- 비었거나 `list` → 최근 20개 list
- `stats` → 통계만 (위 Context 에 이미)
- `clean <days>` → N일+ 캐시 삭제

기본 동작:
```bash
PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=([pathlib.Path(e)] if e else [])+[w,*w.parents];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" lib/pollinations_client.py --list
```

## 위치

- 이미지: `docs/screens/custom/<keyword>-<hash>.jpg`
- 메타: `.claude/state/image-cache/<keyword>-<hash>.json`
- 자동 정리: cleanup-pollution.sh (image-cache *.json 7일+)
