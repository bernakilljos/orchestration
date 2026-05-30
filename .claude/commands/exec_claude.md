---
description: "Claude 전용 심화 — 구조화 질문·아티팩트·커넥터·확장 사고"
allowed-tools: Bash, Read, Edit
---

# /exec_claude — Claude 깊이 활용 허브

## 포함 커맨드
- `/claude-status` — Claude 전용 기능 가용성 + 사용 시나리오 (**기본 액션**)
- `/claude-ask <topic>` — 구조화 질문 폼 (선택지·라벨)
- `/claude-artifact <type> <subject>` — 인터랙티브 HTML/대시보드 산출물
- `/claude-connectors [list|add]` — Slack/Drive/Notion 등 50+ 커넥터 흐름
- `/claude-thinking <task>` — Extended Thinking 가이드 + 적용

## 자동 활성 스킬
- `skill-claude-ask` — "물어봐줘"·"선택지로"·"구조화 질문" 트리거
- `skill-claude-artifact` — "인터랙티브"·"대시보드"·"HTML 결과물" 트리거
- `skill-claude-thinking` — "깊게 생각해"·"단계적 추론"·"어려운 문제" 트리거

## exec_orch 와의 관계
| | exec_orch | exec_claude |
|---|---|---|
| 역할 | 멀티AI 라우팅 | Claude 깊이 활용 |
| 워커 | codex/gemini/claude-auto | 인-세션 |
| 핸드오프 | `.claude/tasks/` 파일 | 대화 + Artifacts |

→ orch 가 "어떤 AI", claude 가 "Claude 는 어떻게 잘".

## 기본 실행
`/claude-status` — 지금 어떤 Claude 전용 기능을 쓸 수 있는지 한 화면 요약.
