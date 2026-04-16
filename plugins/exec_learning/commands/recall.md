---
description: "학습 데이터 조회 — 관련 실패 패턴·최적화 규칙 검색"
allowed-tools: Bash(python:*), Read
---

## Context
- 실패 패턴: !`python -c "import json; d=json.load(open('.claude/learning/failure-patterns.json')); [print(p['id'],'-',p['trigger']) for p in d.get('patterns',[])[-5:]]" 2>/dev/null || echo 없음`
- 최적화 규칙: !`python -c "import json; d=json.load(open('.claude/learning/optimization-rules.json')); [print(r['id'],'-',r['rule'][:50]) for r in d.get('rules',[])[-5:]]" 2>/dev/null || echo 없음`

## Your task

### 검색
`$ARGUMENTS` 키워드로 관련 패턴·규칙 검색.

```python
import json

keyword = "$ARGUMENTS".lower()

# failure-patterns.json 검색
with open(".claude/learning/failure-patterns.json", encoding="utf-8") as f:
    fp = json.load(f)

matches_fp = [p for p in fp.get("patterns", [])
              if keyword in str(p).lower()]

# optimization-rules.json 검색
with open(".claude/learning/optimization-rules.json", encoding="utf-8") as f:
    op = json.load(f)

matches_op = [r for r in op.get("rules", [])
              if keyword in str(r).lower()]

print(f"실패 패턴: {len(matches_fp)}개")
for p in matches_fp:
    print(f"  {p['id']} - {p['trigger']}")
    print(f"  → 해결: {p['fix']}")

print(f"최적화 규칙: {len(matches_op)}개")
for r in matches_op:
    print(f"  {r['id']} - {r['rule']}")
```

### 결과
관련 패턴·규칙 목록 + 이번 작업에 적용 방법 제안
