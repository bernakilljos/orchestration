---
description: "세션 학습 저장 — 성공·실패 패턴을 JSON에 기록"
allowed-tools: Bash(python:*), Read, Write
---

## Context
- 실패 패턴 수: !`python -c "import json; d=json.load(open('.claude/learning/failure-patterns.json')); print(len(d.get('patterns',[])), '개')" 2>/dev/null || echo 0개`
- 최적화 규칙 수: !`python -c "import json; d=json.load(open('.claude/learning/optimization-rules.json')); print(len(d.get('rules',[])), '개')" 2>/dev/null || echo 0개`

## Your task

입력: `$ARGUMENTS` (학습 내용 또는 "이번 세션 요약")

### Step 1 — 분류
입력 내용을 분석해서:
- **실패 패턴**: 오류, 반복 실수, 잘못된 접근 → `failure-patterns.json`
- **최적화 규칙**: 효율적인 방법, 성공 패턴 → `optimization-rules.json`

### Step 2 — failure-patterns.json 업데이트 (해당 시)
```json
{
  "patterns": [
    {
      "id": "FP-NNN",
      "category": "코드/설계/배포/MCP",
      "trigger": "어떤 상황에서 발생",
      "symptom": "어떤 증상",
      "root_cause": "원인",
      "fix": "해결 방법",
      "prevention": "예방 방법",
      "date": "YYYY-MM-DD",
      "count": 1
    }
  ]
}
```

### Step 3 — optimization-rules.json 업데이트 (해당 시)
```json
{
  "rules": [
    {
      "id": "OR-NNN",
      "category": "속도/품질/토큰/구조",
      "context": "어떤 상황에서 적용",
      "rule": "규칙 내용",
      "reason": "효과",
      "date": "YYYY-MM-DD",
      "usage_count": 0
    }
  ]
}
```

### Step 4 — 결과 보고
추가된 패턴/규칙 수, 총 누적 수, 주요 내용 요약
