# exec_orch — Codex 지시서

## Codex 역할 (이 플러그인에서)
- task-instruction.md 읽고 코드 구현
- 워커 병렬 실행 (codex-auto 모드)
- 완료 후 `.claude/tasks/done/` 이동

## 태스크 처리 순서
1. `.claude/tasks/task-*.md` 에서 미잠금 태스크 선택
2. `.claude/tasks/locks/TASK-NAME.lock` 생성
3. task 파일의 `## Files:` 섹션 확인 → 해당 파일만 수정
4. `## Rules:` 준수
5. 완료 → `.claude/tasks/done/` 이동, lock 삭제
6. 완료 보고서 작성

## MCP (이 플러그인)
`.codex/config.toml` 의 기본 3개 사용.
추가 불필요.

## 금지
- 태스크에 없는 파일 수정
- lock 없이 태스크 시작
- Claude 설계 결정 임의 변경
