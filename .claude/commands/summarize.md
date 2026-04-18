---
description: "세션 요약 + 학습 데이터 자동 생성 — 대화 끝날 때 실행"
allowed-tools: Bash(python:*), Read, Write
---

## Context
- 세션 스냅샷: !`cat .claude/context-cache/session-snapshot.md 2>/dev/null | head -20 || echo 없음`
- 오늘 커밋: !`git log --oneline --since="today" 2>/dev/null | head -10 || echo 없음`
- 실패 패턴 수: !`python -c "import json; d=json.load(open('.claude/learning/failure-patterns.json')); print(len(d.get('patterns',[])))" 2>/dev/null || echo 0`

## Your task

### Step 1 — 세션 요약 작성
오늘 작업 내용을 아래 형식으로 요약:

```markdown
## 세션 요약 — YYYY-MM-DD

### 완료한 작업
- ...

### 배운 것
- ...

### 다음에 할 것
- ...

### 주의사항
- ...
```

### Step 2 — 학습 데이터 추출
요약에서 자동으로:
- 반복된 실수 → `/learn` 호출해서 failure-patterns.json 저장
- 효율적이었던 방법 → optimization-rules.json 저장

### Step 3 — session-snapshot.md 업데이트
다음 세션에서 바로 이어받을 수 있도록:
```
.claude/context-cache/session-snapshot.md 업데이트
  - 다음 실행할 명령
  - 미완성 태스크
  - 중요 결정 사항
```

### Step 4 — 결과 보고
요약 저장 경로, 학습 데이터 추가 수, 다음 세션 시작점
