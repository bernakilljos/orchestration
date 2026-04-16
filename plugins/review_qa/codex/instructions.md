# review_qa — Codex 지시서

## Codex 역할
코드 리뷰·테스트 실행·버그 수정.
Claude의 검증 결과를 받아 수정 작업 처리.

## 처리 순서
1. `.claude/tasks/task-review-*.md` 확인
2. 지정된 파일 코드 리뷰
3. 테스트 실행: `npm test` / `pytest` / `mvn test`
4. 실패한 테스트 수정
5. 완료 보고서 → `.claude/tasks/done/`

## MCP (추가 필요)
```toml
[mcp_servers.playwright]
command = "npx"
args    = ["@playwright/mcp@latest"]
```
