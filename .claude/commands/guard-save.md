# /guard-save — 즉시 스냅샷 저장

## 목적
사용자가 명시적으로 "지금 상태 저장" 요청할 때 실행.
토큰 여유 있을 때 방어적으로 저장해두면 이후 소진되어도 안전.

## 실행
1. `plugins/exec_session_guard/skills/guard_snapshot.md` 의 SAVE 액션 수행
2. 저장 완료 후 1줄로 결과 보고: `[guard-save] saved at HH:MM — next: <Next Command>`

## 인자
없음. 현재 컨텍스트에서 모든 정보 추출.

## 금지
- 확인 질문 없이 즉시 저장 (사용자가 이미 요청했으므로)
- 스냅샷 전체 내용 출력 금지 (파일 경로만 안내)
