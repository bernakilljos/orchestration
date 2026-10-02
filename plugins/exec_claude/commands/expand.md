---
description: "내용 확장 — 요약·개요·bullet 를 상세한 본문으로 풀어쓰기"
allowed-tools: Read, Write, Edit
---

## Context
- 대상 파일/텍스트: $ARGUMENTS
- 사용자 요청 길이·깊이 참조

## Your task

사용자가 준 **요약·개요·bullet 를 상세 본문**으로 확장한다.

### 입력 받을 수 있는 인자
- `--depth <2x|3x|5x|detailed>` — 확장 배율
- `--include <example|data|quote|analogy|counterpoint>` — 추가 요소
- `--audience <5살|초보|전문가|경영진>` — 독자
- `--sections <N>` — 섹션 수 지정

### 흐름

1. **원문 분석** — 핵심 포인트·bullet·헤더 추출
2. **확장 계획** — 각 포인트별 (예시·근거·비유·반론) 결정
3. **본문 생성** — 각 섹션에 살을 붙임 · 구조·논리 유지
4. **품질 체크** — 사실 추가가 fabrication 아닌지 자가 검증 (근거 명시 필요)
5. **저장** — 파일이면 `.bak` 백업 후 덮어쓰기

### 확장 패턴
- bullet → 각 bullet 1~2 문단
- 요약 → 서론·본론·결론 구조
- 아웃라인 → 각 섹션 300~500 자

### 금지
- 추측·fabrication (근거 없는 통계·날짜·인용)
- 반복·같은 말 다르게 (padding)
- 원문 핵심 손실 (확장만 추가)
- 사용자 요청보다 짧게 (확장 아님)

### 역방향 X
"요약" 은 `/summarize` · 이 명령은 **확장만**.

## 참조
- plugins/exec_claude/commands/summarize.md (반대 방향)
- plugins/exec_orch/skills/prompt-techniques.md § CoT
- feedback_insight_explain_simple.md (5살 톤)
