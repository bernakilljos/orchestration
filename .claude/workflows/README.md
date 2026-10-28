# 9-Chain Workflow YAML (P1-A)

> **근거**: 2026-10-27 사용자 "P1~P9 빨리" · 외부 감사 `docs/ORCHESTRATION_AUDIT_1027.md § 9 체인` 미구현.
> **역할**: Goal → Discovery → Research → Plan → Execute → Verify → Repair → Learn 체인 선언형 정의.
> **실행 엔진**: `.claude/scripts/workflow-run.py` (R12 종단 테스트 + 향후 Supervisor 연결).

## 9 체인

| # | 파일 | 역할 | 트리거 |
|---|---|---|---|
| 1 | `01-goal.yaml` | 사용자 목표 수신 → Goal 등록 | UserPromptSubmit |
| 2 | `02-discovery.yaml` | 미등록 기술·도메인 탐색 | Goal 등록 후 |
| 3 | `03-research.yaml` | WebSearch·공식 docs | Discovery 결과 분류 |
| 4 | `04-plan.yaml` | Task 분해 + 라우팅 | Research 완료 |
| 5 | `05-execute.yaml` | Worker dispatch (Claude·Codex·general-purpose) | Plan 승인 |
| 6 | `06-verify.yaml` | test·build·smoke·Standing Requirements | Execute 완료 |
| 7 | `07-repair.yaml` | FAIL 시 격리 수정 + 재검증 | Verify FAIL |
| 8 | `08-learn.yaml` | solution 등재 + recurrence-tracker | 성공·실패 모두 |

**Anti-Ping-Pong**: `.claude/scripts/anti-ping-pong.py` (P1-C) — 같은 수정 3회+ 반복 감지 시 체인 중단 + rollback.

## 실행

```bash
# 단일 체인 실행
python .claude/scripts/workflow-run.py --chain 01-goal --input '{"goal":"X 를 해라"}'

# 전체 9 체인 (goal → learn)
python .claude/scripts/workflow-run.py --full --input '{"goal":"X"}'

# REPAIR 종단 테스트 (P1-B)
python .claude/scripts/workflow-test-repair.py
```

## 관련

- `docs/ORCHESTRATION_AUDIT_1027.md` (외부 감사 · 9 체인 L2 상태)
- `plugins/exec_orch/skills/auto-planner.md` (기존 5 단계 확장)
- `.claude/rules/execution-contract.md § 7` (상황 적응형 실행)
- `.claude/scripts/supervisor.py` (FSM 상태 전환)
- `plugins/exec_orch/skills/skill-recurrence-detector.md` (Learn 체인 소스)
