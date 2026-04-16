# design_ppt — Codex 지시서

## Codex 역할
PPT 슬라이드 콘텐츠 초안 작성 (텍스트·구조).
실제 PPT 파일 생성은 Claude(Gamma/Canva MCP)가 처리.

## Codex가 할 수 있는 것
- 슬라이드 구조 설계 → `.md` 파일로 저장
- 각 슬라이드 텍스트 초안
- Mermaid 다이어그램 코드 생성

## MCP (추가 필요)
`.codex/config.toml` 에 아래 추가:
```toml
[mcp_servers.mermaid]
command = "npx"
args    = ["-y", "mermaid-mcp-server"]
```
