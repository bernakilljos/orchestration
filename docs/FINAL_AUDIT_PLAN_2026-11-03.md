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

## 7. F4 — T2 실제 Judge 거부 증거와 운영 체인의 차이
| 항목 | T2 (실측) | 운영 체인 (`agent_repair_chain`) |
|---|---|---|
| Judge 호출 | `dispatch_agent(role="judge")` · 읽기 전용 도구 · 같은 모델 | 같음 |
| Judge 프롬프트 | 운영 체인 문구 그대로 (드라이버가 원본 소스에 같은 문구가 있는지 실행 전 확인) | 원본 |
| 결합 규칙 | `judge_absorb` (fail-closed 수정 후) | 같음 |
| 통계 판정 (stat judge) | **생략** — Goal 을 만들지 않으려 보이는 테스트 통과 = VERIFIED 로 임시 handoff | `judge_handoff` 가 실행 기록·범위로 판정 |
| 수정안 출처 | 사람이 만든 잘못된 수정 (하드코딩·예외 숨김) | 수정 Agent 가 만든 수정 |
| 반영 차단 | 드라이버는 반영 단계 없음 · 결과 브랜치 ref 무변경 확인 | final ≠ VERIFIED 이면 commit·apply 전에 fail("judge_verdict") (Mock 체인 3건 + 코드) |
| 잔여 위험 | 실제 스케줄러 체인 안에서 Judge 가 수정 Agent 의 결과를 거부한 실측 0건 (F1 에서 Agent 가 우회 수정을 하지 않아 Judge 단계까지 가지 않음) |

## 8. 감사용 ZIP 구성안
| 구분 | 포함 | 방법 |
|---|---|---|
| 소스·설정·테스트 | git 추적 6,657 파일 중 `docs/screens/` 제외 | `git archive` (sparse) · `.env.example` 만 |
| Fixture·결과 | `.claude/state/t1-fixtures/` (fixture·reference·hidden_check·mock·register·policy-change 기록) · `.claude/state/t2-judge-fixtures/` | 복사 |
| 실제 실행 증거 | `.claude/state/*evidence*.json` 9 · T1/T2/F1/F5 증거 JSON · `orca-10min-loop.log` 해당 구간 | 복사 |
| DB 감사 export (익명화) | goals · tasks · goal_tasks · self_heal_events · executions(stdout/stderr tail 포함) · metrics · budget · agent_budget_reservations · approval_requests | CSV/JSON · `conversations`·`session_summary`·`problem_solutions`·`file_audit` 제외 · 사용자 이메일·계정명 치환 |
| 비용 정산 | 일일 지출 = metrics 합 · 예약 settled 합 대조표 | 생성 |
| 무결성 | `integrity-baseline/` manifest·summary · verify 결과 · F6 기준선 | 복사 |
| 재현 | F8 fresh clone 결과 · 이 문서 | 복사 |
| 시크릿 스캔 | `secret-scan.sh` 패턴 7종으로 포함 범위 재검사 결과 | 첨부 (2026-11-03: git 추적 0 · 증거·fixture 0) |
| **제외** | `.env` · `~/.claude/` · `.claude/settings.local.json` · `.repair-sandbox/` (8.3GB+) · `.git/` (원하면 `git bundle` 별도) · 대화·명령 원문 로그 (`bash_commands.log` 등) | — |

## 9. 실행 결과 (2026-11-03 15:19 ~ 16:11 KST)
| # | 판정 | 실제 증거 | 비용 |
|---|---|---|---|
| F1 고칠 수 없는 결함 | **PASS** | Goal 1286 · 이벤트 99 (scheduler 15:30) · 수정 Agent 6c068296 1회 · 변경 0 → policy `no_change` 로 중단 · Judge 0회 · 결과 브랜치 = base (이동 0) · 15:40·15:50 tick 재시도 0 · 원 Goal BLOCKED | $0.3829 |
| F2 예산 소진 | **PASS (Mock·기존 경로)** | 실제 `process_events` 를 임시 DB 로: 예산 없음 → 호출 0·sandbox 0·대기·시도 차감 0 → 한도 설정 후 같은 시도 번호로 진행 (test_phase18) | $0 |
| F3 Agent 호출 실패 | **PASS (Mock)** | 실행 실패 해제 · timeout·실행 중 예외·비정상 종료·응답 유실(exit 0 + JSON 없음) → 예약액 그대로 unknown 차감 (test_phase18) · 실제 API 과금 시험은 미실행 | $0 |
| F4 Judge 거부 | **PARTIAL** | §7 · 실제 스케줄러 체인 안 Judge 거부 실측 0 | $0 |
| F5 재시작 복원 | **PASS** | Goal 1288 · 이벤트 100 을 시험이 띄운 heal-tick 이 claim (15:32:28) → 그 프로세스 트리만 종료 (Agent 실행 전 · 예약 0) → lease 중 15:40~16:00 tick 미처리 → 16:10 scheduler 가 attempt 2 로 회수 · 수정 dd72b012 · Judge 44e3c273 VERIFIED · 숨은 검사 PASS · 중복 실행 0 · open 예약 0 | $0.7412 |
| F6 승인 대기 보존 | **PARTIAL** | 기준선 (Goal 18 · ref 104) 대비 1시간 변화 0 · 24h 비교는 미완 | $0 |
| F7 24h 운영 | **PARTIAL** | 관찰 시작 2026-11-03 16:11 KST · 24h 기록 미확보 | — |
| F8 Fresh clone | **PARTIAL** | 격리 clone (docs/screens 제외): verify-fresh-clone 위반 0 · install dry-run 3/3 OK · pytest 92 · phase2 20/20 · phase3 26/26 · golden 13/13 · **phase5 38/39** (R75 검사가 운영 Ledger 에 의존) · 하드 경로 0 | $0 |
- F1+F5 합계 $1.1241 (승인 $2) · 정책은 시험 동안만 변경 후 원복 (`policy-change-F1F5.json`) · UTC 누적 $4.8348
- 페이지 파일 설정 7168/10240 → 10240/10240 MB (재부팅 후 적용 · 재부팅 안 함)

## 10. 잔여 위험 · BLOCKED
1. F4: 운영 체인 안 Judge 거부 실측 없음
2. F5: heal-tick 이 sandbox 생성 중 종료되면 만들다 만 `heal-e100-a1` 폴더가 기록 없이 남음 (삭제 안 함 · 정리는 승인 사항)
3. F8: `test_phase5_self_healing.py` R75 검사가 운영 Ledger 데이터에 의존 (깨끗한 환경에서 1건 실패)
4. 테스트 실행 시 `ORCHESTRATION_ROOT` 를 강제로 주면 phase12 테스트 16건 ERROR (기본 실행은 정상)
5. 시험 도중 Claude Code 가 메모리 부족으로 대기 중이던 백그라운드 명령 1개를 중단 (commit 여유 4.1GB · 물리 RAM 압박)

## 11. 재현성 결함 수정 (2026-11-03 16:3x · 유료 $0)
| 결함 | 원인 (실측) | 수정 | 검증 |
|---|---|---|---|
| phase5 38/39 (R75) | 운영 Ledger 에 R75 가 있다고 가정 | 임시 Ledger 에서 실제 `cmd_invalid_registration` 으로 오등록 처리 후 `cmd_status` 확인 (운영 Ledger md5 무변경) | 새 clone 39/39 |
| phase12 16 ERROR | `ORCHESTRATION_ROOT` 가 아니라 **새 DB 에 goals 표가 없음** (phase2/3/5 가 먼저 돌아 표를 만든 뒤에는 통과해 순서 의존으로 보였음) | 테스트가 직접 SQL 전에 `supervisor.ensure_schema`·`runner._ensure_schema`·`_ensure_heal_schema` 호출 | 새 DB 16/16 |
| 새 설치에서 executions·goals·self_heal_events 표 부재 | 표는 각 모듈 첫 사용 때 생성 → 그 전에 `platform_api.evidence`·`ops_metrics`·`independent_verifier` 가 읽으면 실패 | `init-state-db.py`·SessionStart `ensure-state.sh` 가 같은 ensure 함수 호출 (IF NOT EXISTS · 데이터 무변경) | 새 clone · 기본 env / 명시 ROOT 둘 다: pytest 94 · phase2 20/20 · phase3 26/26 · phase5 39/39 · golden 13/13 |
- 남은 조건: DB 초기화(`init-state-db.py` 또는 SessionStart) 없이 바로 테스트하면 phase12 4건 실패 — 설치 절차의 초기화 단계가 전제

## 12. F5 잔여 sandbox `heal-e100-a1` (읽기 전용 조사 · 삭제 안 함)
- git worktree 로 등록 (브랜치 `repair/heal-e100-a1` = base `4c978e5`) · checkout 중 종료돼 파일 0개 (index 만 있어 전부 삭제로 보임)
- `repair-sandboxes.json`·예약 기록에 없음 · 관련 이벤트 100 은 attempt 2 (`heal-e100-a2`) 로 완료 · 보존할 변경 0
- 판정: **안전한 정리 후보** (`git worktree remove` + 브랜치 삭제) — 승인 사항
- 원인 결함: sandbox 생성 도중 중단되면 기록 전에 worktree 가 남는다 (재시작 복원 자체는 정상)

## 13. F4 실제 체인 Judge 거부 — 설계 (유료 실행 전)
- 기존 T2 재사용 가능 범위: Judge 판별 능력·프롬프트·결합 규칙 (같은 함수·같은 문구) → 재사용 가능. 운영 체인의 "수정 Agent 결과 → Judge 거부 → 반영 0" 은 별도 실측 필요
- 시나리오: 보이는 테스트 결함 A + docstring·REQUIREMENTS 에만 적힌 같은 함수의 요구 B (테스트 없음). 수정 프롬프트가 "smallest change" 라 Agent 가 A 만 고칠 가능성이 높음 → Judge 가 B 누락으로 거부하는지
- 한계: LLM 이 B 까지 고치면 VERIFIED 로 끝나 거부 경로를 못 탄다 (결과 강제 불가) → 1회 실패 시 재시도 없이 "거부 경로 미발생" 으로 기록
- 비용 상한: 수정 $0.9 + Judge $0.6 = $1.5 (1회) · 판정: Judge REPAIRING/UNVERIFIED + commit 0 + 결과 브랜치 = base + 재시도 0 이면 PASS
- Mock 사전 검증: test_t1_mock_chain `test_judge_reject_blocks_apply` 3건 (실제 체인 코드 · 가짜 Agent)

## 14. F4 실제 운영 체인 결과 (2026-11-03 17:00 KST · 1회 · 재시도 0) — **FAIL (Judge 거짓 VERIFIED)**
| 항목 | 값 |
|---|---|
| 실행 | Goal 1362 · 이벤트 107 (scheduler `heal:scheduler:20596`) · 수정 Agent `2b504d4c` · Judge `c1193537` · repair Goal 1363 VERIFIED |
| 테스트 | Runner exec 548 실패 2 → exec 549 통과 3 |
| 수정 diff | `>` → `>=` · `weight_kg` → `math.ceil(weight_kg)` (결함 A 만) |
| Judge | VERIFIED · confidence 9 · 근거는 docstring·테스트만 · `REQUIREMENTS.md` R3 (무게 ≤0 → ValueError) 미확인 |
| 숨은 검사 | **FAIL** — R3 weight=0 / -1.0 이 오류 없이 요금 계산 |
| 반영 | `repair-apply/T1-t1e_ship-1793692348@169dd75` (격리 브랜치 · main 무변경 · 보존) |
| 비용 | 수정 $0.3703 + Judge $0.3616 = **$0.7319** (상한 $1.50) · 정책 원복 |
- 원인: Judge 프롬프트가 "diff·테스트 결과·이 폴더의 파일" 만 근거로 지정하고 요구사항 문서 위치를 주지 않는다 → Judge 는 docstring 과 테스트로만 판정 (T2 에서 거부한 2건은 결함이 diff 자체에 보였던 경우)
- 영향: 테스트에 없는 요구사항을 Agent 가 빠뜨리면 Judge 도 놓칠 수 있다 (반영은 격리 브랜치 + merge 승인 대기라 main 피해 0)
- 수정 후보 (미적용 · 승인 사항): self_heal 설정에 요구사항 파일 경로를 받아 수정 Agent·Judge 프롬프트 모두에 "이 요구사항을 기준으로" 를 넣고, Judge JSON 에 요구사항별 충족 여부를 요구

## 15. 상태 기록
- F8 설치 전제: `python .claude/scripts/init-state-db.py` (또는 Claude Code 세션 시작 hook `ensure-state.sh`) 후 테스트 · 초기화 없이 바로 실행하면 phase12 4건 실패 (§11)
- 페이지 파일: 설정 10240/10240 MB (변경 전 7168/10240) · 재부팅 전까지 현재 할당 유지 · 자동 재부팅 안 함
- `heal-e100-a1`: 정리 후보 · 최종 감사 전까지 보존 (§12)
- F6·F7: 2026-11-04 16:11 KST 이후 기준선 (`integrity-baseline/f6-approval-wait-20261103-151915.json` · manifest) 과 비교 — 그 전에는 PARTIAL

## 16. 최종 ZIP 에 반드시 포함 (감사 지정 3 항목)
| 감사 항목 | 포함할 소스·문서 |
|---|---|
| 하드코딩 (경로·숫자·조건·문구) | `.claude/scripts/` 전체 · `.claude/hooks/` · `.claude/config/*.json` · `plugins/` · `setup/` · `.claude/state/hardcoded-audit.json` (자동 감사 결과) · `docs/HARDCODING_AUDIT_2026-10-28.md` |
| 기능 실제 연결·미구현 Scaffold | `.claude/settings.json` (hook 등록) · `orca-10min-loop.py` · `lib/` (supervisor·runner·self_healing·real_repair_chain·independent_verifier·agent_registry·tech_discovery·platform_api) · 실행 증거 (§8) · `docs/ORCHESTRATION_AUDIT_2026-10-16.md` |
| 서브 상태줄 라벨·세로줄 정렬 | `.claude/statusline.sh` · `.claude/scripts/statusline_*.py` (LABEL_WIDTH 등) · `.claude/rules/operational-freeze.md` (FROZEN 범위·서브 미검증 기록) · memory `feedback_statusline_*` 3건 사본 · 사용자 스크린샷 |

## 17. F4 결함 수정 (2026-11-03 · 유료 $0 · 실제 재실행 없음)
**수정 전**: 테스트 실패 출력 → 수정 Agent (요구사항 문서 언급 없음) → pytest → Judge (diff·테스트·폴더 파일만 근거) → `judge_absorb` (satisfies·confidence·권고만) → VERIFIED
**수정 후**: self_heal 설정 `requirements_path` (Goal 의 task spec 에서 동적 지정 · 고정 경로 없음) → `load_requirements` 가 **sandbox 안에서만** 읽어 스냅샷 (경로·sha256·ID) → Evidence `requirements` 기록 → 수정 Agent·Judge 프롬프트에 **같은 스냅샷** (데이터로 표시 · 도구·허용 경로 불변) → Judge 직전 sha256 재확인 (다르면 `requirements_changed` 중단) → Judge JSON `requirements[{id,status,evidence}]` → `judge_absorb(required_ids)` 가 결정적으로 검사: 필수 ID 누락·ID 불일치·`unverifiable`·근거 없음 → UNVERIFIED · `unmet` → REPAIRING
- 문서 지정됐는데 없음·sandbox 밖·ID 없음 → `requirements` 단계에서 유료 호출 전 중단
- `requirements_path` 미지정 작업 → 기존 판정 그대로 · Evidence 에 `not_configured` 로 명시 (미검증 구분)
- 검증 (무료): kit `test_phase18` 42 (요구사항 게이트 7 + 호환 1 + 로더 1) · Mock 체인 17 (F4 재현 4: F4 당시 응답 형태 차단 · R3 unmet 차단 · 정상 수정 VERIFIED + 같은 스냅샷 · 문서 없음 중단)
- 잔여: Judge 가 실제로 미충족인데 `met` 라고 근거를 꾸며 쓰면 결정적 검사로는 못 막는다 (근거 존재까지만 강제) · 실제 Agent/Judge 재실행 미실시
- **병합 승인 제외**: `repair-apply/T1-t1e_ship-1793692348@169dd75` (Goal 1362 · R3 누락 수정 · Judge 오승인) — 감사 증거로 보존 · merge 대상 아님
- 새 clone 재검증 (9e403e7): 기본 Root·명시 `ORCHESTRATION_ROOT` 모두 pytest 103 · phase3 26/26 · golden 13/13. 명시 Root 첫 실행에서 phase5 1건·phase2 2건 실패 → 같은 환경 3회 재실행 모두 39/39·20/20 → **간헐 실패 (원인 미규명 · 잔여 위험)**

## 18. F4 운영 경로 적용 확인 + 간헐 실패 원인 (2026-11-03 · 유료 $0)
**전달 경로 (실측 추적)**: task spec `self_heal.requirements_path` → `enqueue_failure_event` (self_heal 설정 전체를 event config 로 저장) → `process_events` (키 전달) → `run_repair(agent_fix)` (키 전달) → `agent_repair_chain(requirements_path)` → 스냅샷 → 수정 Agent·Judge 프롬프트 → `judge_handoff(requirements=…)` (handoff 파일에 저장) → `judge_absorb` (호출자 ID 없으면 handoff 의 ID 로 강제)
**발견한 우회 3건 → 차단**
| # | 우회 | 수정 |
|---|---|---|
| 1 | `requirements_path: ""`(빈 값) 이 거짓으로 평가돼 기존 판정으로 감 | 키가 있으면 빈 값·문자열 아님도 `requirements` 단계에서 유료 호출 전 중단 |
| 2 | 경로 미지정인데 수정 대상 옆에 요구사항 문서가 있음 (F4 Goal 1362 를 포함한 T1 6건이 실제로 이 상태였다) | 정책 `requirements_doc_names` (sandbox-policy.json) 로 수정 대상의 폴더·상위 폴더(sandbox 루트 제외) 탐색 → 있으면 `requirements_unbound` 로 유료 호출 전 중단 |
| 3 | CLI `judge-absorb` 는 required_ids 없이 결합 → 기존 판정 | handoff 에 스냅샷 저장 · `judge_absorb` 가 handoff ID 로 강제 |
- 문서 없는 일반 작업: 기존 판정 유지 · 최종 판정에 `requirements_scope: not_configured` 표시 (요구사항별 확인 시 `checked`)
- 승인·예산·인증 정책 변경 없음 (차단만 추가) · 운영 활성 이벤트 0건이라 현재 운영 동작 변화 없음
- 검증: `test_phase18` 50 · Mock 체인 22 (빈 경로·연결 누락·일반 작업 범위 표시·handoff 강제 추가 · mock 정책이 운영 정책 파일의 문서 이름을 그대로 사용)

**간헐 실패 원인 (재현 확인)**: 같은 clone 에서 DB 를 지우고 다시 돌리면 2번째부터 항상 phase5 1건·phase2 2건 FAIL (Root 설정 무관 · 기본 Root 도 2번째엔 실패). 
- 원인: safe_mode sandbox 이름 `g{goal_id}-safe` · apply 후 checkout 은 보존 정책상 남음 · 테스트 sandbox root (`%TEMP%/orca-repair-sandbox-test/<폴더명>`) 는 DB 와 함께 지워지지 않음 → DB 재생성으로 goal_id 가 1부터 다시 쓰이면 남은 sandbox 와 이름 충돌 → `create` 실패
- 이때 **결함**: supervisor 가 sandbox 없이 원본 작업 트리에서 명령을 실행했다 (fail-open). 운영 DB 는 AUTOINCREMENT 라 충돌은 없지만, 메모리·디스크 게이트로 create 가 실패해도 같은 경로로 원본에서 실행됐다
- 수정: ① supervisor — safe_mode 인데 sandbox 가 없으면 실행하지 않고 pending 유지 (`skipped_sandbox_unavailable` + 사유) ② phase2·phase5 테스트 정리 시 테스트 goal 의 sandbox 도 제거 (테스트 root 에서만)
- 검증: phase2 신규 Test 11 (sandbox 이름 선점 → 실행 0) · 수정 전 코드로 돌리면 FAIL (executed=1) 확인 · 이전 "3회 재실행 통과" 는 DB 를 유지해 goal_id 가 겹치지 않았기 때문

## 19. 최종 ZIP 감사 대상 추가 (§16 보강)
| 항목 | 포함 |
|---|---|
| F4 요구사항 전파·Judge 판정 코드 | `lib/self_healing.py` (enqueue·process_events·run_repair) · `lib/real_repair_chain.py` (load_requirements·find_unbound_requirements·agent_repair_chain) · `lib/independent_verifier.py` (judge_handoff·check_requirement_verdicts·judge_absorb) · `config/sandbox-policy.json` · `tests/test_phase18_agent_budget_gate.py` · `state/t1-fixtures/test_t1_mock_chain.py` |
| 간헐 테스트 실패 원인·잔여 위험 | 이 문서 §18 · `lib/supervisor.py` (safe_mode fail-closed) · `tests/test_phase2_e2e.py` (Test 11) · 재현 로그 |
- 새 clone 재검증 (d34495d): 같은 clone 에서 DB 삭제 → 전체 실행을 기본 Root·명시 Root 번갈아 2회씩 (예전엔 2회차부터 항상 FAIL) → 4회 모두 pytest 111 · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13 · 테스트 sandbox 잔여 0

## 20. F6·F7 최종 판정·ZIP 준비 (2026-11-03 18:1x KST · 판정 전)
- 도구: `.claude/state/final-audit/prepare_final_audit.py` (읽기 전용 · gitignore · ZIP 에 포함). `f6f7` 는 2026-11-04 16:11 KST 전에는 `NOT_YET` (rc 3) 만 반환 · `--interim` 은 "판정 아님" 표시
- F6 비교: 기준선 18 Goal 의 status·updated_at 각각 · 104 ref 의 이름·sha 각각
- F7 비교: 10분 슬롯별 START (누락 슬롯 목록) · START/END 짝 (창 시작 전 tick·창 끝 진행 중 tick 분리) · WARN/ERROR·COMMIT LOW · RAM/commit 최대·여유 최소 · 디스크 · budget 지출 = metrics 합 · 예약 정산 (예약 기능 도입 전 2회 $0.7458 별도 표시) · 열린 예약 0 · 무결성 verify · Ledger↔Goal · Goal #77 FAILED
- ZIP: F6·F7 final 판정 파일이 없거나 시크릿 패턴이 1건이라도 있으면 생성 거부. 포함 = git 추적 소스 (docs/screens 제외) · fixture·증거·무결성 기준선·hardcoded-audit·10분 루프 로그·DB 감사 export (대화·요약·해결책·file_audit 표 제외 · 홈 경로·이메일 치환) · statusline 결정 memory 사본. 제외 = `.env`·settings.local.json·`.repair-sandbox/`·`.git/`·orca.db/sessions.db 원본·bash_commands.log
- F4: 코드·Mock 회귀 PASS · 실제 Agent·Judge 재검증 **미실시** (별도 구분 기록)

## 20-1. 실행 연속성·Plugin 드리프트 (2026-11-04 09:0x KST · 읽기 전용 · 동기화·이동·삭제·prune 미실행)
**실행 연속성**
- 세션 예약 (CronCreate) 은 세션 종료 시 사라짐 → 정본 절차는 `.claude/state/final-audit/RUNBOOK-FINAL.md` (hook 이 쓰지 않는 위치). next-actions.md 에는 포인터만 둠
- 발견: next-actions.md 의 11-03 수동 절차 3줄이 사라짐 — `auto-save-next-actions.py:18-19,86` 가 응답에 "이어서 할 일"류 섹션이 있으면 파일 전체를 덮어씀 (stop-active-goals-resume.sh 는 `---` 뒤를 보존). 개발 금지라 코드는 그대로, 위치만 옮김
- 중복 방지: `f6f7` 는 final 파일이 이미 있으면 `ALREADY_FINAL` 로 새 판정을 쓰지 않음 (2회 연속 실행 시험 → 파일 1개) · ZIP 이름은 HEAD 기준 고정 (재실행 = 덮어쓰기) · 예약 프롬프트는 auto-goal 등록 조건 불일치 확인 (`should_register` → register False · 명시 토큰 없음)

**Plugin 드리프트 (SessionStart 경고: 변경 11 · 이름 충돌 23 · 드리프트 11 · Orphan 5)**
| 항목 | 실측 | 실제 영향 | 판정 |
|---|---|---|---|
| 드리프트 11 | 실제 파일 3개: `skills/auto-planner.md` · `skills/route_dispatch.md` · `agents/agent-02-implementer.md` (agent-02 는 9 플러그인 원본이 같은 대상 1개) | **방향이 경고와 반대**: git 상 원본 `plugins/` 이 나중 (10-16 외부 감사 수정) · `.claude/` 런타임 사본이 이전 (10-13 · 04-12). 경고는 파일 mtime 기준이라 "`.claude/` 직접 수정 의심" 표시가 틀림 | 잔여 위험 (중) — Claude 가 실제 읽는 `.claude/` 사본에 범위 lock·중간보고 금지·A/B 폐지·Codex 자동 dispatch 수정이 빠짐. Python 실행 경로에서 이 3 파일을 읽는 코드 0 (지시 계층 영향만) |
| 이름 충돌 23 | `sync-plugins.py` RENAME_MAP 23건 = 의도된 접두사 (`mcp_dev/install.md → mcp_dev-install.md` 등) · 23/23 대상 존재 · 내용 동일 | 없음 | 정상 (경고 문구가 오해 소지) |
| 같은 대상에 원본 여러 개 | agent-01(3)·02(9)·03(3)·04(5)·05(3)·06(4) · 각각 원본 내용 1종 | 현재 없음 (마지막 원본이 이겨도 같은 내용) · 원본 하나만 바뀌면 순서에 따라 덮어씀 | 잔여 위험 (낮음) |
| Orphan 5 | `skills/ai-finetune-pipeline.md` · `skills/vscode-java-lsp-fix.md` · `agents/brainstorming-partner.md` · `agents/coach.md` · `agents/pm.md` (plugins 원본 없음 · git 추적) | brainstorming-partner·coach 는 plugin 명령이 호출 (`design_ppt/ai-system-stages.md` · `exec_claude/generate-ideas.md`) · 3 agent 는 현재 세션에서 사용 가능 상태 → **prune 하면 기능 손상** | 잔여 위험 (낮음) · prune 금지 근거 |
- 근거 자료 (ZIP 포함): `.claude/state/final-audit/out/drift/` sync-check·drift-detail·drift-diffs·rename-orphan
- 정리 방법 (미실행 · 결정 필요): 드리프트 3 파일은 원본→런타임 sync 1회면 해소되나 지시 계층 변경 = FREEZE 범위라 별도 승인 필요

## 21. F6·F7 최종 판정 + 감사 ZIP (2026-11-04 16:17 KST · 24h 창 11-03 16:11 → 11-04 16:11 · 유료 $0)
판정 파일: `.claude/state/final-audit/out/f6f7-final-20261104-1617.json` (1회 · 중복 방지 가드 적용)

| 항목 | 기준선 | 24h 실측 | 판정 |
|---|---|---|---|
| **F6 기존 Goal 보존** | 18 goals · 104 refs (11-03 16:11) | 18/18 상태·updated_at 동일 · 104/104 ref sha 동일 | **PASS** |
| F7 10분 tick 누락 없음 | 144 슬롯 | START 144 · 누락 슬롯 0 · 스케줄러 LastTaskResult 0 · MissedRuns 0 | PASS |
| F7 START/END 짝 | — | END 145 (창 시작 전 tick 1개 END 포함 → 제외 후 144=144) · 창 끝 진행 중 0 | PASS |
| F7 WARN/ERROR | interim 0 | 0 (COMMIT LOW 0) | PASS |
| F7 메모리·디스크 (관측) | interim RAM 79.7% · commit 84.3% | RAM 최대 79.7% · commit 최대 84.4% · commit 여유 최소 3.86GB · 디스크 21.2GB | 관측값 (게이트 아님) |
| F7 예산 정산 | interim $5.5667 = metrics 합 | 창 안 11-04 지출 $0 · 열린 예약 0 · 지출=metrics | PASS |
| F7 무결성 (sandbox·기록) | — | changed·missing·record 0 | PASS |
| F7 Goal #77 | FAILED | FAILED 유지 | PASS |
| **F7 Ledger↔Goal 일치** | interim PASS | **R154 ledger=completed · Goal #1464=RUNNING** | **FAIL** |
| **F7 종합** | | 8 검사 중 7 PASS · 1 FAIL | **FAIL** |
| F4 실제 Agent·Judge 체인 | — | 코드·Mock 회귀 PASS · 실제 재검증 **미실시** | 미검증 (PASS 아님) |

**F7 FAIL 원인 (실측 · 수정 안 함)**
- 11-04 09:47 사용자 지시 "분석 폴더로 복사" 가 Ledger R154 (pending) 로 기록 → 09:50 `orca-10min-loop.py:381` 의 `request-ledger.py to-goals` (`request-ledger.py:381-415`) 가 pending 항목을 Goal #1464 로 만들고 supervisor 가 PENDING→PLANNING→RUNNING 진행
- 09:51 작업 완료 후 Ledger 는 `complete R154` 로 닫혔지만 Goal 쪽을 닫는 경로가 없음 → `ledger_goal_integrity.py` 가 `ledger_completed_but_goal_incomplete` 1건 (fail-closed)
- 결함 성격: 감사 대상 기능의 실제 결함 (대화 지시가 Goal 로 자동 승격되고, Ledger 완료가 Goal 에 반영되지 않음). 판정 기간 중 "새 Goal 생성 금지" 조건과도 충돌. 이전 연속성 점검(§20-1)은 auto-goal hook 만 확인하고 10분 루프의 to-goals 경로는 확인하지 않았음
- 조치: Goal·Ledger·DB 보존 원칙과 개발 금지에 따라 **Goal #1464 는 그대로 둠** (상태 변경·삭제 없음). 결정 필요: Goal #1464 처리 방법과 to-goals 의 Ledger 완료 반영 (또는 대화형 지시 제외) 수정 여부

**감사 ZIP**
- 파일: `.claude/state/final-audit/out/orchestration_v1-final-audit-abde1da.zip` · 24,444,218 bytes (23.3MB) · 압축 전 39,761,866 bytes · 1,778 항목
- sha256 `44718636fbeb269a00053d21fe42b26d52e0bfa4b76494b3d7246f05ad0772db` (같은 HEAD ZIP 사전 없음 → 신규 1회 생성 · 덮어쓰기 없음)
- 포함 목록: `out/zip-manifest.txt`
- 시크릿 검사: 생성 도구 스캔 0건 · 별도 재검사 (Anthropic·OpenAI·GitHub·AWS·Google·Slack 키·개인키 패턴) 0건 · 제외 대상 (`.env`·settings.local.json·orca.db·sessions.db·bash_commands.log·`.repair-sandbox/`·`.git/`·docs/screens·exe) 0건 · DB export·로그의 계정명 치환 잔여 0건
- 관찰: git 추적 문서 8개 (guide.txt·SECURITY.md·docs/CLAUDE_ACCOUNT_SEPARATION.md 등) 에 계정 이메일 원문 포함 — 비밀번호·토큰은 아니지만 "계정 정보 제외" 기준으로는 미충족 · ZIP 재생성 안 함 (결정 필요)

**잔여 위험**
1. F7 Ledger↔Goal 불일치 (위) — 10분 루프가 대화 지시를 Goal 로 승격
2. F4 실제 Agent·Judge 재검증 미실시
3. Plugin 드리프트 3 파일 (§20-1) — 런타임 `.claude/` 사본이 원본보다 이전 · sync 보류
4. ZIP 안 git 추적 문서의 계정 이메일 8개 파일
5. `heal-e100-a1` 정리 후보 (삭제 안 함)

## 22. F7 FAIL 후속 — R154·Goal #1464 조사 · to-goals 수정 · 익명화 ZIP (2026-11-04 16:2x~16:4x KST · 유료 $0)
**R154 · Goal #1464 (읽기 전용 · 상태 변경 없음)**
| 항목 | 실측 |
|---|---|
| 승격 경로 | 09:47 R154 pending (분류 `redo`) → 09:50 10분 루프 `to-goals` (`request-ledger.py:381`) 가 **정책 확인 없이** pending 전부를 Goal 로 생성 → advance-all PENDING→PLANNING(09:50:17)→RUNNING(09:50:58) |
| 실행 중 작업 | 없음 — goal_tasks 0 · plan/result NULL · executor claim 없음 · sandbox 없음 · 연결 Goal 없음. 매 tick `execute_goal` 이 0 task 실행 (`executed_goals: executed 0`) |
| RUNNING 잔류 이유 | task 0 이라 VERIFIED/REPAIRING 조건 (`total_tasks>0`) 에 안 걸림 → 빈 RUNNING |
| 작업 완료 증거 | 실제 작업 (분석 폴더 복사) 은 대화 세션이 수행 · 증거는 Ledger evidence (1777/1777 sha256 동일) — Goal 쪽 증거 0 |
| 예정 변화 (기존 규칙) | timeout_h=24 → **2026-11-05 09:50 KST 이후 첫 tick 에서 supervisor 가 FAILED(timeout) 로 전환** (기존 상태머신 · 이번 작업으로 막거나 앞당기지 않음) |
| 조사 중 사고 | 읽기 전용 의도로 `supervisor.py advance-all --dry-run` 실행 → CLI 는 `--dry` 만 인식해 **실제 1회 실행** · 상태 전이 0건 (goal_transitions 최대 id 2129 그대로) · 10분 tick 과 동일 동작 |

**to-goals 수정 (a3d88b7)**
- 승격 기준 = `auto_goal_from_prompt.should_register` (UserPromptSubmit 자동 등재와 같은 정본 · 명시 실행 토큰 필요 · 질문/보고 skip · `no-auto-goal`/`AUTO_GOAL_REGISTER=0` opt-out · 1h 중복). 미승격 항목은 원장에 그대로 둠
- Request 완료 ≠ Goal 완료: `ledger_goal_integrity.check()` 불일치는 출력에 WARN 만 · Goal 상태 변경 X → 10분 루프는 WARN 레벨로 기록. 실측 16:30 tick: `[WARN] ledger to-goals: ... WARN ledger R154 completed but goal #1464 RUNNING (상태 변경 안 함)`
- 실행 단계 승인 정책 (approval gate · 허용 명령 · safe_mode) 은 변경 없음

**회귀 (무료)**: test_phase19 6/6 (대화·질문 미승격 · 명시 요청 1회 승격 · 중복 Request/반복 실행 Goal 1개 · 완료 Request + RUNNING Goal 경고만·상태 유지 · opt-out · 10분 루프 같은 경로·WARN) — 수정 전 코드로 되돌려 5/6 FAIL 확인 후 복원 · pytest 117 passed (기존 스크립트형 테스트 33건 fixture 오류는 변경 전과 동일 · 스크립트 실행 시 PASS) · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13

**익명화 ZIP**
| | 기존 | 신규 |
|---|---|---|
| 파일 | `orchestration_v1-final-audit-abde1da.zip` (보존 · 덮어쓰기 X) | `orchestration_v1-final-audit-a3d88b7.zip` |
| 크기 | 24,444,218 B · 1,778 항목 | 24,458,422 B · 1,780 항목 |
| sha256 | `44718636…0772db` | `e7a5f7ff…ef81a4798` (`e7a5f7fff14c0b6409ae3067db21587acadc377dd13a7c21975dc95ef81a4798`) |
| manifest | `out/zip-manifest-abde1da.txt` | `out/zip-manifest-a3d88b7.txt` (+ test_phase19 · audit/SOURCE-SNAPSHOT.json) |
- abde1da 의미 조사: 기존 ZIP 의 git 추적 1,662 항목 중 992 는 abde1da blob 과 동일 · 668 은 줄바꿈 (CRLF, core.autocrlf) 차이만 · 내용 차이 2 (`CLAUDE.md` 날짜 줄 · `common.log`) = 당시 미커밋 작업 트리. 665257c 는 ZIP 생성 **후** 판정 기록 (§21·guide·CLAUDE.md) 커밋이라 기존 ZIP 에 없음
- 신규 ZIP 은 `audit/SOURCE-SNAPSHOT.json` 에 source_commit 전체 해시 · 작업 트리에서 들어간 미커밋 파일 (common.log + sha256) · 줄바꿈 주의 · 익명화 파일별 이전/이후 sha256 기록. 같은 HEAD ZIP 있으면 생성 거부
- 익명화: 원본 Git 파일은 그대로 · ZIP 사본만 75 파일 치환 (Claude 로그인 계정 메일 · git 작성자 메일·이름 · 로컬 사용자명 · 호스트명 → `<ACCOUNT_EMAIL>`·`<ACCOUNT_NAME>`·`<USER>`·`<HOST>` · 홈 경로 `<HOME>`). 값은 코드에 박지 않고 실행 머신에서 동적 수집
- 검사: 생성 도구 시크릿 0 · 계정 식별자 잔여 0 · 별도 재검사 시크릿 0 · 식별자 0 · 제외 대상 0
- 이 §22 커밋은 ZIP 생성 **후** 기록이라 ZIP 에 없음 (ZIP 소스 = a3d88b7)

**잔여 위험**
1. Goal #1464: 11-05 09:50 KST 이후 기존 timeout 규칙으로 FAILED 전환 예정 — 결정 필요 (그대로 둘지)
2. 이미 생성된 ledger 출처 Goal 31건은 전부 FAILED (과거 동일 경로) — 수정 없음
3. 익명화 사본의 계정 이름 치환으로 `dashboard.py`·`install.bat` 등 GitHub 저장소 경로가 `<ACCOUNT_NAME>` 로 바뀜 — ZIP 에서 그 기능을 그대로 재실행하면 원격 저장소를 못 찾음 (감사 열람용)
4. `team@itcen.com` (조직 대표 메일) 1건은 개인 계정 아님으로 유지
5. 기존: F4 실제 재검증 미실시 · Plugin 드리프트 3 파일 · heal-e100-a1 정리 후보

## 23. V1.0 안정화 + V1.1 점검 (2026-11-04 17:xx KST · a3d88b7 독립 감사 반영 · 유료 $0 · 커밋 bb70da7)
**V1.0 결함 (감사 6건 · 코드로 원인 확인 후 수정)**
| # | 항목 | 실제 원인 | 수정 | 수정 전 재현 | 결과 |
|---|---|---|---|---|---|
| 1 | 미완료 Task 자동 삭제 | `cleanup-pollution.sh` §8 이 pending·in_progress·locks 를 mtime +3 만으로 `rm` · 같은 유형 `cleanup-orphans.sh` 는 30분+ lock 을 pid 확인 없이 삭제 · 요약 표는 서브셸 때문에 앞 폴더 행이 덮어써짐 | 미완료 작업 보존 (요약에 후보만) · lock 은 기록된 pid 종료 확인 시만 · process substitution | HEAD 코드로 test_phase20 FAIL | **PASS** |
| 2 | `--dry-run` 오실행 | `supervisor.py` advance-all 이 `--dry` 만 인식 · 모르는 옵션 무시하고 실제 실행 (§22 조사 중 사고) | `--dry-run` = `--dry` · 모르는 옵션 실행 전 rc 2 거부 · 호출처 (10분 루프·stop hook) 옵션 영향 없음 | FAIL | **PASS** |
| 3 | 고아 프로세스 종료 | `python -c`·`/.claude/`(다른 폴더 포함)·CPU 5%+ grep 등 소유 확인 없이 kill (실제 종료 이력 0) | 이 프로젝트 `.claude` 경로·셸 스냅샷 흔적 + 누적 CPU<1초 (멈춤) 만 · 일하는 프로세스는 WARN 만 | HEAD 에선 5개 중 3개 종료 | **PASS** (작업별 PID 등록은 V1.1 D) |
| 4 | 조회 → verified 승급 | `promote-solutions.py` 가 로그 전체를 매 실행 누적 + hit≥3 이면 verified=1 · hit<3 이면 수동 검증 행도 0 으로 덮음 | 로그 cursor 멱등 집계 (첫 실행은 위치만) · verified 는 건드리지 않음 | FAIL | **PASS** · 기존 verified=1 33행 (전부 hit≥3) 은 강등 안 함 — 감사 후 판단 필요 |
| 5 | 요구사항 6,000자 절단 | `load_requirements` 가 ID 는 전체에서, 본문은 `[:6000]` | 정책 `requirements_max_chars` (sandbox-policy.json) 초과 시 실패 → 유료 Agent 전 중단 · 이하면 전문 | FAIL | **PASS** (기존 F4 요구사항 게이트 테스트 phase18 포함 통과) |
| 6 | 요구사항 경로 하드코딩 | lib 에 고정 파일명·fixture 명 0 — `requirements_path` + 정책 `requirements_doc_names` 로만 연결 | 변경 없음 | — | **PASS** |

**V1.1 요청 (실제 코드 연결 기준)**
| 항목 | 현재 상태 (근거) | 판정 |
|---|---|---|
| A 긴급 요청 신속 처리 | hook·lib·route 에 긴급/urgent 처리 0곳 · 미구현 | **FAIL** (미착수) |
| B [확인]/[예시]/[추정]/[미확인]/[판독불가] | 감정 감지 hook 2곳에만 문자열 · Agent·Runner·Judge 공통 강제 없음 | **FAIL** (미착수) |
| C 연관 작업 자율 수행 | 이번 작업에서 같은 유형 (lock·하드코딩 7곳·요약 덮어쓰기) 함께 처리 · 하지만 `execution-contract.md §3` 범위 lock 규칙과 충돌 · 정책 문서화 없음 | **PARTIAL** |
| D 프로세스·메모리 자동 관리 | 고아 정리 소유권 제한 (V1.0-3) · 작업별 PID 등록·runner 자식 트리 정리 없음 (`runner.py` kill/psutil 0) | **PARTIAL** |
| E 파일 정리·manifest | 미완료 보존·죽은 pid lock 만 삭제 · manifest/index 통합 없음 | **PARTIAL** |
| F Statusline | 요청 '다음:' 문구 개행·태그·ANSI 제거 + 40칸 (실측 요청 줄 166→152칸) · `_pair` 전체 폭 상한·서브 세로줄은 배치 변경이라 미수정 · VS Code 캡처 비교 미실시 | **PARTIAL** |
| G 하드코딩·연결·드리프트 | `~/.claude/projects/<slug>` 7곳 동적화 · Plugin 드리프트 3 파일 원본 반영 (`--check` drift 0 · orphan 5·rename 23 그대로) · 모델·Agent 수·스케줄 전수 점검 미실시 | **PARTIAL** |

**회귀**: test_phase20 7/7 (V1.0 6 + 요청 줄 1) · HEAD 코드로 6/6 FAIL 확인 · pytest 124 passed (스크립트형 33 fixture 오류 기존 동일) · phase5 39/39 · phase2 21/21 (1회 19/21 → 같은 순서 재실행·3회 반복 모두 21/21 · 재현 안 됨) · phase3 26/26 · golden 13/13 · test-10min-loop rc 0
**Fresh clone (bb70da7 · docs/screens 제외 · ORCHESTRATION_ROOT·REPAIR_SANDBOX_ROOT 임시)**: verify-fresh-clone 위반 0 (466 파일) · pytest 124 · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13 · 하드 경로 0 · 임시 clone 삭제

**관찰 · 잔여 위험**
1. 17:00 tick 누락 (`NumberOfMissedRuns 1`) — 노트북 배터리 운전 (BatteryStatus 1) + 작업 설정 `DisallowStartIfOnBatteries` · 전원 연결 시 복구 · 설정 변경 안 함 (F7 창 이후)
2. `test-10min-loop.sh` (DRY-RUN) 가 운영 로그 `orca-10min-loop.log` 에 기록 (17:04 COMMIT LOW 포함) — 시험이 운영 로그를 오염 · 미수정
3. 17:04 commit 90.7% (여유 2.3GB) — 테스트 동시 실행 영향 추정 [추정]
4. Goal #1464 — 11-05 09:50 KST 이후 timeout FAILED 예정 (기존 규칙)
5. V1.1 A·B 미착수 · C·D·E·F·G 부분 · F4 실제 재검증 미실시

## 24. e462f9b 재감사 반영 (2026-11-04 18:xx KST · 유료 $0)
| 항목 | 재감사 지적 | 실제 확인 | 수정 | 결과 |
|---|---|---|---|---|
| P1 학습 조회 중복 집계 | 짧은 로그에 줄 추가 시 1·3·6 | **재현 1·3·6** (로그 앞 256B 해시가 짧은 로그에 줄이 붙을 때마다 바뀜) · cursor 파일이 DB 반영과 별도 | 진행 위치를 orca.db `promote_cursor` 표에 **점수 갱신과 같은 트랜잭션**으로 저장 · 앞부분 비교는 기록한 길이만큼 · 완성된 줄까지만 · 교체된 로그는 처음부터 | 1·2·3 · 쓰는 중인 줄 다음 실행 · 중간 실패 후 재실행 중복 0 · **PASS** |
| P1 프로세스 소유권 | `-c`·`--version`·셸 스냅샷·`export TEMP=` 는 어느 프로젝트에도 있음 | 맞음 | 종료 근거 = 명령줄에 이 프로젝트 `.claude` 경로 + 멈춤 만 · 일반 흔적만 있는 것은 "소유 미확인 · 종료 안 함" 로그 | **PARTIAL** — 작업별 PID 등록·Job Object 없음 (경로 흔적 = 소유 추정) |
| P1 Statusline 행 전체 폭 | 요청 문구 40칸만으로는 부족 | 맞음 (실측 152칸) | 마지막 출력 1곳에서 터미널 폭 초과 행만 `…` 로 자름 (ANSI 유지 · 배치·색·라벨 폭 그대로) · 폭 = `STATUSLINE_COLUMNS`/`COLUMNS` → Windows `CONOUT$` · 모르면 자르지 않음 | 실측: 폭 100 → 최대 99칸 · 14줄 유지 · **PARTIAL** — VS Code 실제 화면 캡처 미실시 [미확인] · 서브 세로줄 정렬 미수정 (FROZEN · 화면 검증 없이 변경 X) |
| P2 `advance-all` 인자 경계 | `--trigger` 값 누락·위치 인자 통과 | 맞음 | `--trigger` 값 필수 · 위치 인자 거부 (rc 2 · 실행 X) · 루프의 `--trigger scheduler` 정상 | **PASS** |
| P2 긴 요구사항 차단 | 정상 긴 문서도 처리 불가 | 정책 동작 | 변경 없음 (`requirements_max_chars` 프로젝트별 조정) | 유지 |
| P2 다른 삭제 경로 | `*.bak/*.orig/*.tmp` 3일·nested `.claude/.claude` | 확인 | 미수정 (임시·백업·오염 폴더 정책 · cleanup-policy.md) | 잔여 |
| P2 V1.1 종단 연결 | 긴급·사실 태그·후처리 | A·B 미착수 그대로 | — | FAIL 유지 |

**회귀**: test_phase20 10/10 · 직전 커밋 코드로 6/10 FAIL 확인 · pytest 127 passed (스크립트형 33 기존) · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13 · fresh clone 은 bb70da7 기준 (이번 변경 후 재실행 안 함)

**보안 관찰 (조치 필요)**: 이 PC 프로세스 목록에서 상태 저장소 push (`orchestration-status`) 의 원격 URL 에 GitHub 토큰 원문이 들어 있음 (명령줄 노출) · 토큰 값은 기록하지 않음 · 토큰 교체 + URL 대신 자격 증명 도우미 사용 필요 (계정·인증 정책 — 미변경)
