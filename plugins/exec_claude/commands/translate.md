---
description: "번역 — 소스/타겟 언어 자동 감지 · 전문 용어 glossary 유지"
allowed-tools: Read, Write, Edit, Bash(python:*)
---

## Context
- 대상 파일/텍스트: $ARGUMENTS
- Glossary 경로 (있으면): `.claude/state/glossary.json`

## Your task

사용자가 준 글을 **지정 언어로 번역**한다.

### 입력 받을 수 있는 인자
- `--to <ko|en|ja|zh|es|fr|de|ar>` — 타겟 언어 (필수)
- `--from <auto|lang>` — 소스 (기본 auto 감지)
- `--style <literal|natural|technical|literary>` — 번역 스타일
- `--glossary <path>` — 전문 용어 사전 적용

### 흐름

1. **원문 확보** — 파일 또는 inline
2. **언어 감지** — `--from auto` 면 Claude 가 감지 (한글·영문·일본어·중국어·기타)
3. **용어 사전** — glossary 있으면 일관 적용 (예: "함수" ↔ "function")
4. **번역** — 자연스러움 + 원문 뉘앙스 유지
5. **품질 체크** — 역번역 1 샘플 (예: 번역 결과 중 1문장 → 원문 언어 → 의미 일치 확인)
6. **저장** — 파일 입력이면 `.bak` 백업 후 원본 덮어쓰기 · 또는 사용자 명시 시 `_<lang>.ext`

### 금지
- 사실 왜곡 (예: 숫자·날짜·고유명사 변경)
- 번역 안 되는 고유명사 강제 번역 (영문/원어 병기)
- 독자적 추가 (원문에 없는 설명 삽입)
- 민감 문서 (법률·의료) 는 사용자 명시 승인 필요

### 긴 문서
10k+ chars 는 섹션 분할 후 병렬 번역 (Agent sub-agent 활용 가능).

## 참조
- plugins/exec_orch/skills/prompt-techniques.md
- `.claude/state/glossary.json` (용어 사전 신설 예정)
