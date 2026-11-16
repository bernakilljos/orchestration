# task-r275-review-push-regex — 원장 강제 push 정규식 독립 검토 (읽기 전용)

## 1. Role
너는 보안 리뷰어다. 구현을 승인하는 것이 아니라 틀린 부분을 찾는 것이 목적이다.

## 2. Context
- 파일: `.claude/hooks/prompt/ledger_auto_register.py` 의 `_RISK_REGEX` 첫 항목 (`"git push --force"`).
- 정책: 일반 push(예: `git push`, `git push origin main`, `git push -u origin feature`)는 승인 사유가 아니다.
  강제 push·원격 브랜치 삭제·mirror·--all·`+refspec`·`:branch` 는 승인 사유여야 한다.
- 입력 문자열은 소문자로 바뀐 사용자 문장 전체다 (여러 줄 가능).

## 3. Files (allow-list)
- 읽기만: `.claude/hooks/prompt/ledger_auto_register.py`
- 수정 금지: 모든 파일

## 4. Acceptance criteria
- 놓치는 강제·삭제 push 표현(거짓 음성)이 있으면 구체 문자열로 제시
- 일반 push 를 잘못 잡는 표현(거짓 양성)이 있으면 구체 문자열로 제시
- 없으면 "발견 없음"

## 5. Reasoning
정규식을 직접 읽고 각 대체 분기를 하나씩 판단한다.

## 6. Negative constraints
- 파일을 수정하지 마라 · 명령을 실행하지 마라 · 추측을 사실처럼 쓰지 마라

## 8. 완료 검증
읽기 전용 검토 — 변경 0 이 정상.

## 9. Confidence
각 지적마다 확신도 0~10.

## 출력
한국어 10줄 이내.
