# design_ppt — PPT·디자인·다이어그램 자동화 — Gamma·Canva·Figma·Mermaid

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~4000

## 📖 개요

PPT 자동 생성 — Claude 구조 → Canva → Mermaid → Figma → Gamma.

## 📋 커맨드

- `/ai-system-stages`
- `/design_ppt`
- `/install-mcp`
- `/make-ppt` ⭐ 기본
- `/ppt-install`

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

- `hook-07-layout-lock` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 주제 기반 생성
```bash
/make-ppt "Vibe Coding 강의" 20
```

### 예시 2: AI 시스템 템플릿
```bash
/ai-system-stages
```

### 예시 3: MCP 설치
```bash
/ppt-install
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
