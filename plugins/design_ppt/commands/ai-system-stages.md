---
description: "AI 시스템 6단계 PPT 생성 — Prompt→Agent→Orchestration→Automation→Autonomous→Platform"
allowed-tools: Bash(where:*)
---

## Context
- Gamma MCP:  !`claude mcp list 2>/dev/null | grep -i gamma   && echo OK || echo 없음`
- Canva MCP:  !`claude mcp list 2>/dev/null | grep -i canva   && echo OK || echo 없음`
- Mermaid MCP:!`claude mcp list 2>/dev/null | grep -i mermaid && echo OK || echo 없음`

## Your task

슬라이드 수: `$ARGUMENTS` 입력 시 그 수, 없으면 기본 30장
Gamma 1회 최대 10장 → 10장씩 파트 분할 후 순차 생성

**테마 선택: stratos** (다크·우주적·미래지향 — AI 발표 최적)
**이미지: abstract** (비구상적 흐름·기하학적)

---

### Step 0 — WebSearch 실측 (필수 · 생략 X)

생성 전 **WebSearch 2건** 호출:
1. "AI agent system stages 2026 autonomous self-improving" — 최신 단계론
2. "Claude Code multi-agent orchestration production patterns 2026" — 최신 구현 패턴

결과를 각 단계 설명에 반영. 출처 slide 안 각주로 명시.

---

### Step 0.5 — 우리 kit 실측 (각 단계 "현재 구현" column 생성)

| 단계 | 우리 kit 구현 (실측 · slide 반드시 포함) |
|---|---|
| 1 Prompt | prompt-techniques.md 12 기법 · explainlikeim5·brief·ghost |
| 2 Agent | agents/* (coach·pm·judge·code-reviewer·brainstorming-partner) · subagent fork depth 3 |
| 3 Orchestration | exec_orch · route.py (quota·budget·fallback) · codex-auto / gemini-auto / haiku-auto 병렬 |
| 4 Automation | 72+ hooks · SessionStart/PostToolUse/Stop/UserPromptSubmit · Task Scheduler cron |
| **5 Autonomous ★** | **자가발전 계층** — orca.db 지속 기억 (conversations·session_summary·problem_solutions·activations·decisions) · learn-user-patterns.py (반복 패턴 자동 학습) · suggest-learned-patterns.py (자동 매핑 제안) · resume-last-24h.py (재부팅 자동 복구) · aggregate-rule-adherence.py (디자인·개발 룰 위반 지수) · detect-user-emotion (40+ 자동 매핑) · verify-after-edit-mandatory (증명 체인) |
| 6 Platform | multi-project kit (install-to IFRS·RMS·ICM·calc) · marketplace plugins · setup/modules install 자동화 · claude-mem·headroom MCP 통합 |

★ 사용자 강조: "성능향상 기억 자가발전 계층" = 우리 5단계 이미 상당 구현. slide 에 꼭 반영.

---

### Step 1 — 슬라이드 수 계산
- 입력값 없으면 30장 (3파트)
- 10장씩 나누기 → N파트 → N회 Gamma 호출

---

### Step 2 — 파트별 내용 (30장 기준)

**파트 1 (1~10): 도입 + 1~4단계**
표지 / 전체 로드맵 / 1단계 Prompt / 2단계 Agent / 1vs2 비교
3단계 Orchestration / 3단계 파이프라인 / 4단계 Automation / 4단계 현재 구현 / 1~4 비교표

**파트 2 (11~20): 5단계 + 6단계 ★핵심★**
🔥 5단계 Autonomous System — 차원이 바뀐다
5단계 4요소: 라우팅/실패판단/재시도/상태저장
5단계 자율 루프 / 5단계 현재 구현 완료
🔥 6단계 Platform — 생태계
6단계 구성요소 / 전체 비교 매트릭스 / 현재 위치 / 6단계 달성 전략

**파트 3 (21~30): 심화 + 마무리**
파이프라인 상세 / 자율 루프 상세 / 플랫폼 아키텍처
구현 로드맵 / 비용vs가치 / 팀 운영 모델 / KPI / 도전과제 / 다음 스텝
마무리: "AI는 도구가 아니라 팀이다"

---

### Step 3 — Gamma 순차 호출

각 파트마다:
```text
mcp__claude_ai_Gamma__generate 호출
  themeId: "stratos"
  numCards: 10
  textOptions: {language: "ko", tone: "professional"}
  imageOptions: {stylePreset: "abstract"}
  additionalInstructions: "5단계/6단계 강조 색상. 플로우차트·비교표 적극 활용."
```

Gamma 크레딧 부족 오류 시:
- Canva OK → Canva로 대체 생성
- 둘 다 없으면 → Mermaid로 다이어그램만 생성 후 텍스트 슬라이드 구조 제공

---

### Step 4 — 결과 보고

| 파트 | 슬라이드 | Gamma URL |
|------|--------|-----------|
| 파트 1 | 1~10장 | [열기](URL) |
| 파트 2 | 11~20장 | [열기](URL) |
| 파트 3 | 21~30장 | [열기](URL) |

테마 변경: Gamma 편집기 → 우측 상단 테마 → Stratos 선택
