# design_word — Word·문서 자동화 — 계약서·보고서·기획서 생성

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1100

## 📖 개요

Word 문서 자동 생성 — python-docx + Mermaid + PDF.

## 📋 커맨드

- `/design_word`
- `/word-make` ⭐ 기본
- `/word-status`

## 🧠 스킬

- `skill-34-code-docs` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-06-designer`

## 🪝 훅

- `hook-02-post-impl` (spec)
- `hook-06-notify` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: Word 생성
```bash
/word-make outline.md
```

### 예시 2: 상태 확인
```bash
/word-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
