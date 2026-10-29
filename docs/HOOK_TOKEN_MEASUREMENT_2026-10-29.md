# Hook 토큰 소비 실측 + Phase 2-E 상태 (2026-10-29)

> **근거**: 사용자 지시 (952061f 후속 · 세션 재개) — "Hook 출력 실제 측정 · Phase 2-E 자동 advance 확인"
> **범위**: 실측 + 분석만 (큰 수정은 범위 외 · 사용자 "본 개발 지연 X")

## Phase 2-E 실측 결과 — **INTEGRATED (이미 작동 중)**

### 호출 경로 (실측 확인)

| 단계 | 메커니즘 | 실측 |
|---|---|---|
| UserPromptSubmit → Ledger | `ledger_auto_register.py` (prompt-dispatch 호출) | ✅ R59, R60, R61 자동 등재 확인 |
| Ledger → Goal | `request-ledger.py to-goals` (orca-10min-loop 주기 호출) | ✅ `created=5 skipped=0` |
| Goal → advance | `supervisor.advance_all_pending` (Stop hook + scheduler) | ✅ dry-run 31 goals 처리 가능 |

**결론**: Phase 2-E 는 이미 **INTEGRATED** 상태. 신규 코드 X · 측정으로 작동 확인.

### 테스트 유발 Ledger 처리 (사용자 "허위 완료 금지")

Hook 측정 중 자동 등재된 테스트 요청:
- R59·R60·R61 → `OUT_OF_SCOPE → test:phase2e-measurement` (completed X)

## Hook 토큰 소비 실측

### 전체 UserPromptSubmit systemMessage

| 측정 | 값 |
|---|---|
| **chars** | 3,346 |
| **bytes** | 5,078 B |
| **섹션 수** | 16 |

(사용자 지적 "매 턴 5~10KB" **5KB 로 실측 수정** · 과추정)

### Top 소비 섹션 (가장 큰 조각)

| 순위 | 섹션 | chars | % |
|---|---|---|---|
| 1 | 재사용 해결책 (자동 조회) | 877 | 26% |
| 2 | auto-planner ENFORCED | 514 | 15% |
| 3 | 대상 확정 REQUIRED | 495 | 15% |
| 4 | 2중 추천 · 최근 10턴 패턴 | 358 | 11% |
| 5 | Memory recall | 341 | 10% |
| 6 | 관련 세션 요약 | 340 | 10% |
| 7 | SUGGEST skill/tool | 163 | 5% |
| 8 | 관련 이전 대화 DB | 104 | 3% |

### 토큰 환산 (근사)

- 매 턴 systemMessage: ~5KB ≈ **~1,250 토큰** (한글 4 bytes/token)
- 이번 세션 60+ 턴 → 약 **75,000 토큰** · 전체 소비 760,000 토큰의 **~10%**
- 주 소비: 대화 자체 (사용자 지시 + 응답) + 코드 Read/Write (~90%)

### 최적화 포인트 (사용자 승인 후 다음 세션)

| 섹션 | 축소 방안 | 영향 |
|---|---|---|
| 재사용 해결책 (877c) | top 3 → top 1 (sha prefix 만) | 저위험 |
| 2중 추천 (358c) | 최근 10턴 패턴 — 1줄 요약 | 저위험 |
| 관련 세션 요약 (340c) | 1 세션만 (현재 3) | 저위험 |
| 대상 확정 (495c) | 핵심 1줄 유지 | 사용자 명시 "대상 0순위" |
| auto-planner (514c) | 유지 (사용자 지시 핵심) | 사용자 명시 유지 |
| Memory recall (341c) | 유지 (재발 방지 핵심) | 유지 |

**최적화 가능 추정**: 1,575 chars 축소 가능 (약 47%) · 매 턴 ~400 토큰 절감 · 60턴당 24,000 토큰 (~3%)

**사용자 명시**: "Hook 최적화가 본 개발을 무기한 지연 X · 범위 제한"
→ **다음 세션 분리** (사용자 결정) · 이번 세션은 측정만

## Phase 2 전체 상태 매트릭스 (952061f 기준 · 재검증)

| Phase | 상태 | 증거 |
|---|---|---|
| 2-A Verifier Registry | **INTEGRATED** | commit 7432ed7 · goal 70 verify PASS |
| 2-B Worktree 격리 | **미연결** | repair_sandbox.py 자산 재사용 설계만 |
| 2-C Independent Verifier | **PARTIAL** | evidence 집계만 · LLM 평가 X |
| 2-D 범용 Planner | **미연결** | 설계 scaffold (POC_VS_OPERATIONAL docs) |
| **2-E UserPromptSubmit 자동 advance** | **INTEGRATED (이미 작동)** | **이번 세션 실측 확인** |
| 2-F 운영 수직 종단 | **미검증** | 2-B·D 완료 후 통합 |

## 다음 세션 안건 (사용자 결정 범위)

| 우선 | 작업 | 예상 범위 |
|---|---|---|
| CRITICAL | GitHub PAT 폐기 확인 (사용자 조치) | 외부 조치 |
| Phase 2-B | repair_sandbox 재사용 (worktree 격리) | CHANGE 2 |
| Phase 2-C 보완 | LLM 독립 평가 (agent-01-judge) | CHANGE 1 |
| Phase 2-D | 범용 Planner (Grep/Glob + LLM) | NEW 1 |
| Phase 2-F | 운영 수직 종단 테스트 | NEW 1 |
| Hook 최적화 | top 3 섹션 축소 (저위험) | CHANGE 1 |

## Operating Principles 준수

- Statusline FROZEN · 승인 정책 X · 계정 전환 X
- 이번 세션 코드 변경 **0건** · 측정·분석만
- 테스트 유발 ledger R59-R61 → OUT_OF_SCOPE (허위 완료 X)
- GitHub PAT BLOCKED 유지 (사용자 조치)

## 관련

- `.claude/hooks/prompt-dispatch.py` (182 lines · 모듈 라우터)
- `.claude/hooks/prompt/*.py` (19 모듈)
- `.claude/scripts/request-ledger.py` (ledger CLI + out-of-scope)
- `.claude/scripts/lib/supervisor.py` (advance_all_pending)
