# 다중 지시 종단 · Self-Healing · Discovery · Multi-Agent 실측 분석 (2026-10-29)

> **근거**: 사용자 지시 (037a629 후속) "01~08 51/51 PASS 는 구조 검증 · 실 운영 종단 다름 · 실측 분석 후 범위 승인"
> **원칙**: 수정 X · 호출 경로 실측 · 각 단계 가동 수준 명시 · 거짓 PASS 금지
> **보조 수정** (P0): request-ledger.py 에 `out-of-scope` 서브커맨드 신설 · R44·R45 재분류

## P0 완료: R44·R45 OUT_OF_SCOPE 재분류

### 사용자 지적

> "다른 프로젝트의 요청이라는 이유로 complete 처리하면, 사용자 입장에서는 작업이 끝난 것으로 보일 수 있다"

### 수정 내용

| 항목 | 변경 |
|---|---|
| `request-ledger.py` | `out-of-scope <rid> --target <path> --reason ...` 서브커맨드 추가 |
| status 분리 | `out_of_scope` ≠ `completed` (별도 상태) · `handoff_target` · `handoff_reason` 기록 |
| gate 통과 조건 | `completed`·`deferred`·`out_of_scope` 모두 "진행 가능" 으로 간주 (완료 X) |
| status 표시 | ✓ (completed) · ↷ (out_of_scope · 범위 외) · ⏭ (deferred) · ☐ (pending) 구분 |

### 재분류 결과

| ID | 이전 | 현재 | handoff_target |
|---|---|---|---|
| R44 | completed (오해 유발) | **out_of_scope** | C:/pjt/Project1.5 |
| R45 | pending | **out_of_scope** | C:/pjt/Project1.5 |

### 실제 인계 증거

**사용자 책임**: Project1.5 세션에서 해당 요청 등재 필요. 이 세션은 "orchestration_v1 kit 범위 아님" 만 명시.

---

## P1 다중 지시 종단 · 실측 결과

### 호출 경로 각 단계 가동 수준 (엄격 분류)

| 단계 | 가동 | 수준 | 실측 증거 |
|---|---|---|---|
| **1. UserPromptSubmit → Ledger 자동 등재** | ✅ | **VERIFIED** | `ledger_auto_register.py` 가동 · 이 세션 R42·R44·R45 자동 등재 확인 |
| **2. Ledger → Goal 변환 (to-goals)** | ✅ | **VERIFIED** | 실행: `[ledger→goal] created=1 skipped_existing=0` · goal_id 47 생성 |
| **3. Supervisor advance (PENDING → PLANNING)** | ✅ | **VERIFIED** | `advance_all_pending --dry` 호출 성공 · PENDING 1건 처리 |
| **4. Goal → Task 분해** | ⚠ | **PARTIAL** | `goal_tasks` 테이블 18 rows 존재 · 명시 분해 함수 X · 호출자 미확인 |
| **5. Task → Runner dispatch** | ⚠ | **PARTIAL** | hook 등록 · 실 Runner 호출 코드 미완 (dispatch 는 skill 지시 수준) |
| **6. Snapshot pre → 수정 → post → diff 자동** | ⚠ | **PARTIAL** | workflow-run 수동 호출만 작동 · 자동 트리거 (hook) X |
| **7. 06-verify 전수 (test·standing·golden·mojibake)** | ⚠ | **PARTIAL** | yaml step 등록 · 자동 트리거 X · 수동 호출만 |
| **8. 08-learn 자동 호출** | ⚠ | **PARTIAL** | yaml 등록 · 수동 workflow-run 로만 작동 |

### 51/51 PASS 와 실 운영 종단 구분 (사용자 지적 반영)

| 범위 | 상태 |
|---|---|
| **01~08 체인 구조 검증** (yaml 로드·CLI 매칭·snapshot 단독·memory 안전 장치) | VERIFIED (51/51) |
| **실 사용자 요청 자동 종단** (UserPromptSubmit → Verification → Learning 자동 트리거) | **PARTIAL** (1~3 자동 · 4~8 수동) |

### 요청 보존 (사용자 지시 "요청 유실 없음")

- 이 세션 Ledger: 44/46 완료 + 2 OUT_OF_SCOPE + 1 pending (현재 작업)
- 각 request 독립 보존 확인 (R1~R46 전수)
- 세션 재시작 복원: SessionStart hook resume-last-24h 가 next-actions.md + Ledger 로드

### 아직 운영 종단으로 **승격 금지** (사용자 지시)

- 1~3 단계 자동 · **VERIFIED**
- 4~8 단계 **PARTIAL** · 자동 트리거 미연결
- **실 다중 지시 자율 개발 종단은 아직 VERIFIED 아님**

---

## P1-P2 분석 · 수정 X · 범위 명시

### Self-Healing 호출 경로

| 자산 | 상태 | 자동 트리거 |
|---|---|---|
| `lib/repair_sandbox.py` | **IMPLEMENTED** (완전 구현: create/test/apply/discard) | **없음** (수동 호출만) |
| `diagnose-failure.py` | SCAFFOLD (stub exit 0 · "실 LLM 분석은 다음 세션") | **없음** |
| Supervisor REPAIRING 상태 | **IMPLEMENTED** (status 전환 로직 있음) | 자동 advance 는 Stop hook 로 호출 |
| 07-repair workflow yaml | **IMPLEMENTED** (step 6개 등록) | workflow-run 수동 호출만 |

**실제 Self-Healing 가동 수준**: 자동 트리거 **없음** · 자산은 있지만 **연결 안 됨**. "실패 감지 → 격리 → 수정 → 재검증" 자동 흐름 **미구현**.

### Universal Technology Discovery 호출 경로

| 자산 | 상태 |
|---|---|
| `lib/tech_discovery.py` | **SCAFFOLD** (CLI: analyze·domain-list·research·gap · 실 WebSearch 연결 상태 확인 필요) |
| 자동 트리거 | **없음** |

### Multi-Agent Capability Registry

| 자산 | 상태 |
|---|---|
| 중앙 Registry 파일 | **없음** (`.claude/config/agent-registry.*` 미존재) |
| `.claude/agents/*.md` | 19개 (Claude Code 자동 탐색) |
| `plugins/*/agents/*.md` | 29개 (대부분 sync 결과물 · md5 동일) |
| Agent 능력 선언 (capability) | **없음** (각 agent.md 는 description 만 · 구조화 X) |
| Task → Agent 자동 매칭 | **없음** |

**실측 결론**:
- Self-Healing: 자산은 있지만 자동 연결 **없음**
- Discovery: scaffold 수준 · WebSearch 연결 확인 필요
- Multi-Agent: 중앙 Registry **없음** · capability 선언 **없음**

---

## 다음 세션 범위 승인 요청 (사용자 명시 "범위 승인 후 진행")

### Option A — P1 다중 지시 자동 종단 완성 (최소)

범위: 4~8 단계 자동 트리거 연결
- Goal → Task 분해 함수 명시 (goal_tasks 테이블 활용)
- Task → Runner 자동 dispatch
- Snapshot 자동 호출 hook
- Verification 자동 트리거
- Learn 자동 호출

예상: NEW 3~5 · CHANGE 5~8 (호환성 영향 중간)

### Option B — Self-Healing 실전 연결 (중간)

범위: diagnose + repair_sandbox + Supervisor REPAIRING 체인 연결
- diagnose-failure.py stub → LLM 분석 연결
- Supervisor REPAIRING 상태 자동 전환
- repair_sandbox 자동 호출 트리거

예상: NEW 2 · CHANGE 3~5

### Option C — Discovery + Multi-Agent (후반)

범위:
- tech_discovery.py WebSearch 연결 확인/수정
- Agent Capability Registry 신설 (`.claude/config/agent-capability.yaml`)
- Task → Agent 자동 매칭

예상: NEW 2 · CHANGE 3

### Option D — 분석만 (수정 X)

범위: 이 문서 유지 · 다음 세션에 어느 Option 진행할지 사용자 결정 · 수정 0건 · commit 1 (이 문서 + ledger 수정만)

---

## 회귀

| 테스트 | 결과 |
|---|---|
| golden-test.py | **13/13 PASS** |
| test-h1-h2-h4-e2e.py | **68/68 PASS** |
| test-workflow-run-e2e.py | **5/5 PASS** |
| test-workflow-full-chain-e2e.py | **51/51 PASS** |

**수정 범위**: request-ledger.py CHANGE 1 (out-of-scope 서브커맨드) + docs NEW 1

### Operating Principles

- Statusline FROZEN · 승인 정책 X · 계정 전환 X
- Change Budget: NEW 1 (docs) · CHANGE 1 (request-ledger.py)
- 범위 외 승격 X · 51/51 을 운영 종단으로 확대 해석 X
- 실측 결과만 보고 · 추측 X

## 관련

- `docs/WORKFLOW_FAILURE_ANALYSIS_2026-10-29.md` (f945902)
- `docs/P0B_STATUS_MATRIX_2026-10-29.md` (5e242cc)
- `docs/MEDIUM_RECLASSIFY_2026-10-29.md` (b40ecbd)
- `.claude/scripts/request-ledger.py` (out-of-scope 서브커맨드 추가)
- `.claude/scripts/lib/supervisor.py` (advance_all_pending)
- `.claude/scripts/lib/repair_sandbox.py` (Self-Healing 자산)
- `.claude/scripts/lib/tech_discovery.py` (Discovery scaffold)
