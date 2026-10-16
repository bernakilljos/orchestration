# Six Guards — 반복 지시 → 시스템 규칙 승격 (SoT)

> **근거**: 2026-10-16 사용자 지시 — "statusline 만 아니라 반복해서 답답한 모든 문제를 Guard 로 묶자".
> **SoT**: 이 파일. 각 Guard = 역할 + 연결 asset (hook/rule/skill/script).
> **원칙**: 사용자가 매번 "전부 해"·"증명해"·"Codex 돌려"·"공통 써"·"디자인 건들지 마" 반복 불필요.

## Guard 매트릭스

| # | Guard | 역할 | SoT · 자산 |
|---|---|---|---|
| 1 | **Scope Guard** | 요청 밖 수정 차단 | `.claude/scripts/scope-lock.py` · `.claude/hooks/tool/scope_lock.py` · `/scope` |
| 2 | **Completion Guard** | R1~Rn 전부 완료 전 종료 금지 | `.claude/scripts/request-ledger.py` · `.claude/hooks/stop-request-ledger-gate.sh` |
| 3 | **Verification Guard** | test/build/codex/web 증거 없으면 완료 금지 | `.claude/scripts/golden-test.py` · `.claude/scripts/standing-requirements.py` (gate) · statusline `🔐 증명` |
| 4 | **Memory Guard** | 지속 요구사항 자동 재주입 (저장 ≠ 재주입) | `.claude/hooks/session-start-replay-standing.sh` · `.claude/scripts/standing-requirements.py` (replay) |
| 5 | **Quality Guard** | 디자인·공통화·하드코딩·중복·회귀 감시 | `.claude/scripts/recurrence-tracker.py` · `.claude/scripts/dedupe-rule/skill/agent.py` · statusline `📊 품질추세`·`🧩 공통화` |
| 6 | **Freeze Guard** | orchestration 임의 확장 금지 | `.claude/rules/operational-freeze.md` · Change Budget (NEW ≤ 2) |

## 1. Scope Guard

**문제**: Claude 가 요청 밖 파일·시스템을 임의 수정 (auto-planner 과거 "인접 시스템 포함" 룰 때문).

**해결**:
- `/scope activate <glob>` — opt-in 범위 지정 (24h TTL)
- PreToolUse Edit·Write 가 범위 외 target 감지 → WARN 또는 DENY
- SoT: `execution-contract.md § 3` (직접 의존성 1-hop 만)

**검증 (Stop hook)**: 이번 세션에서 범위 외 수정 없는지 git diff 로 확인.

## 2. Completion Guard

**문제**: 사용자 "A·B·C 다 해" → Claude 가 A만 하고 "완료" 보고.

**해결**:
- Request Ledger — 사용자 메시지에서 N개 request 자동 추출 → `.claude/state/request-ledger.json`
- Stop hook `stop-request-ledger-gate.sh` — N/N 완료 전 종료 차단 (exit 2)
- SoT: `execution-contract.md § 1·2`

**검증 (Stop hook)**: `python request-ledger.py gate` exit 0 = 완료 · exit 2 = 미완.

## 3. Verification Guard

**문제**: "다 했다" 뻥 · 자기보고 신뢰 X · 외부 증거 요구.

**해결**:
- Golden Test 10개 (T01~T10) — 매 구조 수정 후 회귀 검증
- Standing Requirements verify_pattern — 각 요구사항 verify_target 안 포함 확인
- statusline `🔐 증명` — git/standing/golden/test 상태 실시간
- READY 상한 — 검증 미측정 → max 70 · A 금지

**검증 (Stop hook)**:
```text
golden-test exit 0 ? → ✓
standing-requirements gate exit 0 ? → ✓
Codex 필요 시 실행 로그 존재 ? → ✓ (필요 없으면 skip)
```

## 4. Memory Guard

**문제**: 사용자 "품질추세 요청" 저장돼 있는데 다음 세션 **까먹음** (저장 ≠ 재주입).

**해결**:
- `standing-requirements.py replay` — ACTIVE 요구사항 systemMessage JSON 반환
- SessionStart hook `session-start-replay-standing.sh` — 매 세션 자동 재주입
- PostCompact / Resume / `/clear` 복구 시도 재주입
- `.claude/state/next-actions.md` — 다음 세션 즉시 이어서 할 일 (auto-save)

**현재 ACTIVE 요구사항 8건**:
- UX-STATUS-001~004 (statusline 라인 유지)
- OP-COMPLETE-001 (n/n 완료 전 보고 금지)
- OP-DESIGN-001 (디자인 임의 변경 X)
- OP-COMMON-001 (공통 컴포넌트 먼저)
- OP-CODEX-001 (Codex 명시 자동 dispatch)

## 5. Quality Guard

**문제**: 디자인 임의 변경·공통 컴포넌트 우회·CSS 중복·하드코딩 반복·같은 실수 재발.

**해결**:
- `recurrence-tracker.py` — 재발 자동 감지 + 1/2/3/5회 승격 (1=log, 2=warn, 3=CLAUDE.md 후보, 5=hook 후보)
- `dedupe-rule/skill/agent.py` — 중복 섹션·skill·agent 자동 축약
- statusline `🧩 공통화` — 재사용·우회·CSS중복·신규공통·하드코딩 실시간
- `operating-principles.md § 4` — "이미 존재하는가? 먼저 증명"

**검증**: 각 Edit·Write 전 common-component 존재 확인 (grep 자동).

## 6. Freeze Guard

**문제**: Claude 가 설정을 계속 늘림 → hook 500+·rule 100+·skill 300+ 폭증.

**해결**:
- `operational-freeze.md` — 2차 안정화 완료 후 FREEZE
- Change Budget — NEW ≤ 2 · CHANGE ≤ 5 · REMOVE 무제한
- 추가 허용 조건 (OR):
  1. 재발 3회+ 자동 승격
  2. 골든 테스트 FAIL
  3. 성능 병목 (SessionStart >5s)
  4. Claude Code 공식 기능 변경 ( 이상)
  5. 크리티컬 5가지

## 통합 Stop Hook (6 Guards 전수 검증)

```bash
# .claude/hooks/stop-six-guards.sh
1. Completion Guard: python request-ledger.py gate (exit 0 요구)
2. Verification Guard: python standing-requirements.py gate (exit 0)
3. Verification Guard: python golden-test.py (10/10 PASS)
4. Scope Guard: git diff --name-only · 범위 외 수정 체크
5. Quality Guard: recurrence-tracker 3회+ 승격 있는지 확인
6. Freeze Guard: Change Budget 안 (NEW ≤ 2)
```

하나라도 FAIL → Stop 차단 + 미완 사유 systemMessage.

## 통합 SessionStart (Memory Guard)

```bash
# .claude/hooks/session-start-six-guards.sh
1. Memory Guard: standing-requirements replay (ACTIVE 요구사항 주입)
2. Freeze Guard: operational-freeze 상태 확인 · systemMessage 알림
3. Scope Guard: 이전 세션 scope-lock 상태 복원 (있으면)
```

## 매트릭스 예시 (사용자 과거 짜증 → Guard 매핑)

| 사용자 짜증 반복 | 매핑 Guard | 자동 대응 |
|---|---|---|
| "R1,R2,R3 중 일부만 수행" | Completion Guard | Stop gate 차단 · "N/M 완료" 알림 |
| "다 안 했는데 중간 보고" | Completion + execution-contract § 2 | 중간보고 금지 (룰) · Stop gate (hook) |
| "다 했다 뻥침" | Verification Guard | Stop hook 이 golden-test·standing 실행 요구 |
| "Codex 안 씀" | Completion + classify-task | 명시 트리거 매치 시 orchestrator 자동 dispatch |
| "공통 컴포넌트 안 씀" | Quality + operating-principles § 4 | PostToolUse Edit 전 grep 체크 |
| "디자인 마음대로 변경" | Scope + execution-contract § 6 | 사용자 요청 없으면 UI 변경 X |
| "같은 실수 재발" | Quality (recurrence-tracker) | 1/2/3/5 자동 승격 |
| "이전 요청 까먹음" | Memory Guard | SessionStart replay |
| "미측정을 0으로 표시" | Verification + operating-principles § 9 | statusline ⏳ 미측정 통일 |
| "READY 뻥튀기" | Verification | READY cap 70 (검증 미측정) |
| "다른 프로젝트 전파 꼬임" | Scope (sync 룰) | sync-to-team · install-to-target 정책 분리 (다음 세션 R20·R21) |
| "hook 너무 많음" | Freeze Guard | Change Budget · dedupe-rule/agent |
| "Claude 가 설정 임의 확장" | Freeze Guard | NEW ≤ 2 상한 · operational-freeze.md |

## 관련

- CLAUDE.md § 0 Operating Principles (10 원칙)
- `execution-contract.md` (Request Ledger · n/n · 범위 lock)
- `operating-principles.md` (10 원칙 SoT)
- `operational-freeze.md` (Freeze Guard)
- `standing-requirements.py` (Memory Guard)
- `request-ledger.py` + `stop-request-ledger-gate.sh` (Completion Guard)
- `golden-test.py` (Verification Guard)
- `recurrence-tracker.py` (Quality Guard)
- `scope-lock.py` (Scope Guard)
- `/audit-claude` (Freeze Guard · 반복 감사)
- 외부 감사: `docs/ORCHESTRATION_AUDIT_2026-10-16.md`
