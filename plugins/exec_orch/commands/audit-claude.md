---
description: Claude Code 환경 감사 — 조사→공식 확인→증명→최소 변경 (NEW 2 / CHANGE 5 / REMOVE 무제한)
allowed-tools: Bash(python:*), Bash(grep:*), Bash(find:*), Bash(wc:*), Bash(ls:*), Read, WebSearch, Agent, Grep, Glob
---

# /audit-claude — Claude Code 환경 감사

> **원칙**: 변경할 필요 없으면 변경하지 않는다. 설정 수정이 목표 X · 단순·안정·검증 가능이 목표.
> **SoT**: `.claude/rules/operating-principles.md`

## 사용

```text
/audit-claude [분야=all]

분야: rules | hooks | agents | skills | mcp | statusline | all (기본)
```

## 수행 순서 (9 단계)

### 1. 조사 (전수)

- CLAUDE.md 줄 수 · 섹션 구조
- `.claude/rules/*.md` 수 + 각 역할
- `.claude/hooks/` + `tool/` + `prompt/` 모듈 수
- `.claude/agents/` + `plugins/*/agents/` 수 + 각 역할
- `.claude/skills/` + `plugins/*/skills/` 수 + 각 역할
- MCP 설정 (`claude mcp list`)
- `.claude/statusline.sh` + 관련 스크립트
- lint·test·build·typecheck 설정

### 2. 최신 공식 자료 확인 (WebSearch)

우선순위:
1. code.claude.com · Anthropic 공식 문서
2. Anthropic 공식 GitHub
3. 공식 Help Center
4. 신뢰할 수 있는 공개 사례

특히 확인:
- hooks · rules · CLAUDE.md · skills · subagents · MCP · permissions · checkpoint · statusline

**기억에 의존 X · WebSearch 로 확인**.

### 3. 증명 (각 후보마다)

| 현재 상태 | 문제점 | 실제 근거 | 공식 문서 근거 | 변경 필요 여부 | 기대 효과 | 부작용·충돌 |
|---|---|---|---|---|---|---|

추측만으로 수정 X.

### 4. 중복 제거 (SoT 통합)

| 층 | 책임 | 중복 금지 |
|---|---|---|
| CLAUDE.md | 기본 원칙 | 본문 중복 X · 참조만 |
| Rule | 영역별 규칙 | 1 규칙 = 1 SoT |
| Hook | 반드시 막음 · 자동 실행 | 경고·알림은 Hook X |
| Skill | 반복 작업 절차 | 1회성 Skill X |
| Subagent | 독립 판단 | 1 역할 = 1 agent |
| Statusline | 관측·표시 | 지시·행동 X |

### 5. 변경 기준 (하나 이상)

- 실제 반복 문제 방지 가능
- 명백한 누락 있음
- 중복·충돌 제거 가능
- 최신 Claude Code 기능으로 더 단순 대체 가능
- 토큰·실행비용·속도 의미 있게 개선 가능
- 검증 신뢰도 향상 가능

**"좋아 보인다"는 이유로 추가 X**.

### 6. 최소 변경 (금지 목록)

- 필요 없는 agent 추가
- 비슷한 hook 중복 생성
- CLAUDE.md 무한 확장
- 같은 규칙 여러 파일 복제
- 기존 정상 기능 삭제
- 근거 없는 구조 변경

### 7. 변경 전 보고 (분류 표)

| 항목 | 현재 | 문제 | 조치 | 이유 | 우선순위 | 분류 |
|---|---|---|---|---|---|---|

분류: **KEEP** · **CHANGE** · **REMOVE** · **NEW**

### 8. 수정 후 검증 (미측정 X 로 표시 금지)

- 설정 문법 (`python -X utf8 .claude/scripts/validate-plugin-schema.py`)
- hook 실행 여부 (실제 호출 테스트)
- agent 로딩 여부
- skill 인식 여부
- 중복 규칙
- 충돌 가능성
- 기존 기능 회귀
- 테스트 가능 항목 실제 실행

**검증 X → "정상" 표시 X · "미측정" 표시**.

### 9. 최종 결과 (보고 포맷)

```text
1. 유지한 것 (KEEP)
2. 변경한 것 (CHANGE)
3. 제거한 것 (REMOVE)
4. 새로 추가한 것 (NEW)
5. 변경 근거
6. 실제 검증 결과
7. 아직 미확인 (미측정)
8. 다음에 다시 볼 항목
```

**중요**: 변경할 필요 없으면 "현재 구성이 더 낫기 때문에 변경하지 않음" 결론 OK.

## Change Budget (매 감사)

- **NEW**: 최대 2개
- **CHANGE**: 최대 5개
- **REMOVE**: 무제한 (엔트로피 낮춤 장려)

사용자 명시 승인 시만 상한 해제.

## 실행 예시

```bash
# 전체 감사
/audit-claude

# rules 만 집중 감사
/audit-claude rules

# 결과 저장
/audit-claude > .claude/state/audit-$(date +%Y%m%d).md
```

## 자동화 예시

```bash
# subagent 로 전수조사 (메인 컨텍스트 보호)
Agent(Explore, "rules/ 50개 중복 패턴 매트릭스 생성")
Agent(Explore, "agents/ 57개 역할 매핑")
Agent(code-reviewer, "hooks 134개 중 결정적 vs 경고 분류")
```

## 관련

- `.claude/rules/operating-principles.md` — SoT (10 원칙 + 역할 분리 + Change Budget)
- `.claude/scripts/recurrence-tracker.py` — 재발 추적
- `.claude/scripts/scope-lock.py` — 범위 lock
- `.claude/state/audit-findings-*.md` — 과거 감사 발견사항

## Anthropic 공식 참고 (반드시 WebSearch 로 재확인)

- Help Center: "반복 워크플로우는 Skill, deterministic 자동화·차단은 Hook, 독립 판단·검증은 Subagent"
- Operating Principles 10 조항은 Anthropic 공식 "완료는 증명" · "최소 변경" 패턴 정합
