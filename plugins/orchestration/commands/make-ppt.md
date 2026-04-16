---
description: "PPT 자동 생성 — 주제 입력 → Gamma/Canva/Mermaid 파이프라인"
allowed-tools: Bash(where:*)
---

## Context
- Gamma MCP: !`claude mcp list 2>/dev/null | grep -i gamma && echo "OK" || echo "없음"`
- Canva MCP: !`claude mcp list 2>/dev/null | grep -i canva && echo "OK" || echo "없음"`

## Your task

**입력받은 주제**로 PPT를 만든다. 아래 파이프라인 순서대로 실행.

### Step 1 — 구조 설계 (Claude)
주제를 분석해서 슬라이드 목차 작성:
- 슬라이드 수: 10~15장
- 각 슬라이드: 제목 + 핵심 포인트 3개 + 시각화 방향

### Step 2 — PPT 생성

**Gamma MCP 있으면:**
```
mcp__claude_ai_Gamma__generate 호출
  → prompt: 설계한 목차와 내용 전달
  → 자동으로 슬라이드 생성
```

**Gamma 없고 Canva MCP 있으면:**
```
mcp__claude_ai_Canva__generate-design 호출
  → 슬라이드별 개별 생성
```

**둘 다 없으면:**
```
/plug_design 실행 → Gamma/Canva 설치 후 재시도 안내
```

### Step 3 — 다이어그램 (Mermaid)
구조도·플로우가 필요한 슬라이드:
```
mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram 호출
```

### Step 4 — 결과 보고
| 항목 | 결과 |
|------|------|
| 슬라이드 수 | N장 |
| 생성 도구 | Gamma/Canva |
| 다이어그램 | N개 |
| 링크 | [열기](URL) |
