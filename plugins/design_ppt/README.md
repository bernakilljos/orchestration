# design_ppt — PPT·디자인·다이어그램 자동화 — Gamma·Canva·Figma·Mermaid

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

PPT 자동 생성 — Claude 구조 → Canva → Mermaid → Figma → Gamma.

- **Why**: 슬라이드 디자인은 AI 파이프라인이 제일 빠름.
- **When**: 제안서, 강의 자료, IR 피치덱.

## 📋 커맨드

- `/ai-system-stages`
- `/design_ppt`
- `/install`
- `/install-mcp`
- `/make-ppt` ⭐ 기본

## 🧠 스킬

- `skill-08-design` ⭐ 핵심
- `skill-14-auto-detail` ⭐ 핵심
- `skill-15-theme-factory` ⭐ 핵심
- `skill-16-brand-guidelines`
- `skill-21-marketing`
- `skill-22-remotion`

## 🤖 에이전트

- `agent-04-architect`
- `agent-06-designer`

## 🪝 훅

- `hook-07-layout-lock`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 주제 기반 생성
```
/make-ppt "Vibe Coding 강의" 20
```

### 예시 2: AI 6단계 템플릿
```
/ai-system-stages
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
