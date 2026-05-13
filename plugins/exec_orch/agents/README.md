# Agent Index — exec_orch + eval_quality

> **목적**: 어떤 에이전트가 언제·왜 호출되는지 한눈에 파악.
> **두 종류**: ① **메인 워커** (파이프라인 단계별 모델) ② **격리 Subagents** (컨텍스트 보호)

---

## 1. 메인 워커 (Pipeline Roles)

이미지 #6 LAYER 4 의 일반적 의미가 아닌, **오케스트레이션 파이프라인의 단계별 역할 정의**.
직접 호출하기보다 `exec_orch` 가 단계 진입 시 자동 매핑.

| # | 파일 | 이름 | 모델 | 역할 | 트리거 |
|---|---|---|---|---|---|
| 01 | `agent-01-team-lead.md` | **Team Lead** | Claude Opus 4.7 | 설계·승인·gate 통과 결정. 코드 직접 작성 X | 모든 파이프라인 시작 |
| 02 | `agent-02-implementer.md` | **Implementer** | Codex (×4) | task-instruction 범위 내 구현만 (Writer=1) | 500줄+ 구현 위임 |
| 03 | `agent-03-reviewer.md` | **Reviewer** | Gemini Flash | 보안·품질·최신패턴 비교. 코드 수정 X (의견만) | post-impl 검증 |
| 04 | `agent-04-architect.md` | **Architect** | Claude Opus 4.7 | 복잡 설계 — 대안 비교·구조 결정·DB 스키마 | 신규 기능·3+ 파일 영향·인증 관련 |
| 05 | `agent-05-monitor.md` | **Monitor** | Bash 스크립트 | PM2·Nginx·포트·디스크·메모리 헬스체크 | 배포 직후·이상 감지 시 rollback 트리거 |
| 06 | `agent-06-designer.md` | **Designer** | Claude + MCP | UI 자산 생성 — Canva·DALL-E·Figma·Video | UI 신규·디자인 자산 요청 |

**파이프라인 흐름**: `01 Team Lead` → `04 Architect` (필요 시) → `02 Implementer` → `03 Reviewer` → `05 Monitor` (배포 후)

---

## 2. 격리 Subagents (Context Protection)

이미지 #5 결정트리의 정석 SUBAGENTS. **메인 컨텍스트를 더럽히지 않고 결과만 반환**.
Anthropic 표준 frontmatter (`name`·`tools`·`model`) 채택.

| # | 파일 | name | 모델 | 도구 | 사용 시점 |
|---|---|---|---|---|---|
| 07 | `agent-07-code-reviewer.md` | **code-reviewer** | sonnet | Read, Grep, Glob, Bash | 커밋 직전·PR 생성 전·완료 보고 전 |
| 08 | `agent-08-test-runner.md` | **test-runner** | sonnet | Bash, Read, Grep | 구현 직후·CI 실패·flaky 재현 |
| 09 | `agent-09-explorer.md` | **explorer** | sonnet | Glob, Grep, Read, Bash | 낯선 영역 진입·심볼 검색·패턴 위치 파악 |

**왜 격리?** 이미지 #3 의 #2 "Context Decay" 방지. 거대한 grep 결과·stack trace·diff 가 메인 대화에 누적되지 않음.

---

## 3. eval_quality 의 Subagent

| 파일 | name | 모델 | 도구 | 사용 시점 |
|---|---|---|---|---|
| `plugins/eval_quality/agents/agent-01-judge.md` | **judge** | haiku | Read, Bash | post-impl 자동·`/score-task` 수동·cross-check |

LLM-as-judge 로 결과물 0~10 점수화 → `.claude/state/evaluations.jsonl` 누적.

---

## 4. 결정 가이드 — 어떤 걸 호출?

```
질문 → 카테고리?

작업 위임 (구현/리뷰/배포)        → 메인 워커 (01~06) — exec_orch 가 자동
탐색·점검만 필요 (수정 X)          → 격리 Subagents (07~09)
품질 점수 매기기                   → judge (eval_quality)
```

### 자주 쓰는 패턴

| 상황 | 호출 순서 |
|---|---|
| 새 영역 디버깅 | `09 explorer` → `08 test-runner` → (필요 시) `07 code-reviewer` |
| PR 직전 점검 | `07 code-reviewer` → `judge` (점수 확인) |
| 큰 기능 구현 | `01 team-lead` → `04 architect` → `02 implementer` → `08 test-runner` → `03 reviewer` → `judge` |
| CI 실패 진단 | `08 test-runner` → `09 explorer` (의심 모듈) |

---

## 5. 호출 방법

### 메인 워커
- 자동: `exec_orch` 가 task-instruction.md 의 단계에 따라 매핑
- 수동: 해당 에이전트 파일의 "Execution Method" 섹션 명령 직접 실행

### 격리 Subagents
- Claude Code 내장: `Task` 툴에 `subagent_type: code-reviewer` 등 지정
- 또는 `@subagent: code-reviewer "변경사항 리뷰"` 패턴 (호환되는 환경에서)

### Judge (점수)
- 슬래시: `/score-task <task-file> <result-file>`
- 자동: post-impl hook (Stop 단계 등록 시)
- 직접: `bash plugins/eval_quality/scripts/score_task.sh --auto`

---

## 6. 추가/수정 시 규칙

- 파일명: `agent-NN-<role>.md` (NN = 두자리 번호)
- 격리 subagent 는 frontmatter 필수 (`name`·`description`·`tools`·`model`)
- 메인 워커는 frontmatter 선택, 역할·실행방법·금지 섹션 필수
- 새 에이전트 추가 시 이 INDEX 표에도 한 줄 추가
- 검증: `python .claude/scripts/validate-plugin-schema.py exec_orch`

## 참조

- 이미지: `docs/screens/arch/클로드코드-아키텍처-결정트리-판데이.jpg` (#5 결정트리)
- 이미지: `docs/screens/arch/에이전트개발킷-5레이어구조-판데이.jpg` (#6 5레이어)
- 룰: `.claude/rules/file-naming.md` (agent 파일명 규약)
- 룰: `.claude/rules/failure-mode.md` (subagent 의 confidence/거절 룰)
- 평가: `plugins/eval_quality/README.md` (LLM-as-judge)
