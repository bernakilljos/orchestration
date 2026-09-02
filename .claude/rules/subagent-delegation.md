# Sub-agent 자동 위임 룰

> **근거**: 2026-09-02 · 컨텍스트 절약·병렬화. v2.1.232 subagent forking·nesting depth 3.

## 절대 룰

**대량 처리·격리 필요·병렬 가능 = 즉시 sub-agent 위임. 메인 컨텍스트 오염 방지.**

## 위임 매트릭스

| 상황 | Agent | 이유 |
|---|---|---|
| 대량 파일 검색 (5+ 파일 read) | **Explore** | 읽기 전용·컨텍스트 격리·결과 요약만 |
| 코드 설계·플랜 | **Plan** | Edit X·설계만·안전 |
| 검증·채점 (0~10) | **Judge** (Haiku 4.5) | 빠름·저비용·객관 |
| 복잡 리서치 (3+ 쿼리) | **general-purpose** | 병렬 dispatch |
| 코드 리뷰 | **code-reviewer / superpowers:code-reviewer** | 격리·구조화 반환 |
| 테스트 실행 | **test-runner** | stack trace 격리 |

## 병렬 dispatch (v2.1.232)

**독립 작업 여러 개** = 단일 메시지에서 여러 Agent 병렬 호출.

```text
Agent(Explore, "kit rule 분석") + Agent(Explore, "install 자산 분석") + Agent(Explore, "MCP 상태") 병렬
```

= 3배 속도.

## Fork subagent (v2.1.232)

`subagent_type: "fork"` = 전체 대화+prompt cache 상속. Live teammates 아니면 background.

## Nesting depth (v2.1.232)

- **default depth = 3** (subagent 가 sub-sub-agent spawn 가능)
- `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` 로 nesting 비활성 (컨텍스트 폭주 방지)

## 위임 안 하는 경우

| 상황 | 이유 |
|---|---|
| 1~2 파일 read | 오버헤드 |
| 사용자와 대화 진행 중 | 컨텍스트 유지 |
| 상태 유지 필요한 편집 | 메인 세션 |
| 확실치 않은 결과 | 스스로 확인 |

## 자동 트리거

- "전수조사" · "100% Read" · "모든 파일" → Explore 병렬
- "설계" · "플랜" · "계획" · EnterPlanMode 전 → Plan
- "검증" · "채점" · "리뷰" → Judge
- 대량 리서치 (`Grep` 결과 20+ hits) → Explore

## 관련

- `.claude/rules/failure-mode.md` § 전수조사
- `superpowers:dispatching-parallel-agents` skill
- v2.1.232 subagent fork·nesting changelog
