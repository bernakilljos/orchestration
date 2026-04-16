---
description: "Word 문서 자동 생성 — 계약서·보고서·기획서·회의록"
allowed-tools: Bash(where:*), Bash(python:*)
---

## Context
- python-docx: !`python -c "import docx; print('OK')" 2>/dev/null || echo 없음`
- officecli 스킬: .claude/skills/skill-* 에서 officecli 관련 확인

## Your task

### 요청 분석
$ARGUMENTS 를 분석해서:
- 문서 유형 (계약서/보고서/기획서/회의록/제안서)
- 필요 섹션 구성
- 서식 (표, 번호 목록, 헤딩 구조)

### 생성
python-docx OK → .docx 생성 → docs/YYYY-MM-DD/ 저장
없으면 → `pip install python-docx` 안내

### 결과
파일 경로, 페이지 수(예상), 섹션 목록 보고
