---
description: "Claude 전용 기능 가용성 + 사용 시나리오 한 화면 요약"
allowed-tools: Bash(claude mcp list:*), Bash(ls:*), Bash(where:*)
---

## Context
- MCP 목록: !`claude mcp list 2>/dev/null | head -20`
- 설치 플러그인: !`ls plugins/ | grep -v "^_"`
- exec_orch 워커: !`ls .claude/state/ 2>/dev/null | grep -E "worker|heartbeat" | head -5`

## Your task

Claude 전용 기능 4영역을 가용성 표로 출력하고, 어느 시나리오에 어떤 커맨드를 쓸지 안내.

### 출력 포맷

```
═══════════════════════════════════════════════════════
   exec_claude — Claude 깊이 활용 (vs exec_orch 라우팅)
═══════════════════════════════════════════════════════

📋 4대 영역 가용성

  1. AskUserQuestion (구조화 질문)
     상태:  항상 사용 가능 (Claude 내장)
     커맨드: /claude-ask <topic>

  2. Artifacts (인터랙티브 결과물)
     상태:  항상 사용 가능 (HTML 출력)
     커맨드: /claude-artifact <type> <subject>
     타입: dashboard | calculator | chart | form | game

  3. Connectors (외부 SaaS 통합)
     상태: <MCP 목록 보고 판단>  일부만 설치됨
     커맨드: /claude-connectors [list|add]
     설치된 것: <상위 5개>

  4. Extended Thinking (복잡 추론)
     상태:  항상 사용 가능 (Claude Opus/Sonnet)
     커맨드: /claude-thinking <task>

 시나리오별 추천

  사용자에게 입력 받아야 함         → /claude-ask
  대시보드·계산기·시각화 만들기      → /claude-artifact
  Slack/Notion/Drive 와 연동         → /claude-connectors
  어려운 알고리즘·설계 결정          → /claude-thinking
  여러 AI 가 협업해야 함 (큰 코드)   → exec_orch (이 플러그인 X)

🔗 함께 보기
  /help exec_orch       — 멀티AI 라우팅
  /arch-mindmap claude  — Claude 전체 맵 다이어그램
```

### 동적 부분
- "Connectors" 항목은 Context 의 MCP 목록을 분석해서 실제 설치된 것 표기
- MCP 가 0개면 → "/mcp_collab" 등 설치 안내

### 짧게 (옵션)
사용자가 `--brief` 같은 인자 주면 4줄로 요약.
