# exec_learning — Codex 지시서

## Codex 역할
학습 데이터 JSON 파일 읽기·업데이트.
Python으로 failure-patterns.json / optimization-rules.json 파싱 및 저장.

## 처리 순서
1. task-instruction.md 에서 학습할 내용 확인
2. 기존 JSON 읽기
3. 새 패턴/규칙 추가 (중복 체크)
4. JSON 저장
5. 완료 보고

## 파일 경로
- `.claude/learning/failure-patterns.json`
- `.claude/learning/optimization-rules.json`
- `.claude/context-cache/session-snapshot.md`
