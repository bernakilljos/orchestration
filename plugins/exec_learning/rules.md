# exec_learning 플러그인 규칙

## 목적
세션에서 배운 것을 저장·요약·재활용.
실패 패턴과 최적화 규칙을 축적해서 다음 작업에 반영.

## 학습 저장 위치
- 실패 패턴: `.claude/learning/failure-patterns.json`
- 최적화 규칙: `.claude/learning/optimization-rules.json`
- 세션 스냅샷: `.claude/context-cache/session-snapshot.md`

## 파이프라인
```
작업 완료 / 오류 발생
  → 패턴 분석 (Claude)
  → failure-patterns.json 또는 optimization-rules.json 업데이트
  → 다음 세션 시작 시 자동 로드 → 같은 실수 방지
```

## 규칙
- 학습 데이터는 JSON 형식 유지
- 개인정보·API키 저장 금지
- 오래된 패턴 (30일 이상 미사용) 자동 정리
