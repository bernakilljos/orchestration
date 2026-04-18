---
description: "디자인/PPT MCP 설치 — Canva·Figma·Gamma·PowerPoint·Google Slides·Mermaid"
allowed-tools: Bash(claude:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`

## Your task

Canva·Figma·Gamma·Mermaid는 **claude.ai 내장 MCP**로 이미 활성화되어 있을 수 있다.
미설치된 것만 추가 설치한다.

```
# PowerPoint (Office 365 MCP)
claude mcp add powerpoint -s user -- npx -y @modelcontextprotocol/server-office

# Google Slides
claude mcp add google-slides -s user -- npx -y @googleapis/mcp-server-slides

# Mermaid (내장 없으면 설치)
claude mcp add mermaid -s user -- npx -y mermaid-mcp-server
```

내장 MCP 상태 확인:
- Canva → `mcp__claude_ai_Canva__` 접두사 툴 존재 여부
- Figma → `mcp__claude_ai_Figma__` 접두사 툴 존재 여부
- Gamma → `mcp__claude_ai_Gamma__` 접두사 툴 존재 여부

결과 보고:

| MCP | 상태 | 파이프라인 역할 |
|-----|------|--------------|
| Canva | 내장/설치됨 | 초안 생성 |
| Figma | 내장/설치됨 | 디자인→코드 |
| Gamma | 내장/설치됨 | PPT 자동 생성 |
| PowerPoint | 설치됨/실패 | 오피스 편집 |
| Google Slides | 설치됨/실패 | 슬라이드 편집 |
| Mermaid | 내장/설치됨 | 다이어그램 생성 |

파이프라인: Claude → 구조 → Canva 초안 → Mermaid 다이어그램 → Figma 완성
