---
description: "세션 학습·실패 패턴·최적화 규칙 축적"
---

# /exec_learning — 학습 메모리 허브

## 포함 커맨드
- `/learn` — 현재 세션에서 배운 것을 패턴으로 저장
- `/recall` — 과거 학습 결과 불러오기
- `/summarize` — 세션 요약 생성

## 저장 위치
- `.claude/learning/failure-patterns.json`
- `.claude/learning/optimization-rules.json`

## 기본 실행
`/learn` — 현 세션의 성공·실패 패턴을 추출해 다음 세션에 반영.
