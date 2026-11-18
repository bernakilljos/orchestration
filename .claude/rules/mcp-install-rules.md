---
paths:
  - ".mcp.json"
  - "plugins/mcp_*/**"
  - "plugins/exec_orch/commands/plug_*"
  - ".claude/commands/plug_*"
  - ".claude/scripts/*mcp*"
---
# MCP 설치 룰

> **전문**: `.claude/rules-ref/mcp-install-rules.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**npm package 명령을 .md / .json / 커맨드에 작성 전 `npm view <package>` 로 실재 확인.**
