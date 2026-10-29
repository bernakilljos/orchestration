# PoC vs 운영 Supervisor 호출 경로 비교 분석 + 범용 Planner 통합 설계 (2026-10-29)

> **근거**: 사용자 지시 (9d6c074 후속) — "SAFE_PATTERNS 추가 X · PoC → 운영 통합"
> **범위**: 분석·설계만 (큰 구현은 다음 세션 · 사용량 L2 97%)
> **원칙**: 신규 scaffold X · 기존 자산 재사용 · 임의 shell 변환 X · 패턴 무한 추가 X

## PoC vs 운영 호출 경로 매트릭스

| 단계 | PoC (test-phase1-vertical-poc.py) | 운영 (Supervisor) | 연결 상태 |
|---|---|---|---|
| **Request → Ledger** | 테스트 수동 호출 | `UserPromptSubmit hook` → `ledger_auto_register.py` → `ledger add` | ✅ **자동 작동** (R55 자동 등재 확인) |
| **Ledger → Goal** | 테스트 수동 INSERT | `request-ledger.py to-goals` → `INSERT INTO goals` | ✅ **CLI 작동** (`orca-10min-loop.py` 가 주기 호출) |
| **Goal → Task 분해** | 테스트 안 `natural_language_to_contract` | `supervisor.decompose_goal` → `_parse_natural_language` | ⚠ **부분 작동** (운영은 investigate kind · cmd=None) |
| **자연어 → cmd 변환** | **PoC SAFE_PATTERNS 2개** 매칭 | ❌ **없음** (운영 decompose 는 investigate 만) | **끊긴 지점 1** |
| **Task 실행** | 테스트 안 `subprocess.run` 직접 | `supervisor.execute_goal` → `runner.run` → `_is_allowed_cmd` → `_check_approval_gate` | ✅ **운영 완전** (cmd 있는 task 만) |
| **Verify** | **Python callable** (OS 중립) | `runner.run(verify_cmd)` + `_verify_output_passed` | ⚠ **shell verify 만** (Python callable 미지원) **끊긴 지점 2** |
| **격리** | tempdir git repo | ROOT cwd + `repair_sandbox.py` (REPAIR 체인만) | ⚠ **GENERAL 체인 격리 X** **끊긴 지점 3** |
| **독립 Verifier** | 테스트 자체 판정 | execute_goal 자가 보고 | ❌ **별도 검증자 없음** **끊긴 지점 4** |

## 끊긴 지점 4건 (실측)

### 끊긴 지점 1: 자연어 → cmd 변환 (운영 decompose 안 없음)

**현재 운영**:
- `_parse_natural_language` → `kind=investigate, cmd=None, verify=None` 반환
- `execute_goal` → `cmd` 없는 task 는 `skipped_disallowed`

**PoC 임시 해결**:
- SAFE_PATTERNS 2개 (`append_line_to_file`·`create_file`)
- 테스트 내부에서만 cmd 생성

**사용자 지시 "SAFE_PATTERNS 추가 X"**: 패턴 늘리기 금지 → **범용 Planner 필요** (코드베이스 조사·LLM 호출·Agent 선택)

### 끊긴 지점 2: Verify Python callable 미지원

**현재 운영**:
- `verify_pass = _verify_output_passed(stdout, stderr, exit_code)` — shell verify_cmd 의 stdout 분석만
- Python callable (OS·encoding 중립) 미지원

**PoC 임시 해결**:
- `verify_fn` lambda · Python 함수 호출

**통합 방향** (다음 세션):
- Task spec 에 `verify_type: "shell"|"python"` 추가
- `execute_goal` 안 verify_type 분기 (shell → runner.run · python → importlib + callable)

### 끊긴 지점 3: GENERAL 체인 격리 미연결

**현재 운영**:
- REPAIR 체인만 `repair_sandbox.py` 호출 (worktree 격리)
- GENERAL 체인 execute_goal 은 ROOT cwd 에서 직접 실행 (운영 코드 영향 가능)

**PoC 임시 해결**:
- tempdir git repo (별도 격리)

**통합 방향** (다음 세션):
- `execute_goal` 호출 전 `repair_sandbox.create(goal_id)` 재사용
- 성공 시 fast-forward merge · 실패 시 discard
- 사용자 지시 "임의 Shell 변환 X · 격리 수행" 정합

### 끊긴 지점 4: 독립 Verifier 없음

**현재 운영**:
- `execute_goal` 자체 결과 (executed·verified·failed) 보고
- 사용자 요구사항 충족 여부 **독립 확인 X**

**사용자 명시**: "개발 Agent 성공 주장만으로 VERIFIED X · 독립 Verifier"

**통합 방향** (다음 세션):
- `.claude/agents/agent-01-judge.md` (Haiku 4.5) 재사용
- execute_goal 결과 → judge agent 입력 → PASS/PARTIAL/FAIL 재판정

## 통합 설계 (다음 세션 범위 · 사용자 승인 받고 진행)

### Phase 2-A: Verify Python callable (CHANGE 1 · 저위험)

**변경**: `supervisor.execute_goal`
- Task spec `verify_type` 필드 지원
- `verify_type == "python"` → `verify_module.verify_fn(context) → (ok, note)`
- 기본 `verify_type == "shell"` (호환 유지)

**영향**: 운영 goal 중 verify 가 shell 인 것은 그대로 · 신규 Python callable task 만 추가 분기

### Phase 2-B: GENERAL 체인 worktree 격리 (CHANGE 2)

**변경**: `supervisor.execute_goal`
- 호출 전 `repair_sandbox.create(goal_id)` 재사용
- 격리된 cwd 에서 `runner.run` 호출
- 성공 → `apply_merge` · 실패 → `discard`
- `safe_mode: bool` task spec 필드 (true 시만 격리 활성 · 기본 false 호환)

### Phase 2-C: 독립 Verifier 연결 (CHANGE 1)

**변경**: `supervisor.execute_goal` 완료 후
- `agent-01-judge.md` 재사용 (Haiku 격리 호출)
- 입력: goal description + 실제 diff + runner 결과
- 출력: PASS / PARTIAL / FAIL
- failed=0 but judge=FAIL → `REPAIRING` 전환

### Phase 2-D: 범용 Planner (NEW 1 · 큰 작업)

**사용자 명시**: "SAFE_PATTERNS 추가 X · 실제 코드베이스 조사"

**설계 (scaffold)**:
- `supervisor._parse_natural_language` → `investigate` kind 유지 (현재)
- 추가: `supervisor.plan_investigation(goal_id)` 신규 함수
  - 입력: investigate task · description
  - 처리: Grep/Glob 으로 **실 코드베이스 조사** (사용자 명시 "실제 파일·명령 평가")
  - 출력: 조사 결과 요약 → task 승격 제안 (cmd + verify + risk)
  - **승인 필요**: investigate → cmd task 승격 전 사용자 승인 (현재 approval-gate 재사용)

**신규 호출**: `supervisor.plan_investigation` (NEW 1) · LLM 호출 X · Grep/Glob 만 사용

### Phase 2-E: UserPromptSubmit → Supervisor advance 자동 연결 (CHANGE 1)

**현재**: `Stop hook stop-six-guards.sh` 가 `advance_all_pending(trigger_source="stop_hook")` 호출
**추가**: `UserPromptSubmit hook` 에서도 `advance_all_pending` 호출 (즉시 반응)
**영향**: 사용자 요청 직후 PENDING → PLANNING 자동 전환

## 예산 (다음 세션)

| Phase | 작업 | 예산 |
|---|---|---|
| 2-A | Verify Python callable | CHANGE 1 (supervisor.execute_goal) |
| 2-B | worktree 격리 | CHANGE 2 (supervisor.execute_goal · repair_sandbox 재사용) |
| 2-C | 독립 Verifier | CHANGE 1 (supervisor.execute_goal · agent-01-judge 재사용) |
| 2-D | 범용 Planner | NEW 1 (supervisor.plan_investigation) · Grep/Glob 만 |
| 2-E | UserPromptSubmit 자동 advance | CHANGE 1 (hook or supervisor) |
| 종단 테스트 | 운영 호출 경로 종단 (ledger_auto_register 자동) | NEW 1 (test-phase2-operational-e2e.py) |

**총**: NEW 2 · CHANGE 5 · 큰 작업 (다음 세션 승인 후)

## 이번 세션 (실 변경 없음)

- NEW 1 (이 분석 문서)
- CHANGE 0
- 사용자 명시 "SAFE_PATTERNS 추가 X · 테스트 추가 X" 준수

## 미완료·BLOCKED (사용자 결정 대기)

| 항목 | 상태 | 해제 조건 |
|---|---|---|
| GitHub PAT 폐기 | **BLOCKED** | 사용자 GitHub Settings 폐기·재발급 확인 |
| 운영 호출 경로 통합 | **다음 세션** | Phase 2-A~E 승인 |
| 범용 Planner (LLM 호출) | **다음 세션** | Phase 2-D 설계 승인 (Grep/Glob 기반) |
| Multi-Agent DAG | **Phase 4** | Phase 2 완료 후 |

## 사용자 명시 반영 체크리스트

| 지시 | 반영 |
|---|---|
| SAFE_PATTERNS 추가 X | ✅ 분석만 · PoC 2 패턴 유지 |
| 테스트 전용 구현 운영 착각 X | ✅ 4 끊긴 지점 명시 |
| 범용 Planner 설계 | ✅ Phase 2-D scaffold |
| 임의 Shell 변환 X | ✅ Grep/Glob + 사용자 승인 |
| 독립 Verifier | ✅ Phase 2-C agent-01-judge 재사용 |
| 격리 환경 | ✅ Phase 2-B repair_sandbox 재사용 |
| 운영 DB·Git 보호 | ✅ safe_mode flag · 호환 유지 |

## 관련

- `.claude/scripts/lib/supervisor.py` (advance_all_pending · execute_goal · decompose_goal)
- `.claude/scripts/lib/runner.py` (실 cmd 실행)
- `.claude/scripts/lib/repair_sandbox.py` (worktree 격리 · 재사용)
- `.claude/agents/agent-01-judge.md` (독립 Verifier · 재사용)
- `.claude/scripts/test-phase1-vertical-poc.py` (PoC · 참조)
- `docs/WORKFLOW_FAILURE_ANALYSIS_2026-10-29.md` (f945902 분석)
- `docs/MULTI_REQUEST_E2E_SURVEY_2026-10-29.md` (687fed0 실측)
