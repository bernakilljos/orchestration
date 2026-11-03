# 100점 최종 심사 준비 — T5 운영 안정성 · 실패 안전성 · 재현성 · 감사 패키지 (2026-11-03 · 계획)

기준: main `fc6d4e9` · 잠정 97점 · 이 문서 작성 중 유료 호출 0 · Goal·브랜치·sandbox 변경 0

## 0. 현재 증거 (재측정 2026-11-03 15:xx KST)
| 항목 | 값 |
|---|---|
| 예산 정산 | budget.today_spent $3.7106 = Agent metrics 11건 합 $3.7106 (NULL 비용 0) · 예약 settled 9건 $2.9648 (= 예약 기능 이전 R134 $0.7458 제외분과 일치) |
| Ledger↔Goal 무결성 | `ledger_goal_integrity.py` 이슈 0 · 요청 148 |
| self-heal 이벤트 | repaired 13 · failed 1 (#38 policy) · 진행 중 0 |
| 무결성 기준선 | `.claude/state/integrity-baseline/manifest-20261103-124910.jsonl` · 시험 6회 전후 기존 파일 변경 0 |
| 실패 경로 실측 | 실제: Judge 거부 2/2 (T2 · 드라이버 경로) · policy 실패 1 (#38) / Mock: 예산 소진·재시도 차단·잘못된 수정·Judge 거부 (test_t1_mock_chain 13) |

## 1. 미검증 항목 → 실제 검증 방법 (100점 조건)
| # | 미검증 | 실제 검증 방법 | 비용 | 합격 기준 |
|---|---|---|---|---|
| F1 | **고칠 수 없는 결함** (실제 스케줄러) | 허용 파일 밖(보호 테스트 쪽)에 원인이 있는 fixture 1건 등록 → 수정 Agent 1회 | ≈$0.39 (상한 $0.9) | policy 또는 pytest 실패 → 이벤트 failed · 원 Goal BLOCKED · **재시도 0 · Judge 0회** · 결과 브랜치 이동 0 |
| F2 | **예산 소진 중 이벤트** (실제 스케줄러) | 일일 한도 = 현재 지출 + $0.50 (< 수정 예약 $0.90) 로 두고 T1 fixture 1건 등록 → 2 tick 관찰 → 원복 | $0 | 호출 0 · sandbox 미생성 · 이벤트 pending(대기) · attempts 차감 0 · 한도 원복 후 다음 tick 정상 처리 (이때만 유료 ≈$0.72) |
| F3 | **Agent 호출 실패** (실제 CLI) | 수정 Agent 호출 상한 $0.01 로 실행 → CLI 가 예산 상한에서 중단 | ≤$0.01 | fail("agent_fix") · 예약이 settled/unknown 으로 정산 (0 처리 X) · Judge 0 · 반영 0 |
| F4 | **실제 체인에서 Judge 거부** | Agent 가 스스로 틀린 수정을 하게 만들 수 없어 실제 체인 강제는 불안정 → T2 실측(드라이버 · 같은 Judge 프롬프트) + Mock 체인 분기 + `judge_absorb` fail-closed 회귀 11종 으로 대체 · 심사 시 명시 | $0 | 잔여 위험으로 보고 |
| F5 | **재시작 복원** | 이벤트 처리 중 heal-tick 프로세스 종료 (Agent 실행 전 sandbox 단계) → 다음 tick 이 lease 만료 회수 | $0~$0.72 | 죽은 시도 repair Goal FAILED(interrupted) · 새 시도 1회 · 예약 open 잔존 0 (unknown 으로 정산) |
| F6 | **승인 대기 보존** | 24h 동안 BLOCKED(merge 승인 대기) Goal 18건 상태·결과 브랜치 ref 변화 감시 | $0 | 상태·ref 변화 0 · 자동 merge 0 |
| F7 | **T5 24h 운영** | 실제 Orca_10MinLoop 144 tick · F1/F2 를 시간 간격 두고 주입 · tick 마다 무료 일관성 점검 기록 | F1+F2 합 ≈$1.1 | 정시 ≥98%(전원 사유 분리) · 단계 실패 0 · 재시도 0 · 예산 정산 일치 · 무결성 변경 0 |
| F8 | **깨끗한 환경 재현** | `git clone` → 임시 폴더 · `ORCHESTRATION_ROOT`·`REPAIR_SANDBOX_ROOT` 임시 → `verify-fresh-clone.py` · `install.sh --dry`(또는 audit-install-dryrun.py) · pytest 92 · phase2/3/5 · golden 13 · t1 mock 13 | $0 | 운영 폴더·DB·스케줄러 무변경 · 전 테스트 PASS · 하드 경로 0 |

## 2. 운영 전 필수 조건 (F1~F7 공통)
- AC · commit 여유 ≥3GB·<90% — **주의: 재부팅하면 페이지 파일이 설정값 7168MB 로 돌아가 여유 ~2.7GB (기준 미달)**. 24h 시험 전에 설정 시작값을 10240MB 로 올릴지 결정 필요 (Windows 설정 변경 = 승인 사항)
- 정책 값은 시험 동안만 변경 · 전후 기록 · 종료 즉시 원복 (T1 과 같은 절차: `.claude/state/t1-fixtures/policy-change-*.json`)
- 일일 한도 = 실행 시점 UTC 누적 지출 + 시험 상한 (UTC 자정 = KST 09:00 재계산)

## 3. tick 마다 기록할 무료 일관성 점검 (F7)
1. budget.today_spent == 당일 Agent metrics 합 (NULL 비용 수 별도) · open 예약 0 (실행 중 제외)
2. 예약 settled 합 == 해당 체인 metrics 합 · unknown 은 예약액 그대로
3. Ledger↔Goal (`ledger_goal_integrity.py`) 이슈 0
4. 이벤트 상태 ↔ repair Goal 상태 ↔ 결과 브랜치 ref (repaired = VERIFIED + ref 존재 · failed = ref 이동 없음)
5. 무결성 기준선 비교 (6시간마다 · 전체 재해시 약 4분)
6. 10분 루프 로그 START/END 쌍 · 단계 실패 · COMMIT LOW 횟수

## 4. 최종 ZIP 감사 패키지
**포함**
- git 추적 소스 전체 (6,656 파일) — 단 `docs/screens/` (디자인 참조 이미지 4,979 파일 · 2.5GB) 는 제외 권장 (코드·정책 무관)
- 설정: `.claude/config/*.json` · `.claude/settings.json` · `.env.example` · `pytest.ini`
- 테스트: `.claude/scripts/tests/` · `golden-test.py` · `.claude/state/t1-fixtures/` (fixture·reference·hidden_check·mock 테스트·register) · `.claude/state/t2-judge-fixtures/`
- 증거: `.claude/state/*evidence*.json` 9 · `integrity-baseline/summary-*.json` · T1/T2 결과 JSON · `policy-change-*.json` · 이 문서 · `docs/ORCHESTRATION_AUDIT_2026-10-16.md`
- DB: `orca.db` 원본 X → 감사용 export (goals · tasks · goal_tasks · self_heal_events · executions · metrics · budget · agent_budget_reservations · approval_requests) — **conversations·session_summary·problem_solutions 는 대화 원문 포함이라 제외**
- 로그: `orca-10min-loop.log` (24h 구간) · `sync-drift.log`

**제외 (필수)**
- `.env` · `~/.claude/` (계정·OAuth·credentials) · `.claude/settings.local.json`
- `.repair-sandbox/` (8.3GB · 운영 worktree 복사본) · `.git/` (감사는 `git bundle` 로 별도 제공 가능)
- `conversations` 원문이 든 DB·로그 (`bash_commands.log` 등 명령 원문 로그)
- 만든 뒤 `secret_scan.py` + gitleaks 로 ZIP 내용 재검사 · 결과 첨부

## 5. 승인 필요 사항 (다음 단계)
| 항목 | 내용 |
|---|---|
| 유료 | F1 ≈$0.39 · F2 후속 ≈$0.72 · F3 ≤$0.01 · F5 0~$0.72 → 합계 ≤ 약 $1.9 (시험별 상한 $1.5) |
| 생성 | 테스트 Goal 3~4 · base·결과 브랜치 각 3~4 · sandbox 3~4 (약 36MB 씩) |
| 설정 | 페이지 파일 시작값 7168→10240MB (재부팅 후에도 commit 여유 확보) — 선택 |
| 실행 | F5 의 heal-tick 프로세스 1회 종료 (이 시험이 만든 프로세스만) |

## 6. 보존 (변경 금지 유지)
T1 결과 브랜치 6 (`repair/t1-*` · `repair-apply/T1-*`) · Evidence · 무결성 기준선 · Goal #77 FAILED · main 병합 0 · Statusline FROZEN · 승인 정책·계정·인증
