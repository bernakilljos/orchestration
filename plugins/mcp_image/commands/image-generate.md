---
description: "Pollinations.ai 무료 이미지 생성 — `/image-generate \"<prompt>\" [keyword] [cluster]`"
allowed-tools: Bash(python:*)
---

## Your task

입력 `$ARGUMENTS` = `"<prompt>" [keyword] [cluster]`

1. prompt 추출 (큰따옴표 안)
2. keyword 옵션 (없으면 prompt 첫 5단어로 자동)
3. cluster 옵션: warm-editorial / dark-minimal / corporate-blue / neon-acid / colorful

```bash
PYTHONIOENCODING=utf-8 python -c "import os,sys,pathlib,subprocess as s;n=sys.argv[1];e=os.environ.get('CLAUDE_PROJECT_DIR','');w=pathlib.Path.cwd();c=([pathlib.Path(e)] if e else [])+[w,*w.parents];g=next((p/'.claude'/'scripts'/n for p in c if (p/'.claude'/'scripts'/n).is_file()),None);g or sys.exit('[오류] 프로젝트 루트를 찾지 못했습니다: .claude/scripts/'+n+' 없음 (CLAUDE_PROJECT_DIR='+repr(e)+', 현재 폴더='+str(w)+') - 다른 폴더로 접근하지 않고 중단');sys.exit(s.call([sys.executable,str(g),*sys.argv[2:]]))" lib/pollinations_client.py $ARGUMENTS
```

결과:
- `docs/screens/custom/<keyword>-<hash>.jpg` 생성
- 사이즈·경로 보고

## 예시

```text
/image-generate "cute giraffe, flat design" giraffe warm-editorial
→ docs/screens/custom/giraffe-3df77c16.jpg  29KB

/image-generate "minimal dashboard mockup" dashboard dark-minimal
→ docs/screens/custom/dashboard-<hash>.jpg

/image-generate "코딩하는 5살 아이, 친근한 일러스트" 5살-비유
→ docs/screens/custom/5sal-biyu-<hash>.jpg
```

## 메모

- 시간: 5-30 초 (flux 모델)
- 비용: $0 (Pollinations.ai 무료)
- 재호출 시 캐시 적중 = 즉시
