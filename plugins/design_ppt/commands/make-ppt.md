---
description: "PPT 자동 생성 — 주제 입력 → Claude 구조 → Gamma 슬라이드 → Mermaid 다이어그램"
allowed-tools: Bash(where:*)
---

## Context
- Gamma: !`claude mcp list 2>/dev/null | grep -i gamma && echo OK || echo 없음`
- Canva: !`claude mcp list 2>/dev/null | grep -i canva && echo OK || echo 없음`
- Mermaid: !`claude mcp list 2>/dev/null | grep -i mermaid && echo OK || echo 없음`

## Your task

### Step 1 — 구조 설계 (Claude)
슬라이드 목차 작성 (10~15장, 각 슬라이드: 제목 + 핵심 3포인트 + 시각화 방향)

### Step 2 — 생성
- Gamma OK → mcp__claude_ai_Gamma__generate 호출
- Gamma 없고 Canva OK → mcp__claude_ai_Canva__generate-design 호출
- 둘 다 없음 → /install-mcp 실행 후 재시도 안내

### Step 3 — 다이어그램
Mermaid OK → mcp__claude_ai_Mermaid_Chart__validate_and_render_mermaid_diagram 호출

### Step 4 — 결과 보고
슬라이드 수, 생성 도구, 다이어그램 수, 링크
