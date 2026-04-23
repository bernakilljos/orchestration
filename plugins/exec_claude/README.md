# exec_claude — Claude 전용 심화 활용

## 목적
`exec_orch` 가 멀티AI(Claude+Codex+Gemini) **라우팅**을 담당한다면,
`exec_claude` 는 **Claude 자체를 깊게 활용하는** 패턴을 제공한다.

배경: "Claude is eating up everything" 다이어그램(Ruben Hassid)에서 식별된
Claude 전용 기능 중 우리 킷에 부족했던 부분(AskUserQuestion·Artifacts·Connectors·Extended Thinking)을 보완.

## 두 플러그인 관계

| | exec_orch | exec_claude |
|---|---|---|
| **역할** | 멀티AI 협업 라우팅 | Claude 깊이 활용 |
| **워커** | codex/gemini/claude-auto | (없음 — 인-세션) |
| **태스크 핸드오프** | `.claude/tasks/` 파일 | 대화 + Artifacts |
| **언제** | 500줄+ 구현·검증 분담 | 사용자 인터랙션 강화·인터랙티브 산출물 |

→ **함께 사용**: orch 가 "어떤 AI 가 할 것인가" 를 정하고, claude 가 "Claude 는 어떻게 잘 할 것인가" 를 정한다.

## 커맨드

| 커맨드 | 용도 |
|--------|------|
| `/claude-status` | Claude 전용 기능 가용성 + 사용 시나리오 안내 |
| `/claude-ask <topic>` | 구조화된 질문 폼 생성 (자유텍스트 대신 선택지·라벨) |
| `/claude-artifact <type> <subject>` | 인터랙티브 HTML/대시보드 결과물 생성 |
| `/claude-connectors [list\|add]` | Slack/Drive/Notion 50+ 커넥터 1-click 흐름 |
| `/claude-thinking <task>` | 복잡 추론용 Extended Thinking 가이드 + 적용 |

## 스킬 (자동 활성화)

| 스킬 | 트리거 |
|------|--------|
| `skill-claude-ask` | "물어봐줘", "선택지로", "구조화 질문" |
| `skill-claude-artifact` | "인터랙티브", "대시보드", "HTML 결과물" |
| `skill-claude-thinking` | "깊게 생각해", "단계적 추론", "어려운 문제" |

## 의존
- `exec_orch` (라우팅 결정 시 참조)

## 참고
- 분석 근거: `docs/2026-04-23/claude-vs-orchestration-comparison.md`
- 관련 다이어그램: `docs/screens/arch/claude-mindmap-eating-everything-hassid.png`
