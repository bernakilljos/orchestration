# mcp_docs — 문서처리 MCP 설치 — PDF·DOCX·OCR

> **Prefix**: `mcp_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1100

## 📖 개요

문서처리 MCP — PDF·DOCX·OCR(Tesseract).

## 📋 커맨드

- `/install` ⭐ 기본
- `/mcp_docs`
- `/status`

## 🧠 스킬

- `skill-34-code-docs` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`

## 🪝 훅

- `hook-02-post-impl` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 일괄 설치
```bash
/plug_docs
```

### 예시 2: 상태 확인
```bash
/mcp_docs-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
