# Workflow 운영 실패 분석 — Phase 1·2 완료 (2026-10-29)

> **근거**: 사용자 지시 "분석 완료와 복구 완료를 구분한다" · "증거 없이 결함이라고 단정하지 않는다" · "Goal 상태 일괄 변경 금지"
> **범위**: 42 goals + workflow-run.log 2회 실행 분석. **코드 변경 0건**.

## 핵심 결론

**25 FAILED 는 운영 결함이 아니라 scaffold 노출 + 테스트 축적**.

| 축 | 발견 |
|---|---|
| 25 FAILED goals 성격 | **테스트/cleanup 20건 + 테스트 유발 REPAIR 5건** · 실 사용자 작업 유발 결함 0건 |
| workflow-run.log 2회 FAIL | **scaffold 스크립트 미존재 2건 + CLI 서브커맨드 불일치 1건 + 호출 순서 1건** |
| 실제 사용자 작업 실패 | **0건** (ledger:R1~R5 는 숫자 하드코딩 sim 세션의 register_goal 테스트) |

→ **운영 결함 X · workflow-run 엔진 scaffold 상태 노출**. 수정 전 설계 결정 (사용자 승인) 필요.

---

## Phase 1 · 42 goals 전수 분석

### Status 분포

| status | count |
|---|---|
| FAILED | 25 |
| VERIFIED | 15 |
| BLOCKED | 1 (G18 · RPA target 외부 의존 · 이미 BLOCKED 명시) |
| RUNNING | 1 |

### workflow_type

| type | count |
|---|---|
| GENERAL | 38 |
| REPAIR | 4 |

### 생성 날짜

- 2026-10-26: 1 (G3)
- 2026-10-27: 30 (대부분 테스트)
- 2026-10-28: 11

### FAILED 25건 재분류 (failure_reason 기준)

| 카테고리 | 건수 | 성격 | 예시 |
|---|---|---|---|
| test_cleanup | 16 | **의도된 테스트** | G6 "[TEST] restart recovery sim" · G22 "[E2E-FAIL]" · G28 "[CLAIM-TEST]" |
| cleanup | 4 | **cleanup** | G12/13 "TEST E BLOCKED/INDEPENDENT" · G35/36 "[SELF-HEAL-*]" |
| retry_limit | 3 | **REPAIR 재시도 소진** | G29 "verify=echo NOT OK" (의도된 실패) · G37/44 재발 자동 해결 |
| timeout | 1 | **12h 초과** | G3 REPAIR rule=증명지시 |
| no_fault | 1 | **"no real fault"** | G7 REPAIR trivial (명시 "no real fault") |

### source_ref 분포 (25건)

| source_ref | count | 성격 |
|---|---|---|
| (empty) | 12 | 수동 테스트 |
| ledger:R1~R5 | 5 | **register_goal 테스트** (설명 "[R1] 작업 1" 숫자 하드코딩 sim) |
| rule:* | 4 | REPAIR auto-advance 재발 처리 테스트 |
| verify:cmd:* | 3 | verify 커맨드 테스트 |
| scheduler_only:natural_cycle_test | 1 | 스케줄러 테스트 |

### 과거 vs 현재 재현

- 모든 FAILED goals: **2026-10-26 ~ 10-28 생성** (3일 간 테스트 축적)
- 2026-10-29 (오늘) 생성 FAILED 0건
- **현재 활성 결함 아님** · 테스트 하네스 결과 축적

---

## Phase 2 · workflow-run.log 2회 FAIL 재현

### 실행 이력 (전체 73줄)

- **2026-10-27 14:20:39** 1차 실행 — 01-goal register_goal FAIL · 07-repair diagnose FAIL
- **2026-10-27 14:21:12** 2차 실행 (session_id/goal_id 추가 입력) — 06-verify pre_post_snapshot FAIL → 07-repair diagnose FAIL
- **2026-10-27 14:35:21** 3차 실행 — 06-verify run_tests FAIL → 07-repair isolate_sandbox FAIL
- **2026-10-27 14:35:22** 4차 실행 — 01-goal parse_requests FAIL

### 각 FAIL 재현 결과 (오늘)

| 체인·step | 호출 스크립트·args | 실제 재현 결과 | 근본 원인 |
|---|---|---|---|
| 01-goal `parse_requests` | `request-ledger.py parse "{user_prompt}"` | **invalid choice: 'parse'** (choices: add/add-batch/complete/status/gate/clear/to-goals) | **yaml 과 CLI 불일치** · parse 서브커맨드 없음 |
| 01-goal `register_goal` | `lib/supervisor.py create --prompt ... --session ...` | (파일 존재 · 입력 세션 ID 필요) | **입력 누락** (1차 실행 session_id 없음) |
| 06-verify `pre_post_snapshot` | `lib/snapshot.py diff --files ...` | `{"error": "pre.json or post.json missing"}` · exit 0 | **호출 순서 전제** (pre/post 먼저 호출 필요) |
| 06-verify `run_tests` | `run-language-tests.sh --changed ...` | **파일 없음** (`run-language-tests.sh` 존재 X) | **scaffold 스크립트 미존재** |
| 07-repair `diagnose` | `diagnose-failure.py --report ...` | stub · exit 0 (`"note": "stub · 실 LLM 분석은 다음 세션"`) | workflow-run.py FAIL 판정 로직 (exit 0 인데 FAIL 로 기록 — 재조사 필요) |
| 07-repair `isolate_sandbox` | `worktree-dispatch.py sandbox --goal ...` | **파일 없음** | **scaffold 스크립트 미존재** |

### 근본 원인 그룹핑

| 그룹 | 결함 | 영향 | 수정 복잡도 |
|---|---|---|---|
| **A. 스크립트 미존재** | `run-language-tests.sh` · `worktree-dispatch.py` | 06-verify · 07-repair 체인 영구 FAIL | 중 (신규 작성 2건) |
| **B. CLI 서브커맨드 불일치** | `request-ledger.py parse` 호출 (실제 add 등) | 01-goal 체인 영구 FAIL | 저 (yaml 또는 CLI 수정) |
| **C. 호출 순서 전제** | `snapshot.py pre.json` 선행 필요 | 06-verify pre_post_snapshot stub | 저 (workflow 재설계) |
| **D. workflow-run 엔진 판정** | stub exit 0 인데 FAIL 로 기록 (14:21:12 diagnose) | 로그 정확성 | 저 (판정 로직 확인) |

### 25 FAILED goals 와 workflow-run FAIL 의 관계

**관계 없음** (별도 축):
- 25 FAILED goals: supervisor.py 가 **독립 호출** 로 생성 (lib/supervisor.py create · auto-advance · timeout)
- workflow-run.log FAIL: **workflow-run.py** 가 yaml chain 실행 중 생긴 결함
- workflow-run.py 는 **2026-10-27 추가** (R19 minimal 엔진) · scaffold 수준

→ workflow-run 엔진 scaffold 는 **25 FAILED goals 를 유발 X** (별도 축).

---

## 실제 수정 대상 (사용자 승인 필요)

### 결함 분류

| ID | 결함 | 상태 | 수정 승인 필요? |
|---|---|---|---|
| F1 | `run-language-tests.sh` 미존재 | **실 결함** | YES (NEW 1) |
| F2 | `worktree-dispatch.py` 미존재 | **실 결함** | YES (NEW 1) |
| F3 | `request-ledger.py parse` 서브커맨드 불일치 | **실 결함** | YES (CHANGE 1 · 저위험) |
| F4 | `snapshot.py pre.json` 호출 순서 | **설계 결함** | YES (workflow yaml 재설계) |
| F5 | 14:21:12 `diagnose` stub exit 0 → FAIL 기록 | **조사 필요** (실제 FAIL 재현 X · 로그와 재현 불일치) | NO (재현 전 수정 X) |

**사용자 지시 "증거 없이 결함이라고 단정하지 않는다"** 준수 — F5 는 **재현 안 됨** 상태.

### 수정 전 재현 테스트 (사용자 지시 Phase 3)

**필요한 재현 테스트** (수정 승인 후 작성):
1. workflow-run.py --chain 01-goal · 02~08 각 체인 FAIL/OK 재현 테스트
2. request-ledger.py 모든 서브커맨드 CLI 호환 테스트
3. snapshot.py pre→post 순서 테스트

### 수정 금지 영역 (사용자 지시)

- Goal 상태 일괄 SUCCESS 변경 X
- FAILED 기록 삭제 X
- 로그 삭제 X
- 운영 데이터 임의 변경 X

---

## 회귀 테스트 (Phase 4)

| 테스트 | 결과 |
|---|---|
| golden-test.py | **13/13 PASS** |
| test-h1-h2-h4-e2e.py | **68/68 PASS** |

**분석 작업 중 코드 변경 0건** · 회귀 영향 없음.

---

## P1 다중 지시 동적 종단 진입 가능 여부

### 평가

**조건부 가능**:
- P1 다중 지시 종단 **= workflow-run 엔진 실 가동 전제**
- workflow-run 엔진 **scaffold 상태** (F1·F2·F3·F4 미해결)
- P1 진입 전 **workflow-run 완성** 필요

### 권장 순서

1. **workflow-run 엔진 완성** (F1·F2·F3·F4 수정 + 재현 테스트)
2. workflow-run 종단 테스트 (01-goal → 08-learn 전체 OK)
3. **P1 다중 지시 동적 종단** 진입 (여러 requests → workflow chain → 완료 검증)
4. Self-Healing
5. Universal Discovery
6. 다중 Agent DAG

### 사용자 결정 사항

**Option A — 분석 종결 · 다음 세션 수정 승인**
- 이번 세션: Phase 1·2 분석 보고만 (현재 상태)
- 다음 세션: F1·F2·F3·F4 수정 + 재현 테스트 + 종단 검증

**Option B — 이번 세션 수정 착수**
- F1·F2·F3·F4 수정 (NEW 2 · CHANGE 2) → 지시 승인 받고 진행

---

## Operating Principles 준수

- Statusline FROZEN · 승인 정책 X · 계정 전환 X
- Scope Lock: 운영 중 X (opt-in)
- Change Budget: NEW 1 (이 문서) · CHANGE 0 · REMOVE 0
- 범위 외 리팩터링 X
- 지시 "분석 완료와 복구 완료를 구분한다" 준수

---

## 관련

- `docs/P0B_STATUS_MATRIX_2026-10-29.md` (P0b 종료)
- `docs/MEDIUM_RECLASSIFY_2026-10-29.md` (MEDIUM 재분류)
- `.claude/scripts/workflow-run.py` (R19 minimal 엔진)
- `.claude/workflows/*.yaml` (8개 체인 정의)
- `.claude/logs/workflow-run.log` (73줄 · 2회 실행)
- `orca.db.goals` (42 goals · 25 FAILED)
