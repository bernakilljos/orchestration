---
description: "PPT 자동 생성 — Claude 구조 → Canva 초안 → Mermaid 다이어그램 → Figma 완성"
allowed-tools: Bash(where:*)
---

## Context
- Gamma MCP:  !`claude mcp list 2>/dev/null | grep -i gamma   && echo OK || echo 없음`
- Canva MCP:  !`claude mcp list 2>/dev/null | grep -i canva   && echo OK || echo 없음`
- Mermaid MCP:!`claude mcp list 2>/dev/null | grep -i mermaid && echo OK || echo 없음`
- Figma MCP:  !`claude mcp list 2>/dev/null | grep -i figma   && echo OK || echo 없음`

## Your task

파이프라인: **Claude → Canva → Mermaid → Figma**

---

### Hook (사전 확인)
- 필요 MCP 설치 여부 확인 (Context 참조)
- 없으면 `/install-mcp` 실행 안내 후 계속 진행 가능한지 판단

---

### Step 1 — Planner: Claude가 구조 설계
주제: `$ARGUMENTS`

슬라이드 목차 작성 (10~15장):
```
1. 표지 — 제목, 부제, 날짜
2. 목차
3~N. 본문 슬라이드 (각 슬라이드: 제목 + 핵심 3포인트 + 시각화 방향)
N+1. 결론/요약
N+2. Q&A / 감사 인사
```

각 슬라이드에 대해:
- 텍스트 내용
- 시각화 유형 (차트/다이어그램/이미지/표)
- 색상 톤 제안

---

### Step 2 — Executor: Canva 초안 생성
Canva OK →
```
mcp__claude_ai_Canva__generate-design 호출
  type: "presentation"
  title: [주제]
  slides: [목차 기반 슬라이드 수]
```

Canva 없고 Gamma OK →
```
mcp__claude_ai_Gamma__generate 호출
  prompt: [설계한 전체 목차와 내용]
```

---

### Step 3 — Executor: Mermaid 다이어그램
다이어그램이 필요한 슬라이드 (흐름도·시퀀스·구조도):

```
mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram 호출
  diagram: ```mermaid
    [자동 생성된 다이어그램 코드]
  ```
```

없으면 ```mermaid 코드블록 직접 생성.

---

### Step 4 — Validator: 검토
- 슬라이드 수 확인 (목표 달성 여부)
- 텍스트 과다 슬라이드 감지 (1슬라이드 = 3포인트 이하)
- 다이어그램 렌더링 오류 확인

---

### Step 5 — Figma 연동 (Figma OK + 디자인 다듬기 요청 시)
```
mcp__claude_ai_Figma__get_design_context 호출
  → 기존 디자인 시스템 색상·폰트·컴포넌트 참조
  → Canva 초안에 브랜드 가이드라인 적용
```

---

### Step 6 — State 저장
```
docs/YYYY-MM-DD/presentations/[주제].md  ← 슬라이드 구조 텍스트본
```

### Step 7 — 결과 보고
| 항목 | 결과 |
|------|------|
| 슬라이드 수 | N장 |
| 생성 도구 | Gamma/Canva |
| 다이어그램 | N개 |
| Figma 연동 | 완료/미연동 |
| 저장 경로 | docs/YYYY-MM-DD/ |
