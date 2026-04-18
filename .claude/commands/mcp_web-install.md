---
description: "웹 자동화/크롤링 MCP 설치 — Playwright·Puppeteer·Selenium·Apify·Fetch"
allowed-tools: Bash(claude:*), Bash(where:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task

미설치된 것만 설치한다.

```
# Playwright (Microsoft 공식)
claude mcp add playwright -s user -- npx -y @playwright/mcp

# Puppeteer
claude mcp add puppeteer -s user -- npx -y @modelcontextprotocol/server-puppeteer

# Fetch (기본 웹 요청)
claude mcp add fetch -s user -- npx -y @modelcontextprotocol/server-fetch

# Apify (크롤링 플랫폼)
claude mcp add apify -s user -- npx -y apify-mcp-server
```

Selenium: 로컬 WebDriver 설치 필요 (MCP 미지원 — 대신 Playwright 권장)

결과 보고:

| MCP | 상태 | 역할 |
|-----|------|------|
| playwright | 설치됨/실패 | 브라우저 자동화·스크린샷 |
| puppeteer | 설치됨/실패 | 크롤링·PDF 생성 |
| fetch | 설치됨/실패 | API 호출·데이터 수집 |
| apify | 설치됨/실패 | 경쟁사 분석·대규모 크롤링 |
