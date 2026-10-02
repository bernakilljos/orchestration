---
description: "글 다시 쓰기 — 톤·스타일·대상·길이 지정해 Claude 가 재작성"
allowed-tools: Read, Write, Edit
---

## Context
- 대상 파일 (있으면): $ARGUMENTS
- 현재 선택 영역 / 사용자 지시 본문 참조

## Your task

사용자가 준 글을 **지정 조건에 맞춰 다시 쓴다**.

### 입력 받을 수 있는 인자
- `--tone <formal|casual|friendly|professional|academic>` — 톤
- `--style <bullet|paragraph|conversation|technical>` — 스타일
- `--audience <5살|초보|전문가|경영진|고객>` — 독자
- `--length <short|medium|long|50%|200%>` — 길이
- `--lang <ko|en|ja|zh>` — 언어 유지/변경

### 흐름

1. **원문 확보** — 파일 경로 주어졌으면 Read · 아니면 사용자가 붙여넣은 본문
2. **분석** — 1줄로 "원문: X 톤·Y 스타일·Z 길이" 요약
3. **재작성** — 지정 조건 반영 · 사실·논리·핵심 요소 유지
4. **대조 출력** — 원문 vs 재작성 축약 2행 표 (처음·마지막 2줄만)
5. **저장** — 파일 입력이면 `.bak` 백업 후 원본 자리 덮어쓰기 (feedback_no_version_suffix 준수)

### 금지
- 사실 추가·왜곡 X (hallucination)
- 핵심 메시지 손실 X
- `-v2` 접미사 X (`.bak` 백업 후 원본 덮어쓰기)
- 사용자 명시 없이 언어 변경 X

### 짧은 응답 선호
결과만 보여줘. 변경 사유 긴 설명 X (사용자 ENFP-ADHD).

## 참조
- feedback_no_version_suffix.md
- feedback_ghost_writing.md (ghost skill 와 중복 아님 — 이건 조건부 재작성)
- plugins/exec_orch/skills/prompt-techniques.md § Role·Context
