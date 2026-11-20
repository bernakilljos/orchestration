---
paths:
  - ".claude/tasks/**"
  - "plugins/exec_orch/codex/**"
  - "plugins/exec_orch/skills/route_dispatch.md"
  - ".claude/agents/**"
---

# Sub-agent 자동 위임 룰

> **근거**: 2026-09-02 · 컨텍스트 절약·병렬화. v2.1.232 subagent forking·nesting depth 3.
> **SoT 통합 (2026-10-26)**: 적응형 실행 매트릭스는 **`.claude/rules/execution-contract.md § 7`** 가 SoT. 이 파일은 매트릭스 참조 + Explore/Plan/Judge 역할 설명만 유지.

## 절대 룰

**기본은 메인 직접 실행. 위임은 서로 독립이고 결과만 필요한 일일 때 최대 2개로 시작하고, 같은 종류 작업에서 더 빨랐다는 실측이 있을 때만 늘린다 (R333).**
- R333 실측 (2026-11-18~19 · 15건): 서브에이전트 호출은 3건뿐이었고 병목이 아니었다. 다만 읽기 조사 1건이 Opus 를 물려받아 280초 · 입력 155만 토큰을 썼다 → 읽기 조사 위임은 가벼운 모델로 · 위임보다 Grep·Read 직접이 빠른 범위(파일 수십 개 이하)는 직접.
- 아래 표는 «위임해도 되는 상황» 목록이지 «반드시 위임» 기준이 아니다 (5+ 파일·500줄 같은 숫자만으로 위임하지 않는다).
**실행 방식 결정 (직접·병렬·worktree·Codex·순차) 은 `execution-contract.md § 7 상황 적응형 실행` 매트릭스 참조.**

## 역할별 Agent (위임을 «고려할 수 있는» 상황 · 자동 아님 · R337 2026-11-20)

파일 수·줄 수·단어 같은 숫자 하나로 위임하지 않는다. 판단 축은 `execution-contract.md § 7` (규모·의존성·쓰기 충돌·위험·비용) 하나다.

| 상황 | 고를 수 있는 Agent | 위임이 이득일 때 | 메인 직접이 나을 때 |
|---|---|---|---|
| 넓은 읽기 조사 | **Explore** (가벼운 모델) | 서로 독립인 여러 영역 · 결론만 필요 | 대상 위치를 알거나 파일 수십 개 이하 (Grep·Read 가 더 빠름) |
| 설계·플랜 | **Plan** | 큰 구조 결정 · 구현자와 다른 시각 필요 | 작은 변경 |
| 검증·채점 | **Judge** (Haiku) | 결과를 독립적으로 다시 볼 때 | 실행 결과로 바로 판정 가능할 때 |
| 독립 구현 여러 건 | **general-purpose** (적은 수부터) | 결과 결합이 명확하고 쓰기 충돌 없음 | 같은 파일·공유 상태 · 순차 의존 |
| 코드 리뷰 | **code-reviewer** | 구현자와 분리된 결함 찾기 | — |
| 테스트 실행 | **test-runner** | 긴 실패 출력 격리 | 짧은 관련 시험 |

- 사용자가 «Codex 써»·«병렬로 해» 라고 명시하면 그대로 따른다 (가용성·위험만 확인).
- 위임해도 통합·검증·최종 보고 책임은 메인 (§ 7 «메인 Claude 책임»).

## Codex·멀티 AI

- 호출 가능 여부(CLI·키) · 작업 적합성 · 총 비용(지시서 작성·대기·회수·재검증 포함) · 사용자 지시로 정한다 (SoT `execution-contract.md § 4`).
- 토큰 절약만을 이유로 검증 품질을 낮추지 않는다.

## 병렬 dispatch (v2.1.232)

독립 작업 여러 개는 한 메시지에서 여러 Agent 를 병렬로 부를 수 있다.

```text
Agent(Explore, "kit rule 분석") + Agent(Explore, "MCP 상태") 병렬
```

N 개를 병렬로 돌려도 N 배 빨라진다고 적지 않는다 — 최종 완료 시간에는 시작·설명·대기·통합·검증·재작업이 들어간다 (R333 실측: 읽기 조사 1건 280초 · 입력 155만 토큰).

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

## 단어 감지 (판단 재료일 뿐 · R337)

- 프롬프트 훅이 «전수조사»·«100% read» 같은 단어를 보면 위임을 «검토» 하라는 힌트만 준다 — 위임 지시가 아니다.
- 실제 선택은 위 표와 § 7 로 한다. 단어만 보고 Agent 를 띄우지 않는다.

## 관련

- `.claude/rules/failure-mode.md` § 전수조사
- `superpowers:dispatching-parallel-agents` skill
- v2.1.232 subagent fork·nesting changelog
