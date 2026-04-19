# design_word — Word·문서 자동화 — 계약서·보고서·기획서 생성

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

Word 문서 자동 생성 — python-docx + Mermaid + PDF 변환.

- **Why**: 긴 문서·계약서·기술문서 자동화.
- **When**: 제안서 문서, 기술 스펙, 매뉴얼.

## 📋 커맨드

- `/design_word`
- `/make`
- `/status`

## 🧠 스킬

- `skill-34-code-docs` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-06-designer`

## 🪝 훅

- `hook-02-post-impl`
- `hook-06-notify`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 기본 생성
```
/word-make outline.md
```

### 예시 2: 상태 확인
```
/word-status
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
