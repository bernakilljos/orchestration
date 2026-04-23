---
description: "디자인/PPT 도구 설치 — 검증된 npm 패키지만 · Canva(OAuth) + Mermaid + Figma(PAT)"
allowed-tools: Bash(npm:*), Bash(claude:*)
---

## Context
- 현재 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`
- npm 설치 가능 여부: !`which npm && echo "OK" || echo "NodeJS/npm 필요"`

## 실제 설치 가능한 디자인 MCP (2026-04 검증됨)

### A. 인증 불필요 — 즉시 설치 가능

```bash
# Mermaid (다이어그램·플로우차트 자동 생성)
# npm: mermaid-mcp-server v1.0.8 ✓ 검증됨
claude mcp add mermaid -s user -- npx -y mermaid-mcp-server

# PowerPoint Ultimate (python-pptx 기반, 로컬 PPT 편집)
# npm: powerpoint-mcp-ultimate v1.0.0 ✓ 검증됨
claude mcp add powerpoint -s user -- npx -y powerpoint-mcp-ultimate

# HTML→PPTX 변환 (CSS 그라디언트·그림자 지원)
# npm: dom-to-pptx v1.1.7 ✓ 검증됨
claude mcp add dom-to-pptx -s user -- npx -y dom-to-pptx
```

### B. OAuth 필요 (로그인 협조 시)

**Canva Connect** — 전문 디자인 생성
- npm: `@mcp_factory/canva-mcp-server`
- 공식: https://www.canva.dev/docs/connect/mcp-server/
- 요구: 개발자 앱 등록 → `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET`
- 설치:
```bash
claude mcp add canva -s user \
  --env CANVA_CLIENT_ID=$CANVA_CLIENT_ID \
  --env CANVA_CLIENT_SECRET=$CANVA_CLIENT_SECRET \
  -- npx -y @mcp_factory/canva-mcp-server
```

**Google Slides** — 공동편집 및 API 연동
- npm: `@zhenujt123/google-slides-mcp`
- 요구: Google Cloud 프로젝트 → Slides API 활성화 → OAuth 설정
- 설치:
```bash
claude mcp add google-slides -s user \
  --env GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID \
  --env GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET \
  -- npx -y @zhenujt123/google-slides-mcp
```

**Figma** — 디자인 시스템 가져오기
- npm: `claude-talk-to-figma-mcp`
- 공식: https://www.figma.com (Personal Access Token 발급)
- 요구: Figma Account Settings → PAT 토큰
- 설치:
```bash
claude mcp add figma -s user \
  --env FIGMA_TOKEN=$FIGMA_TOKEN \
  -- npx -y claude-talk-to-figma-mcp
```

## 삭제된 거짓 명령어 (npm에 없음)

❌ `@modelcontextprotocol/server-office` — 404 (npm 존재 안 함)
❌ `@googleapis/mcp-server-slides` — 404 (npm 존재 안 함)
❌ "Gamma claude.ai 내장" — Claude Code CLI에는 없음 (claude.ai 웹 전용)
❌ "Canva/Figma/Gamma 내장" — 가정 제거

## 사용 가능 파이프라인

| 수준 | 도구 조합 | 용도 |
|------|---------|------|
| **최소** | python-pptx + Mermaid | 로컬 PPT, 다이어그램 자동 생성 |
| **중급** | + Figma PAT | 기존 Figma 디자인 → PPT 템플릿 |
| **고급** | + Canva OAuth | 전문 디자인 · 클라우드 저장 |

## Gamma는?

공개 API 없음. 대체:
1. **Claude 직접 설계** → python-pptx 로 PPT 생성 (추천)
2. **Playwright MCP** + 웹 자동화 (실험적)
3. **claude.ai 웹** 에서 직접 사용
