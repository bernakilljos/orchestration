---
description: "웹 자동화/크롤링 MCP 설치 — Playwright·Puppeteer·PDF (실측 npm 기반)"
allowed-tools: Bash(claude:*), Bash(cmd:*)
---

## Context
- 현재 OS: Windows (MINGW64)
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Verified Packages (2026-04-23 실측)

| 패키지 | 버전 | 상태 | 설치 가능 |
|--------|------|------|---------|
| @playwright/mcp | 0.0.70 | 공식 | ✅ |
| @modelcontextprotocol/server-puppeteer | 2025.5.12 | 공식 | ✅ |
| @modelcontextprotocol/server-pdf | - | 공식 | ✅ |
| @hisma/server-puppeteer | 0.6.5 | 커뮤니티 fork | ✅ (대체) |

## 불가능한 패키지
- `@modelcontextprotocol/server-fetch` — npm 미등록 (404)
- `apify-mcp-server` — npm 미등록
- `@modelcontextprotocol/server-selenium` — 미지원

## Your task: 미설치된 것만 설치

### Windows 필수: cmd /c 래퍼
npx MCP 는 Windows MINGW64 에서 진정한 cmd /c 필요. 없으면 "failed to connect" 에러.

```bash
# Playwright (Microsoft 공식 — 브라우저 자동화·스크린샷)
claude mcp add playwright -s user -- cmd /c npx -y @playwright/mcp

# Puppeteer (크롤링·PDF 생성 — 공식 최신)
claude mcp add puppeteer -s user -- cmd /c npx -y @modelcontextprotocol/server-puppeteer

# PDF (PDF 조작·생성)
claude mcp add pdf -s user -- cmd /c npx -y @modelcontextprotocol/server-pdf
```

## 결과 보고

| MCP | 상태 | 역할 | 설치 명령 |
|-----|------|------|---------|
| playwright | 설치됨/실패 | 브라우저 자동화·스크린샷 | cmd /c npx @playwright/mcp |
| puppeteer | 설치됨/실패 | 크롤링·PDF 생성 | cmd /c npx @modelcontextprotocol/server-puppeteer |
| pdf | 설치됨/실패 | PDF 조작 | cmd /c npx @modelcontextprotocol/server-pdf |

## 인증 필요한 MCP (선택)
Apify 대체 필요 시 API 토큰 필요 (https://console.apify.com).
현재 npm 에 공식 Apify MCP 미등록 → 직접 npm 패키지 검색 후 이 섹션 갱신.
