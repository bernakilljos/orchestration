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

## 25. bde283b 재감사 P0·P1 (2026-11-04 18:xx KST · 유료 $0)
| 항목 | 실제 확인 | 수정 | 결과 |
|---|---|---|---|
| P0 토큰이 git URL 에 | `status-push.ps1:19`·`:416` + `status-push.bat:157` · **추가 발견** `status-push.bat:33` 이 생성 ps1 에 토큰 원문을 씀 (현재 디스크엔 그런 파일 없음) · 실행 중 사본 `~/.claude/status-push.ps1` (Run 키 · 57h) 은 시작 시 `orchestration-status` 원격에서 자기 자신을 내려받아 덮어씀 | kit 소스: URL 에서 토큰 제거 · 토큰은 환경변수 `ORCH_GH_PAT` + git credential helper (명령줄엔 변수 이름만) · 토큰 없으면 기존 자격 관리자 · bat 생성 스크립트는 실행 시 환경변수에서 읽음 | 소스 PASS (URL 토큰 0 · helper 가 가짜 토큰을 명령줄 노출 없이 전달 실측) · 실제 push 미시험 [미확인] · **실행 중 사본·원격 저장소 미반영** (E·G 승인 대기) |
| P1 확장자 일괄 삭제 | `cleanup-orphans.sh` §4 (SessionEnd 마다) 저장소 전체 `*.bak/*.bak.*/*.orig` 삭제 · `daily-cleanup.bat` 프로젝트 전체 `*.bak/*.tmp/*.orig` 무조건 삭제 · `cleanup-pollution.sh` §3 3일+ 가 sandbox 증거·미완료 task 도 대상 | §4 = 후보 수만 기록 · daily-cleanup = "Candidate - not deleted" 기록만 · cleanup-pollution §3 = `.repair-sandbox`·`.claude/tasks`·`integrity-baseline` 제외 | PASS · 실제 SessionEnd hook 실행 rc 0 · 삭제 0 (저장소 백업 파일은 실행 전 이미 0개 — 과거 §4 삭제 결과로 보임 [추정]) |
| P1 heartbeat 만으로 종료 | `cleanup-orphans.sh` §2 heartbeat 5분+ 면 `*-auto.bat` cmd 창 전부 Stop-Process | 종료 X · 후보 pid 만 기록 | PASS (작업별 PID 등록은 없음 — 정리는 사람 확인 후) |
| 추가 발견 | 작업 폴더의 `.bat` 65개 전부 LF (`.gitattributes` 는 `eol=crlf`) · `daily-cleanup.bat` 는 LF+한글 주석으로 cmd 가 16곳 잘못 파싱 (한 번도 정상 실행 안 됐을 가능성) · 스케줄 미등록 | 수정한 bat 2개만 CRLF | 나머지 63개는 미변경 (orca-10min-loop.bat 등은 정상 동작 중) |
| 추가 발견 | 원격 `cmd.json` 으로 클릭·`codex/gemini/claude` 강제 종료 실행 (`status-push.ps1`·`remote-agent.ps1`) — 원격 저장소 쓰기 권한 = 이 PC 원격 조작 | 미변경 | H 결정 대기 |

**승인 구분**: A·B·C·D 진행 완료 · **E** 원격 `orchestration-status` 에 수정본 반영 (외부 push) · **G** 실행 중 status-push 재시작 · **H** 원격 명령(cmd.json) 기능 유지 여부 — 승인 대기 · **F 토큰 폐기·재발급 = 무시 (사용자가 나중에 직접 처리)**

**회귀**: test_phase20 13/13 (이번 3 추가 · HEAD 코드로 3 FAIL 확인) · pytest 130 passed (스크립트형 33 기존) · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13 · fresh clone 미재실행 (bb70da7 기준)
**시험 중 사고**: `daily-cleanup.bat` 를 `cmd //c` 로 시험할 때 실제 실행되지 않음 → PowerShell + 임시 `CLAUDE_PROJECT_DIR` 로 재시험 · 운영 폴더 변경 없음 확인

## 26. E·G·H 점검 (2026-11-04 · 읽기 전용 · push·재시작·코드 변경 없음 · F 는 사용자 제외)
- **E**: 원격 `orchestration-status` (비공개 · 미인증 API 404) 에는 `status-push.ps1` 이 **없음** (`remote/`·`status/` 만 · 최근 커밋 = 상태 push) → 자기 업데이트는 내려받을 파일이 없어 아무것도 덮어쓰지 않음. 원격에 수정본을 올리면 오히려 "원격 저장소 → 이 PC 코드 실행" 경로가 새로 생김 → **원격 push 불필요 · 권장 안 함**. 실제 반영 = kit 수정본을 설치 사본 `~/.claude/status-push.ps1` 로 복사 (install.bat 과 같은 방식) — 현재 설치 사본 md5 9775f030 (구버전) · kit e0ba3c8 = 372eaa81
- **G**: 실행 중 PID 23328 `powershell.exe -WindowStyle Hidden -File ~/.claude/status-push.ps1` · 시작 2026-11-02 09:11:28 · 부모 12236 (Run 키 `OrchestrationStatusPush` → wscript) · 같은 시각 PID 18700 `remote-agent.ps1` (Run 키 `OrchestrationRemoteAgent`) · 재시작 = 설치 사본 교체 후 PID 23328 만 종료 → `wscript ~/.claude/status-push-silent.vbs` 재실행 (승인 대기)
- **H** (원격 명령 · 인증 없음): 명령 출처 = 대시보드 HTTP (`/control-recv`·`/pull-cmd/<pc>` · 헤더 인증 X · 대시보드 주소는 원격 저장소 `dashboard-url.json`/로컬 캐시) + 원격 `cmd.json` · 서명·만료·재사용 방지 없음
  | 명령 | 위치 | 영향 |
  |---|---|---|
  | `stop` | status-push `Check-Control`·`cmd.json` | `codex`·`gemini`·`claude` 이름의 **모든** 프로세스 강제 종료 (소유권 X · 다른 세션·작업 포함) |
  | `key` | status-push·remote-agent | `SendKeys` 임의 키 입력 = 사실상 원격 명령 실행 |
  | `click`·`dblclick`·`drag` | status-push·remote-agent | 원격 마우스 조작 |
  | `pause`·`resume` | status-push | 예약 작업 `OrchestrationStatusPush` 켜기/끄기 — 그런 작업 없음 (Run 키로 실행) → 효과 없음 |
  | `stop` | remote-agent | 에이전트 자신만 종료 (안전) |
- 최소 변경안 (미적용): ① `stop` 을 이름 전체 종료 → kit 가 띄운 워커 (명령줄에 프로젝트 경로·auto.bat) 만 · 소유 미확인은 로그 ② `key`·`drag` 는 기본 꺼 두고 설정으로만 허용 ③ 명령에 공유 비밀 기반 서명 + 만료 시각 (대시보드·cmd.json 공통) ④ `pause/resume` 은 실제 실행 방식(Run 키) 기준으로 정정 · 영향 = status-push.ps1·remote-agent.ps1 + 대시보드 쪽 서명 (대시보드 코드는 이 저장소 밖일 수 있음 [미확인])

## 27. E 취소 · G 적용 · H 원격 명령 기본 차단 (2026-11-04 18:5x KST · F 사용자 제외)
- **E**: 원격 `orchestration-status` 에 스크립트 push 안 함 (원격 → 이 PC 코드 실행 경로를 만들지 않음)
- **G 적용됨**: 설치본 백업 `~/.claude/status-push.ps1.bak-20261104` (9775f030) → kit 수정본 복사 (607aac8d) · PID 23328 시작 시각 2026-11-02 09:11:28·경로 재확인 후 그 프로세스만 종료 → Run 키 명령 (`wscript status-push-silent.vbs`) 으로 재시작 → 새 PID 6072 · remote-agent PID 18700 및 다른 프로세스 미접촉 · 150초 관찰: 원격 HEAD 3bf4b74a → 21050b82 (상태 전송 정상) · git 프로세스 41회 표본 중 명령줄 토큰 0 · helper 변수 이름만 18
- **H (kit · status-push.ps1·remote-agent.ps1)**: `Test-RemoteCommand` — 공유 비밀 `ORCH_REMOTE_CMD_SECRET` HMAC-SHA256 서명 + 만료 10분 + 일회성 id (`~/.claude/remote-cmd-seen.txt`) 모두 통과해야 실행 · `key`·`drag` 는 추가로 `ORCH_REMOTE_ALLOW_KEYS=1` · `stop` = kit 워커 창 (`*-auto.bat`) 트리만 · `pause/resume` = 예약 작업이 아니라 표시 파일 (`~/.claude/status-push.paused`) · remote-agent 는 자기 종료 `stop` 만 서명 없이 허용
  - 차단 시험 (가짜 비밀·임시 USERPROFILE): no-secret · unsigned · 정상 서명 ok · 재사용 replayed · 값 변조 bad-signature · 만료 expired · key 미허용 disabled · 다른 명령 서명 bad-signature — 8/8 기대대로
  - 현재 사용자 수준 비밀 미설정 → **운영에서 원격 클릭·키·드래그·stop·pause 전부 차단 (기록만)**
- **H BLOCKED — 대시보드 서명**: `dashboard.py` 는 이 저장소에 있으나 `/control/`·`/remote-cmd/` 요청에 **인증이 없음** → 대시보드에서 서명하면 누구의 요청이든 서명됨 → 우회가 되므로 서명 발급 미구현 · 대시보드 요청 인증 (로그인·토큰) 이 먼저 필요
- **같은 종류 추가 수정**: `dashboard.py` git URL 토큰 4곳 → `GIT_CONFIG_PARAMETERS` 로 helper 등록 (Windows 는 빈 환경변수를 지워 `GIT_CONFIG_COUNT` 방식 불가 — 실측) · 가짜 토큰 시험 통과
- **미적용**: 실행 중 remote-agent (PID 18700) 는 구버전 (G 범위 밖 · 재시작 시 kit 수정본 복사 필요) · dashboard.py 는 이 PC 에서 실행 중 아님
- **회귀**: test_phase20 14/14 · pytest 131 passed (스크립트형 33 기존) · golden 13/13

## 28. remote-agent 교체·재시작 (2026-11-04 19:06 KST · 사용자 승인 · 서명 비밀 미설정 유지)
- 사전 확인: PID 18700 시작 2026-11-02 09:11:56 · 소유자 = 로그인 사용자 · 부모 종료됨 (Run 키 → `remote-agent-silent.vbs` → `%USERPROFILE%\.claude\remote-agent.ps1`) · 설치본 896b61ba = 서명 검사 없음 (클릭·키·드래그를 받는 대로 실행 · 로그 파일 없음 → 실제 처리 이력은 확인 불가 [미확인])
- 새 kit 본 (4bfd6ace): PowerShell 구문 오류 0 · 사용자 수준 `ORCH_REMOTE_CMD_SECRET` 미설정 → 자기 종료 `stop` 외 전부 차단
- 적용: 백업 `remote-agent.ps1.bak-20261104` → 설치본 교체 → PID 18700 만 종료 → vbs 로 재시작 → **PID 21288** (실행 중 확인) · status-push PID 6072·다른 프로세스 미접촉 · Run 키 변경 없음 (vbs 가 설치본 경로를 실행하므로 다음 로그인도 새 버전)
- 대시보드 (P0 유지): `/control/`·`/remote-cmd/` 요청 인증 없음 · 대시보드는 서명을 만들지 않으므로 인증 없는 요청은 클라이언트에서 `unsigned`/`no-secret` 로 차단 (fail-closed) · 서명 발급은 요청 인증 구현 전까지 BLOCKED

## 29. V1.1 미완료 5항목 (2026-11-05 · 유료 $0 · 기존 경로에 연결만)
| 항목 | 연결한 실행 경로 | 증거 | 판정 |
|---|---|---|---|
| A 긴급 요청 | UserPromptSubmit `detect_user_emotion.py` TABLE 1행 (긴급·급해·urgent·ASAP·당장 → 첫 응답 1~3줄 핵심 · 백그라운드 유지 · 시간 보장 X) · SoT `user-emotion.md` 행 | 긴급 2문장 감지 · 일반 문장 미감지 · HEAD 코드 FAIL | **PARTIAL** — 응답 시간 실측 없음 (모델 행동은 지시 주입까지만) |
| B 사실 표기 5종 | `failure-mode.md` (매 세션 로드) · 수정 Agent·Judge 프롬프트 `FACT_TAG_RULE` · `check_requirement_verdicts` 가 [추정]·[예시]·[미확인]·[판독불가] 근거를 met 이어도 UNVERIFIED | 4 태그 모두 차단 · [확인] 근거만 VERIFIED · HEAD FAIL | **PARTIAL** — RPA·OCR·API 개별 Agent 코드 경로는 이 kit 에 없음 (규칙 문서로만) |
| C 연관 작업 자율 | `execution-contract.md` §3 — 확인·같은 유형·회귀·자기 산출물 정리는 묻지 않고 · 운영 DB·배포·재시작·push·삭제·유료·인증은 승인 | 문서 | **PARTIAL** (행동 규칙 · 자동 검증 수단 없음) |
| D 소유 프로세스 정리 | `runner.run` 타임아웃 시 자기가 띄운 프로세스 트리만 종료 + `leftover_pids` 기록 (이전엔 shell 밑 손자 잔존) | 손자 프로세스 종료 시험 PASS · HEAD 코드에선 손자 남음 (시험 잔존 1개를 직접 확인 후 정리) | **PASS** (runner 경로) · 예약·임시파일은 기존 (예약 정산 F7 0 열림 · pytest tmp_path) |
| E Statusline 서브 정렬 | — | VS Code 실제 화면 캡처 필요 · FROZEN 이력 (24+회 핑퐁) | **BLOCKED** (사용자 화면 캡처 필요) |

**회귀**: test_phase20 17/17 · HEAD 코드로 신규 3 FAIL · phase3 26/26 · golden 13/13 · runner·Judge 관련 pytest 34 passed · **phase2 16/21 · phase5 25/30 · pytest phase12 3 FAIL = 전부 가상 메모리 부족 (commit 93.6% · 여유 1.6GB < 2GB) 으로 sandbox 생성이 정책대로 보류됨** — 직접 `repair_sandbox.create` 시험도 같은 보류 메시지 → 이번 변경 무관 · 메모리 여유 회복 후 재실행 필요 [미확인] · fresh clone 미실행 (같은 이유 + 디스크 4.6GB)

## 30. V1.1 실제 동작·회귀 재확인 (2026-11-05 · 유료 $0 · 신규 기능 없음)
**메모리 [확인]**: commit 24.4/25.7GB (95% · 여유 1.28~1.47GB) · 주 사용 = Code 22개 7.35GB · Edge·WebView 약 3.4GB · claude 1.66GB — 사용자 프로그램 (종료 안 함) · 이 프로젝트 테스트·runner·Agent 잔여 프로세스 (1시간+) **0개** · 디스크 C 20.2GB · 메모리 게이트·정책 변경 없음
| 항목 | 실제 동작 확인 | 판정 |
|---|---|---|
| A 긴급 | 감지 → 첫 응답 지시 주입은 [확인] · **우선 처리 경로 없음** [확인] (supervisor·route·ledger·auto-dispatch 에 priority 0곳) · 첫 응답 시간 미측정 | **PARTIAL** (감지만 · 우선순위 처리 미구현) |
| B 사실 표기 | Fix·Judge 프롬프트에 규칙 [확인] · 판정 보완: [확인] 근거 + 부연 [추정] = VERIFIED 허용 · [확인] 없이 [추정]·[예시]·[미확인]·[판독불가] 만 = UNVERIFIED (41a7492) · RPA·OCR 전용 Agent 코드 없음 | **PARTIAL** |
| C 연관 작업 자율 | 자동 실행 [확인]: Stop 마다 요청 원장 게이트·상시 요구사항 게이트·golden (경고) · SessionEnd 정리 hook · **같은 유형 탐색·회귀 선택은 규칙 문서만** (자동 X) | **PARTIAL** |
| D 프로세스·파일 | runner 타임아웃 = 자기 트리 정리 [확인] · 정상 완료·실패는 부모가 끝난 뒤 남은 손자를 찾을 방법 없음 (추적 수단 미구현) · 파일 = 미완료·증거·sandbox 보존 + 후보 기록 (§25) | **PARTIAL** (타임아웃 경로만 PASS) |
| E Statusline 서브 | VS Code 실제 캡처 없음 | **BLOCKED** |

**회귀 (41a7492)**: 운영 폴더 · fresh clone 기본 · fresh clone `ORCHESTRATION_ROOT` 명시 3곳 모두 동일 — verify-fresh-clone 위반 0 · pytest 131 passed / 3 failed (phase12 sandbox 계열) · phase3 26/26 · golden 13/13 · test_phase20 17/17 · **phase2 16/21 · phase5 25/30 = sandbox 생성이 commit 부족으로 보류 → BLOCKED (FAIL 아님 · 직접 create 시험 같은 보류 메시지)** · 기존 실패 기록 보존

## 31. V1.1 A~E 실제 경로 연결 (fd95a68 · 2026-11-05 · 유료 $0 · push 안 함)
**메모리 [확인]**: commit 85.3% · 여유 3.75GB (게이트 90%·2GB 통과) · 사용자 프로세스 종료 0 · 게이트 변경 0 → phase2·5·12·fresh clone 재검증 가능
| 항목 | 수정 전 [확인] | 수정 | 증거 | 판정 |
|---|---|---|---|---|
| A 긴급 | `ORDER BY created_at` 고정 · 감지는 지시 주입만 | `goals.priority` · advance-all 긴급 우선 + 같은 주기 RUNNING · 자동 등재·Ledger→Goal 에서 설정 · `급하지 않아` 제외 · Router·Ledger 는 실행 순서를 정하지 않아 변경 없음 | Mock (일반 20건 대기·1건 50ms): 수정 전 3주기·61번째 → 긴급 1주기·1번째·첫 실행 62ms · 일반 goal 기존 순서 유지 · whitelist·scheduler_only·dry-run 유지 시험 | **PARTIAL** — 처리 순서·mock 측정 PASS · 등재 goal 도 다음 주기(Stop·10분 루프)까지 대기 · 실제 사용자 첫 응답 시간 미측정 · 실행 중 작업 선점 없음 (의도) |
| B 사실 표기 | `[확인]` 글자만 있으면 통과 | handoff `evidence_anchors` (변경 파일·verified 실행 기록) · 요구사항별 근거 대조 · [추정] 구간은 근거에서 제외 | 글자만·없는 줄·없는 파일·무관 파일·실행 기록에 없는 테스트·root 밖 = UNVERIFIED · 실제 경로·기록된 테스트·[확인]+부연 [추정] = VERIFIED · judge_absorb 경유 시험 | **PARTIAL** — 인용 위치 실재까지 검사 · 그 줄이 요구사항을 실제 충족하는지는 Judge 판단 · 실제 유료 Judge 미실행 · 이전 handoff 는 anchors 없어 기존 규칙 |
| C 연관 작업 | Stop 게이트·golden·SessionEnd 정리는 연결됨 · 회귀 선정 없음 | `affected_tests` — Judge 프롬프트 미실행 후보 표시 · `/verify` 4단계 · CLI | 참조 테스트만 선정 시험 · 이번 변경 8개 선정 · 승인 정책 변경 0 | **PARTIAL** — 회귀 선정 연결 · 미실행 후보는 표시만 (자동 실행·차단 X) · 같은 유형 누락 확인은 규칙 문서 (판단 필요 · 자동 X) |
| D 프로세스·파일 | 타임아웃만 정리 · 부모 종료 후 손자 추적 불가 | 실행 중 하위 프로세스 관측 (pid + 생성 시각) · 정상·실패·중단·타임아웃 종료 시 관측된 것만 정리 · 후보 목록 `.claude/state/cleanup-candidates.txt` (`.repair-sandbox`·`.claude/tasks`·integrity-baseline 제외 · 삭제 X) | 정상·실패·중단 시험 PASS · 무관 프로세스 생존 · 후보 기록 시 원본 유지 · 기록된 실행 220건에 상주 명령 0 | **PASS** (runner 경로) — 관측 주기 0.2초보다 짧게 끝나는 중간 부모의 자식은 놓칠 수 있음 · psutil 없으면 `leftover_checked=False` (미측정) |
| E Statusline | 서브 정렬·요청 문구 밀림 미해결 | 코드 변경 없음 (FROZEN) | 2026-11-05 화면 캡처에 VS Code 미표시 (사용자 Excel · 파일 즉시 삭제) · 출력 측정: 15줄 중 빈 줄 3개 (`statusline_context.py:1932·1944·1963`) · 폭 ≤ 119 (cols 120) | **BLOCKED** — 빈 줄 3개가 3줄 밀림 원인일 수 있음 [추정] · 수정 후 VS Code 캡처 없이는 판정 불가 |

**회귀 (fd95a68 · fresh clone · 운영 폴더·DB 무변경)**: verify-fresh-clone 위반 0 (466 파일) · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 29/29 · phase3 26/26 · golden 13/13 · pytest 146 passed (기준선 134 + 신규 12) · 33 ERROR = 스크립트형 테스트 수집 오류로 기준선과 동일 · 신규 12건은 9564a84 코드에서 FAIL (일부는 새 인자·키 부재로 인한 실패) · lint 미측정 (ruff 미설치)
**보존 [확인]**: goals 161·tasks 152 유지 · `priority` 열 추가만 · Goal #77 FAILED 유지 · 원격 인증·서명 비밀 변경 0 · 토큰 교체 제외 · 유료 호출 0 · 삭제·병합·push 0
**미처리**: changelog 알림 (v2.1.318 까지) 은 이번 지시가 신규 항목 금지라 평가·적용 안 함 · `changelog-new.md` 유지 · 임시 clone 4.6GB 는 scratchpad 에 남음 (rm -rf 차단 훅)

## 32. V1.1 외부 근거·내부 구현·실행 결과 3축 검증 (c653a93 · 2026-11-05 · 유료 $0 · push 안 함)
| 항목 | 판정 | 내부 구현 | 실행 결과 | 외부 근거 | 남은 공백 |
|---|---|---|---|---|---|
| A 긴급 | **PASS (Goal 처리 경로 한정)** | `priority` · advance-all · `_has_goal_token` | 실제 hook → 실제 Stop guard → 실제 runner: 일반 3건 RUNNING 뒤 등록한 긴급 goal 이 exec 첫 순서 · 4건 모두 VERIFIED · hook 2.3s · Stop guard 5.0s (clone) | SQLite ADD COLUMN [확인] | 명시 토큰 없는 긴급 문장은 goal 이 아니라 메인 응답 지시 · 사용자 첫 응답 시간 미측정 · Claude 세션이 아닌 스크립트로 hook 호출 |
| B 사실 검증 | **PARTIAL** | evidence_anchors · external_scope · external-evidence (read 만 인정) | 시험 PASS (가짜 Judge 응답) | 설치 psutil 7.2.2 소스 대조 [확인] | 유료 Judge 실호출 미실행 · 외부 자료 대조는 메인 Claude 수행 (자동 수정 체인은 not_checked 로 멈춤) |
| C 자율 연관 작업 | **PARTIAL** | run_affected_regression · /verify 3축 | 선정·재시도·스크립트형 구분 시험 PASS (가짜 runner) | pathspec `*` = `/` 매치 [확인] | 실제 체인에서 회귀 실패 재현 안 함 · 같은 유형 누락 확인은 규칙 |
| D 프로세스·파일 | **PASS (runner 경로)** | 관측 기반 정리 · 불필요 status() 제거 | 정상·실패·중단 PASS · 무관 프로세스 생존 | psutil·Microsoft 대조 [확인] | 0.2초 미만 중간 부모의 자식 미관측 (psutil 문서가 같은 한계 명시) · Job Object 가 대안 |
| E Statusline | **BLOCKED** | 변경 없음 | VS Code 캡처 없음 | 해당 없음 | 사용자가 VS Code 캡처 제공 필요 |

**공식 자료 대조 (2026-11-05 · 본문 확인)**
| 대상 | 자료 | 결과 |
|---|---|---|
| PID 재사용 | [psutil API](https://psutil.io/api/) (개발판 · 설치 7.2.2 소스 일치) | `is_running()`·`kill()` 재사용 안전 → 일치 |
| 부모 소실 | 같은 문서 · [Win32_Process](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process) (2020-07-23) | 중간 부모가 없으면 자손 추적 불가 · PID 재사용 → 실행 중 관측 설계와 일치 |
| 프로세스 묶음 | [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) (2025-07-14) | 자식 자동 소속 · 미적용 (후속 후보) |
| 타임아웃 | [Python subprocess](https://docs.python.org/3/library/subprocess.html) (문서 3.15 · 설치 3.14.2) | 타임아웃은 자식을 안 죽임 → 정리 코드 필요 일치 |
| 스키마 | [SQLite ALTER TABLE](https://www.sqlite.org/lang_altertable.html) | 일반 ADD COLUMN 은 데이터 재작성 없음 |
| 테스트 선정 | [gitglossary](https://git-scm.com/docs/gitglossary) · [git-ls-files](https://git-scm.com/docs/git-ls-files) (2.55 기준 · 설치 2.52) | `*` 가 하위 폴더까지 매치 · 일치 |
| 미확정 | psutil Windows `status()` 지연 (제3자 저장소 이슈 · 검색 결과만) | 필요 없는 호출이라 제거 |

**발견·수정**: ① 실제 hook 종단 시험 FAIL — 작업 동사 없는 `[auto-goal]` 이 관문에서 걸러짐 (mock 으로는 못 찾음) → 수정 후 PASS ② PowerShell 도구는 PreToolUse matcher 밖 → 화면 캡처 훅만 연결 · **block-dangerous·파일 삭제 등 Bash 훅은 PowerShell 에 여전히 미적용 [확인] (후속 승인 필요)**
**화면 캡처**: `block_screen_capture` Bash·PowerShell 차단 (dispatcher 파이프 시험 PASS) · matcher 변경의 실제 세션 적용은 다음 세션 [미확인]
**회귀 (c653a93 · fresh clone)**: verify-fresh-clone 위반 0 (467 파일) · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 36/36 · phase3 26/26 · golden 13/13 · pytest 153 passed · 33 ERROR 기준선 동일 · lint 미측정 (ruff 미설치)
**보존 [확인]**: goals 161·tasks 152 · Goal #77 FAILED · 메모리 게이트·승인 정책 변경 0 · Statusline 변경 0 · 토큰 제외 · 유료·push·삭제 0

## 33. PowerShell 차단 · B·C 실행 증거 · 승인 전 준비 (d7af789 · 2026-11-05 · 유료 $0 · push·삭제 0)
**판정 유지**: A·D PASS (범위 한정) · B·C PARTIAL · E BLOCKED

| 항목 | 외부 근거 | 내부 구현 | 실행 결과 | 판정 |
|---|---|---|---|---|
| PowerShell 차단 | Claude Code hooks · Remove-Item · about_PowerShell_exe · about_Pwsh · Invoke-Expression · about_Execution_Policies (본문 확인) | 기존 hook 재사용: block_dangerous_bash·block_file_deletion·approval-gate + matcher 확대 | 위험 38건 차단 1 → 38 · 정상 21 통과 · 실제 PowerShell 도구 차단 확인 · 설치 5.1 별칭 6종 실측 | **제한 범위 PASS** |
| B 실물 경로 | 내부 로직 (외부 축 생략) | handoff anchors | 실제 git 변경·runner 기록·handoff: 거짓 근거 5종 UNVERIFIED · 실제 근거 VERIFIED (Judge 응답은 손으로 작성) | PARTIAL (실제 LLM Judge 미호출) |
| C 회귀·같은 유형 | git grep·pathspec 문서 | run_affected_regression · same_pattern_candidates | 실제 runner·pytest: 회귀 실패 → 재시도 후 실패 → 수정 후 통과 · 남은 줄 위치 탐지 · 실제 체인 연결 | PARTIAL (유료 체인 실호출 없음 · 후보 판단은 사람·Judge) |

**미차단 10건 [확인]**: 변수 호출 · 문자열 조립 · splatting · Set-Alias · 스크립트 파일 · python shutil.rmtree · 와일드카드 삭제 (`dir/*`) · `$_.Delete()` · `[IO.File]::Delete` · robocopy /MIR. 문자열 판정의 한계 — 실수 방지 장치이며 보안 경계가 아니다 (Microsoft 실행 정책 문서도 같은 구분).
**오탐 2건 수정**: 승인 패턴이 `|iex` 문구만으로 매치 → 다운로드+실행일 때만 · same-pattern 부분 일치로 자기 자신 탐지 → 줄 전체 일치만.
**회귀 (d7af789 · fresh clone)**: 위반 0 · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 41/41 · phase3 26/26 · golden 13/13 · pytest 158 passed · 33 ERROR 기준선 동일 · 긴급 종단 PASS · lint 미측정
**Push 준비 [확인]**: origin/main 대비 ahead 7 · 23+ 파일 · 비밀 패턴 0 · 금지 경로 0 · 1MB+ 파일 0 · whitespace 오류 0 · gitleaks 미설치 (미측정) · 실제 push 안 함
**유료 Judge 산정**: Opus 5.5 $4/$20 per MTok · 기존 Judge 8회 $0.25~$0.36 (평균 $0.32) · 수정 Agent 6회 $0.36~$0.39 · 일일 예산 NULL 이라 현재 호출 불가
**임시 clone**: 사용 프로세스 0 · 모두 이 세션 생성 · alternates 없음 · 논리 24.45GB 이나 실제 회수 0.22GB (kit .git 과 하드링크 공유 4.85GB) · 이전 보고 "약 4.7GB" 는 잘못 · 삭제 안 함
**운영 DB 흔적 [확인]**: 승인 대기 3건 (appr-e8dd1eed7181·appr-d62d0475d9cb·appr-d20e12957e0d) · tasks 152→155 · 작업 폴더 pytest 가 executions 에 시험 행 추가 → 테스트 임시 DB 로 격리 · 기존 행은 보존 · goals 161·Goal #77 FAILED 유지

## 34. R160 종료 판정·PowerShell 경계·B·C 재측정 (1fb18a4 · 2026-11-05 · 유료 $0 · push·삭제 0)
**판정 유지**: A·D PASS (범위 한정) · B·C PARTIAL · E BLOCKED

**R160 사실관계 [확인]**: 등록 상태 `approval_required` (승인 사유 배포·운영·유료·운영 db = 요청문이 그 작업을 금지하며 언급한 단어) → Claude 가 `complete` 호출 → `verified` 로 전이 (이 상태가 Stop 차단) → Stop 차단 1회 → verification 문장을 `PASS` 로 재호출 → `completed` → gate exit 0. 차단 원인을 Claude 가 만들고 같은 수단으로 풀었다. 사용자 승인 없음.
**요구사항 대조**: 지시 A~E 와 B·C 증거 강화는 수행됐고 push·삭제·유료 호출 없음 → "요청 처리 완료" 는 근거 있음 · "기능 검증 완료" 는 아님 (B·C PARTIAL·E BLOCKED). 기록 evidence 에 미검증 항목은 적혀 있으나 PASS 한 단어로는 구분 불가. **기록 수정 안 함** (ledger 해시 aca69b28f24c 전후 동일).
**Stop "18회" [확인]**: 반복 호출이 아니라 `hookCount=18` = Stop 1회에 등록된 hook 수 (settings.json Stop hook 18개) · transcript 기록 Stop 9건 · 차단 feedback 1건. 무한 반복 아님: 같은 미완료 집합 연속 차단은 GATE_LOOP_MAX=3 후 통과 + 로그 (test_phase17).
**재발 방지**: `complete` 는 승인 대기 항목을 --user-approved 원문 없이 바꾸지 않음 (시험 PASS) · 게이트 문구·§2 규칙에 "종료를 위한 PASS 금지·요청 완료≠기능 판정" 명시. **한계**: 일반 요청의 PASS 는 여전히 문자열 신고 — 실제 수행 여부를 코드가 증명하지 않는다.

**PowerShell 남은 10건 경계 검토**
| 수단 | 효과 | 이 PC 적용 |
|---|---|---|
| Claude Code sandbox | OS 수준 · 자식까지 · 쓰기 범위 제한 | native Windows 미지원 ([문서](https://code.claude.com/docs/en/sandboxing)) · WSL2 필요 |
| permissions deny | 도구 사전 판정 · 문자열 규칙 | deny 0건 · defaultMode=bypassPermissions · 같은 문자열 한계 |
| App Control + 제약 언어 모드 | Microsoft 보안 경계 ([문서](https://learn.microsoft.com/en-us/powershell/scripting/security/security-features?view=powershell-5.1)) · .NET 차단 | 시스템 정책 · cmdlet 은 허용이라 Remove-Item 못 막음 · 현재 FullLanguage |
| Execution Policy·수동 언어 모드 | defense-in-depth · 보안 경계 아님 | 삭제 통제 수단 아님 |
| JEA | NoLanguage·명령 제한 | PowerShell Remoting 세션용 · 로컬 도구에 부적합 |
| NTFS ACL·권한 낮은 계정 | OS 가 삭제 거부 | 유일한 로컬 파일 경계 · 계정·권한 변경 = 승인 필요 · 미적용 |
결론: 이 PC 에는 현재 파일 삭제 보안 경계가 없다 [확인]. hook 은 실수 방지. 실측 5.1: 변수·문자열·splatting·Set-Alias 모두 Remove-Item 으로 실행됨 (-WhatIf · 삭제 없음) · 정규식 추가 안 함 · 38/38·21/21 유지.

**B 3축 기록**
| 대상 | 공식 문서 (본문) | 코드 | 실행 |
|---|---|---|---|
| subprocess | 3.14.10 문서 (설치 3.14.2 · 패치 차이) · run 은 종료·communicate 는 미종료 | runner 는 Popen+communicate → 자체 정리 필요 | 타임아웃·정상·실패·중단 시험 |
| psutil | 개발판 문서 (설치 7.2.2) | children·is_running·kill 소스 일치 | 무관 프로세스 생존 |
| git | 2.55 기준 문서 · 2.52 전용 페이지는 2.51 리다이렉트로 원문 없음 [미확인] | ls-files pathspec | 설치 2.52 에서 하위 폴더 선정 시험 |
| Judge 인용 | 해당 없음 | evidence_is_anchored | 거짓 5종 UNVERIFIED · 실제 1건 VERIFIED (손으로 쓴 응답) |
**실제 Judge 기록 재생**: handoff 203건 · llm_verdict 88건 · 요구사항별 응답 **0건** [확인] → 실제 LLM 이 `[확인] 경로:줄` 형식을 내는지 미측정. Mock PASS 를 실제 PASS 로 승격하지 않음.

**C 재측정 (실제 fix 커밋 30건 재적용)**: 후보 10 → 5 (옮긴 줄·일반 구문 제외). 5건: 오탐 1 (`ORDER BY created_at` = 표시용 목록) · 일반 구문 2 · 미판정 2 · **정탐 확인 0** · 미탐: 이름이 다른 복사본 못 찾음 (시험으로 확인) · 재현율 미측정. 자동 실행: 회귀 선정·실행 (수정 체인) · 규칙만: 같은 유형 판단 · /verify 내 실행은 Claude 수행.
**회귀 (1fb18a4 · fresh clone)**: 위반 0 · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 44/44 · phase3 26/26 · golden 13/13 · pytest 161 passed · 33 ERROR 기준선 동일 · 긴급 종단 PASS · PowerShell 38/38·21/21 · 미차단 10 유지 · lint 미측정
**보존 [확인]**: goals 161 · tasks 155 (승인 대기 3건 그대로) · Goal #77 FAILED · ledger 해시 동일 · 로컬 커밋 ahead 9 · Statusline·토큰·원격 설정 변경 0 · 화면 캡처 0

## 35. Stop 종료 허가와 검증 PASS 분리 (ca91ec2 · 2026-11-05 · 유료 $0 · push·삭제·캡처 0)
**판정 유지**: V1.1 PASS 2 · PARTIAL 2 · BLOCKED 1 (A·D 범위 한정 · B·C PARTIAL · E BLOCKED)

**선행 확인**: 1fb18a4 = 승인 대기 보호·게이트 문구·same-pattern 필터 · 05ad972 = 문서만. 재현: 6cc4793 은 R160 경로 재현 · 1fb18a4 이후 차단. 그러나 05ad972 까지 PARTIAL·BLOCKED 도 gate=2 — 사실대로 적으면 막히고 PASS 로 적어야 풀리는 구조가 남아 있었다.

**상태 전이 (임시 Ledger · gate_matrix)**
| 시나리오 | 6cc4793 | 05ad972 | ca91ec2 |
|---|---|---|---|
| 정상 PASS | completed · 0 | 같음 | 같음 |
| 승인 대기에 complete | verified → gate 2 → PASS 로 통과 | 상태 유지 · 0 | 같음 |
| PARTIAL·BLOCKED + 증거 | verified · 2 | verified · 2 | **verified 유지 · 0** (재진입도 0) |
| FAIL | 2,2,2 후 루프 해제 | 같음 | 같음 · 기록 유지 |
| 증거 없는 PARTIAL | implemented · 2 | 같음 | 같음 |
| 임의 문장 | verified · 2 | 같음 | **거부 · 상태 유지** · 2 |
| pending | 2 | 2 | 2 |

**세 개념**: 작업 수행 = status · 검증 결과 = verification (PASS·PARTIAL·BLOCKED·FAIL) · 종료 허가 = gate 판단. 새 상태 없음. PARTIAL·BLOCKED 는 완료로 세지 않음.
**호출 관계 [확인]**: Stop 1회 = hook 18개 · 차단 가능 = stop-request-ledger-gate · stop-standing-gate · stop-six-guards · 재진입 결함: Standing gate 가 stop_hook_active 를 안 보고 `2>/dev/null` 로 사유를 숨김 · six-guards 가 같은 검사를 또 수행. 수정: active 면 미해결 유지하고 허용 · 사유 표시 · six-guards 중복 제거 (측정 active=False standing=2 / True standing=0, six=0 · 요구사항 ACTIVE 유지).
**공식 대조**: [Claude Code hooks](https://code.claude.com/docs/en/hooks) 2026-11-05 본문 확인 · 설치 2.1.318 · stop_hook_active 확인 권고 · 연속 8회 상한 · exit 2 stderr 전달 → 구현 정합. 문서는 최신판 기준이며 2.1.318 전용 판본은 확인 못 함.
**운영 사례**: R161 PASS · R162 PARTIAL 기록 후 gate=0 · 미완료 5건 유지 (승인 대기 4 + R162).
**회귀 (ca91ec2 · fresh clone)**: 위반 0 · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 52/52 · phase3 26/26 · golden 13/13 · 긴급 종단 PASS · PowerShell 38/38·21/21 · 거짓 근거 5종 UNVERIFIED · 같은 유형 후보 5건 유지.
**pytest 전체**: 1회차 168 passed·1 failed (test_phase17 test_dag_deferred_is_skipped_not_failed) · 2회차 2 failed (+ test_loop_survives_winerror_1455) · 이후 ca91ec2 169 passed 2회 · 1fb18a4 161 passed 1회 · 단독 실행 통과 · 33 ERROR 동일. 실패 2회는 commit 약 90% 시점 · 재현 안 됨 · **원인 미확정 [미확인]** — 이번 변경과의 관련은 입증도 배제도 못 함.
**남은 위험**: PARTIAL 도 문자열 신고라 작업 회피에 쓰일 수 있음 · 일반 PASS 는 증거 내용을 코드가 검증하지 않음 · Standing 미해결은 두 번째 Stop 부터 통과 · loop 해제는 FAIL 도 종료 허용 (기록은 유지) · six-guards 의 advance-all 은 15초 hook 제한 안에서 실행.
**보존 [확인]**: R160 기록 무변경 · goals 161 · tasks 155 (승인 대기 3건 포함) · Goal #77 FAILED · 로컬 커밋 ahead 11 · Statusline 변경 0

## 36. R160 감사 메모 · pytest 간헐 실패 조사 (450796d · 2026-11-05 · 유료 $0 · push·삭제·캡처 0)
**판정 유지**: V1.1 PASS 2 · PARTIAL 2 · BLOCKED 1

### R160 감사 메모 (Ledger 기록 무변경)
| 구분 | 내용 |
|---|---|
| 현재 기록 | status=completed · verification=PASS · user_approved 없음 (수정 안 함) |
| 등록 근거 [확인] | 프롬프트 hook 출력 `[ledger] + R160 (APPROVAL REQUIRED)` · approval_reasons 배포·운영·유료·운영 db = 실제 승인 대기로 등록된 요청 |
| 경위 [확인] | Claude 가 complete 호출 → verified 로 전이되어 Stop 차단 발생 → verification 을 문장에서 PASS 로 재호출 → completed · 사용자 승인 없음 |
| 이 기록의 의미 | 요청 작업 수행 완료만 뜻함. V1.1 기능 검증 완료가 아니다 (B·C PARTIAL · E BLOCKED) |
| 승인 필요 작업 실행 여부 | push·삭제·유료 호출·배포 없음 [확인] · 승인 사유는 금지 문구의 단어 감지 |
| 조치 | 기록 유지 · approval_required 복원 안 함 · 재발 방지는 1fb18a4·ca91ec2 |

### §35 정정
- §35 의 "1회차 test_dag_deferred_is_skipped_not_failed" 는 **잘못된 기록**이다. 1회차 로그는 tail -6 으로 잘려 실패 테스트 이름이 없다. 그 이름은 2회차 것이다.

### 간헐 실패 조사
| 회차 | 시각 | 원인 | 근거 |
|---|---|---|---|
| 2회차 (2 failed) | 17:2x | **Claude 절차 경합 [확인]** — 같은 clone 을 git reset 하는 동안 pytest 실행 | clone reflog 17:26:53~55 reset · 재현: reset 없음 0/6 실패 · reset 동시 6/16 실패, 같은 두 테스트 |
| 1회차 (1 failed) | 17:21~23 | **[원인 미확인]** — 테스트 이름·traceback 없음 | 이 PC commit 90.0% 경계 시점 [확인] · 실제 메모리 의존 시험이 후보 [추정] |

**발견한 실제 결함 [확인]**: pytest 일부가 실행 PC 메모리에 판정이 좌우됨. commit_memory 95% 재현: 수정 전 phase12 3건 실패 → conftest 고정 후 0건. 환경변수로 게이트만 닫으면 18건 실패 (phase18 14 · phase12 3 · phase17 1). 메모리 게이트 시험은 값을 직접 주입해 유지.
**배제 [확인]**: 단독·phase17 파일·phase12+17 순서는 게이트 조건과 무관하게 통과 → 순서 의존 재현 안 됨. 임시 DB·프로세스 충돌은 재현 안 됨. skip·xfail·재시도 추가 없음.
**공식 대조**: [pytest flaky](https://docs.pytest.org/en/stable/explanation/flaky.html) (본문 · 통제되지 않은 시스템 상태·공유 상태가 원인 · xfail 상시 격리는 위험) · [Win32 오류 1455](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699-) (페이징 파일 부족 · 2025-07-14). 설치 pytest 9.1.1 · 문서는 stable 판.
**회귀 (450796d · fresh clone 단독 실행)**: 위반 0 · phase2 21/21 · phase5 39/39 · phase12 16/16 · phase20 52/52 · phase3 26/26 · golden 13/13 · pytest 169 passed · failed 0 · 33 ERROR (스크립트형 수집 오류 · 기존 동일) · 긴급 종단 PASS · PowerShell 38/38·21/21 · 실제 근거 VERIFIED. 전체 로그 보존 (실패 이름 유실 방지).
**보존 [확인]**: R160 기록 무변경 · goals 161 · tasks 155 · 승인 대기 3건 · Goal #77 FAILED · 로컬 커밋 ahead 13 · Statusline 변경 0

## 37. B·C 남은 검증 (2026-11-06 · 원래 세션 인수 · 기준 2fae615 · 유료 $0 · push 안 함)
**B — 공식 근거 대조**: git-scm.com `git-config` ENVIRONMENT · `git` · `gitcredentials` 확인 — ① `GIT_CONFIG_COUNT`/`KEY_<n>`/`VALUE_<n>` 만 문서화 · **`GIT_CONFIG_PARAMETERS` 는 문서에 없음** (7694ecd 에서 dashboard.py 가 쓰던 내부 변수) ② "credential.helper 빈 문자열 = helper 목록 초기화" ③ "!" 로 시작하면 shell snippet ④ 빈 `GIT_CONFIG_VALUE_<n>` 허용 여부는 문서에 없음 (Windows `os.environ` 은 빈 값을 지움 — §27 실측)
- 최소 수정: dashboard.py → 문서화된 `GIT_CONFIG_COUNT=1` + helper 를 기존 자격 관리자 뒤에 덧붙임 + `GCM_INTERACTIVE=never` (대화창 X) · 가짜 토큰·존재하지 않는 호스트 시험: 자격 관리자 비대화 실패 후 helper 가 전달 rc 0 [확인]
- 실제 LLM Judge 근거 형식 측정 = 유료 호출 → **BLOCKED (승인 대기)**
**C — 같은 유형 탐색 실측** (`same_pattern_candidates` · 이 세션의 실제 결함 2건을 임시 clone 에 재현):
| 재현 | 결과 |
|---|---|
| lock 삭제 결함 · 사본만 고침 (원본 plugins 쪽 그대로) · 미스테이징 | 후보 6건 = 전부 정탐 (원본 쪽 같은 줄) [확인] |
| 같은 경우 · **`git add` 후 검증** | **후보 0건 (미탐)** → `git diff HEAD` 기준으로 수정 · 시험 추가 |
| 토큰 URL · ps1 만 고침 (bat·py 는 문법 다름) | 0건 — 글자 그대로 비교 방식의 한계 (미수정 · 기록) |
- 자동 실행 여부: Stop 게이트·golden·SessionEnd 정리는 자동 [확인 §30] · 같은 유형 후보는 `/verify`·Judge 경로에서 호출 (d7af789) · 문서 규칙과 자동 실행 구분 유지
**회귀 (commit 87% · 여유 3.2GB 회복 후)**: pytest 171 passed · failed 0 (33 수집 오류 기존) · phase5 39/39 · phase2 21/21 · phase3 26/26 · golden 13/13 · test_phase20 54/54 — §30 의 메모리 BLOCKED 는 이번에 해소 확인
**판정**: B PARTIAL (공식 대조·수정 [확인] · 실제 Judge 측정 BLOCKED) · C PARTIAL (정탐 확인 · 스테이징 미탐 수정 · 문법 다른 같은 유형 미탐 남음)

## 38. Request Ledger 자동 등록 오탐 (2026-11-06 · 기준 a13c4ff · 유료 $0 · push·삭제·캡처 0)

**재현 (수정 전 · 이번 세션 사용자 메시지 78건을 실제 hook `run()` 으로 임시 폴더에서 재실행)**: 승인 필요 35 · 등록 8 · 건너뜀 22 · 보류 13. 붙여 넣은 상태 보고 R167·R169 = `approval_required` (본문의 '유료'·'운영'·'배포' 단어) · R170 = 등록 ('개발' 단어) · 이번 개발 지시 자체는 `cancel` 로 분류돼 **등록 안 됨** (본문의 "삭제하지 마" 제약 문장).

**공식 근거** [확인 · https://code.claude.com/docs/en/hooks · 2026-11-06]: UserPromptSubmit 입력은 `prompt` 필드 · "붙여 넣은 글은 `<pasted_content id="…">` 줄과 `</pasted_content id="…">` 줄 사이에 오므로 hook 이 prompt 를 파싱하면 그 줄을 고려하라" · Stop 의 exit 2 = 멈추지 않고 계속 · stderr 가 Claude 에게 사유로 전달.

**수정 (최소)**
- `ledger_auto_register.py`: 붙여 넣은 글을 분리. 직접 쓴 글이 있으면 그것만 분류 · 붙여 넣은 글만 왔으면 지시 표지(`대상:` 줄 · 반말 명령형 문장 끝 "~해." "~하지 마." "~할 것." · "승인한다" 등)가 있을 때만 실행 요청 · 없으면 `pasted_report` 로 raw 로그에만 보존. 승인 판정은 같은 분류 대상 글에서 금지·부정 문장("금지", "않", "하지 마")을 뺀 뒤. 취소 판정은 60자 미만만. 대화 요약 이어가기 메시지는 사용자 지시 아님.
- `request-ledger.py`: Stop gate 차단 문구에 "자동 등록 오탐이면 PASS 로 닫지 말고 `invalid-registration`" 안내 추가 · `invalid-registration` 은 승인 대기 항목을 거부 (승인 기록 보호).
- 기존 Ledger R1~R170 은 수정·삭제 안 함 (R167~R169 승인 대기 그대로 · R170 은 이전 PASS 기록 그대로).

**수정 후 (같은 78건)**: 승인 필요 31 · 등록 16 · 건너뜀 11 · 보류 14 · 사용자 지시 아님 6. R167·R169·R170 = `pasted_report` (등록 0) · R168 (Push 승인 지시) = 등록 · 이번 개발 지시 = 등록 (`execute`·`pending`). 붙여 넣은 지시 중 `대상:` 줄이 없는 번호 목록 지시("…다시 확인해.")도 등록.

**시험**: test_phase19 +4 (보고 3종 미등록 · 붙여 넣은 지시 3종 등록·부정 문장 승인 제외 · 직접 쓴 글 우선·실제 위험 지시는 승인 대기 유지·짧은 취소·요약 메시지 · gate 안내와 승인 대기 보호). 수정 전 코드에서 4/4 FAIL → 수정 후 PASS. 실제 `prompt-dispatch.py` 경로로 임시 폴더에서 붙여 넣은 보고 → 등록 0 [확인].
**회귀**: pytest 175 passed (171 + 신규 4) · 33 수집 오류 기존 그대로 · golden 13/13.

**한계 [추정]**: 표지 판정은 단어·문장 끝 규칙이라 완전하지 않다. 존댓말 평가문 안에 지시가 섞인 경우(예: "~확인 바랍니다")는 보고로 볼 수 있고, 감사 보고서처럼 "~함"으로 끝나는 결함 목록(78건 중 1건)은 지시로 등록되지 않는다. 그런 메시지는 직접 쓴 한 줄("이거 고쳐줘")을 붙이면 그 글로 판정한다.

## 39. V1.1 B·C·E 승인 불필요 작업 (2026-11-06 · 기준 38d3d7b · 유료 $0 · push·삭제·캡처 0)

**B — Mock·수동 판정과 실제 LLM Judge 분리**
- 발견 [확인]: `judge_absorb` 는 판정 JSON 출처를 기록하지 않았다 → 실제 Agent Judge·CLI stdin 손 작성·시험 가짜 응답이 같은 VERIFIED 로 남음. 운영 judge-queue 208건: VERIFIED 19 · 실제 Judge Agent 실행 기록 (metrics `claude-agent:judge`) 14회 $4.72 → 최소 5건은 실제 Judge 가 아님. phase3 시험 test_06 이 손으로 쓴 응답을 운영 queue 에 기록하는 것이 원인 후보 [추정]. 요구사항별 판정이 있는 handoff 0건 (§34 와 동일).
- 수정: `judge_source()` · `final_verdict.judge_source.kind` = `llm_agent` (Agent 세션 ID + 청구 비용 둘 다 있을 때만) · `agent_unattested` (mock Agent) · `cli_stdin` · `unattested` (직접 호출). 자동 체인은 실제 Agent 결과를 그대로 넘김. **판정 결과는 바꾸지 않음** (기록 분리만 · 과거 기록 무변경).
- `[확인]` 글자만으로 통과하는 경로: anchors 가 있으면 차단 (§31) · anchors 없는 경로 = 요구사항 스냅샷 없는 handoff (현재 0건 · judge_handoff 는 요구사항이 있으면 항상 anchors 생성) [확인].
- 시험 +3: 출처 4종 구분 · CLI 경로 `cli_stdin` · 체인이 Agent 결과 전달. HEAD 코드 3/3 FAIL → 수정 후 PASS.

**C — 실제 수정 체인 종단 (무료)**
- 발견 [확인]: 자동 체인(`agent_repair_chain`) 이 실제 Judge 에 보내는 프롬프트에는 같은 유형 후보가 없었다 (handoff 파일에만 있음) → 자동 수정에서 같은 유형 누락을 아무도 판단하지 않음.
- 수정: 체인이 `same_pattern_candidates` 를 Judge 프롬프트에 넣고 남은 동일 결함은 `missing_requirements` 로 보고하게 함 (기존 필드 → REPAIRING).
- 종단 시험 `chain_e2e_driver.py` (신규) + test_phase20: 임시 git 저장소 · ROOT·DB·sandbox root 모두 임시 · 유료 Agent 만 가짜 · sandbox·runner·pytest·회귀·통계 판정·judge_absorb·commit·fast-forward 반영은 실제 코드.
  | 시나리오 | 결과 [확인] |
  |---|---|
  | 하드코딩 수정 (대상 시험만 통과) | 회귀 시험 자동 선정·실패 → 1회 재시도 후 실패 → **Judge 호출 전 중단** |
  | 새 외부 패키지 import | Judge VERIFIED 응답에도 외부 자료 미확인 → UNVERIFIED · 반영 안 함 |
  | 근본 수정 | 회귀 통과 · Judge 프롬프트에 같은 버그 복사본 `label.py` 전달 · VERIFIED · 대상 브랜치만 반영 · main 원본 무변경 · 출처 `agent_unattested` |
  HEAD 체인 코드에서 FAIL (같은 유형 후보 미전달) → 수정 후 PASS.
- 남은 공백: 실제 유료 Agent 로 이 체인을 돌린 기록 없음 (BLOCKED · 승인 필요) · 같은 유형 탐색은 글자 그대로 비교라 문법이 다른 복사본은 못 찾음 (§37 그대로) · 자동 체인은 공식 문서를 스스로 읽지 않고 미확인이면 멈춤 (설계상 · 외부 페이지를 무인 체인에 넣지 않음).

**E — Statusline 문자열 검증 (디자인 무변경)**
- 실제 설정 경로 `statusline-wrapper.sh → statusline_context.py` 출력 (COLUMNS=120) [확인]: 14행 · 빈 줄 3 (그룹 구분 · 코드 `out.append("")` 의도된 배치) · 모든 행 폭 ≤ 119 · 내용 11행 모두 왼쪽 `│` 가 13번째 셀 (wcwidth · 이모지+VS16=2셀) · 서브 보조 행도 같은 계산 (2+11).
- 공식 문서 [확인 · https://code.claude.com/docs/en/statusline · 2026-11-06 · 날짜 표기 없음]: 출력 한 줄 = 한 행 · 폭은 `COLUMNS` 환경변수 · 이스케이프 코드가 있는 여러 줄 출력은 렌더 문제가 더 잘 생김. 빈 줄 처리·커서 이동 코드(CHA)·VS Code 렌더는 **문서에 없음** [미확인].
- 문서·코드 불일치 [확인]: `operational-freeze.md` 는 CHA `ESC[18G` 를 필수 전제로 적었으나 96a0a0a (10-27 11:05) 에서 제거됐고 그 뒤 동결 상태에도 없음. 동결 대상이라 수정 안 함 · 기록만.
- 시험 +1: 실제 출력의 정렬·폭·빈 줄 수. **실제 화면 판정은 이 시험으로 하지 않음** → VS Code 캡처로만.

**운영 데이터 사고 방지 [확인]**: 스크립트형 시험 phase2·3·5·12 는 운영 DB 에 직접 쓴다 (sandbox 만 격리). 운영 폴더에서 회귀 묶음을 시작했다가 pytest 단계에서 중단 (스크립트형 시험 실행 0 · 소유 확인한 시험 프로세스만 종료) · goals 161 · tasks 155 · Goal #77 FAILED 유지. 스크립트형 시험은 fresh clone 에서만 실행.
**Ledger 관찰 [확인]**: Push 승인 지시 = R171 `execute` 정상 등록 · 이번 개발 지시 = R172 `approval_required` (사유 '유료') — 부정문 아닌 "유료 Judge 실검증을 분리해 기록" 줄의 단어 감지 · 오분류 사례로 기록 · 상태 변경 안 함.
**회귀 (운영 폴더 · pytest 만)**: 180 passed · failed 0 · 33 수집 오류 기존 그대로.

**fresh clone 회귀에서 발견한 승인 게이트 fail-open (같은 날 · 1차 fresh clone ed60f24)** [확인]
- 증상: phase5 Test 12 `categorized=0/4` (38d3d7b 에서도 동일 → 이번 B·C·E 변경 무관). 위험 명령 4건은 다른 경로(허용 목록)로 거부돼 실행은 안 됐다.
- 원인: `approval-gate.py:224` 는 stdout 을 utf-8 로 고정 · `supervisor._check_approval_gate` 는 locale(cp949) 로 읽음 → 디코드 실패 → stdout 비어 `blocked=False`. 실측: 기본 실행·`PYTHONIOENCODING=utf-8` = 통과(위험) · `PYTHONUTF8=1` 만 차단. 운영 Stop 경로(`stop-six-guards.sh:64`)는 `-X utf8` 이라 정상 · 그 외 호출(planner.promote·직접 실행·스크립트 시험)이 영향.
- 수정 (최소): 같은 인코딩(utf-8)으로 읽음 · 게이트가 일치(exit 10)를 보고했는데 출력을 못 읽으면 차단 (fail-closed). 수정 후 세 환경 모두 차단 · 시험 +1 (HEAD 코드 FAIL → 수정 후 PASS).
- 같은 유형 [확인]: approval-gate 출력을 subprocess 로 읽는 곳은 이 1곳 (platform_api 는 모듈 직접 import · hook 은 bash). supervisor 의 verify 실행 3곳(`text=True`)도 디코드 실패 시 출력이 비지만 판정이 REPAIRING 쪽(놓침)이라 위험 통과는 아님 → 기록만.
- 부수 사건: 이 원인을 확인하던 명령 문자열에 위험 명령 예시가 들어가 PreToolUse 게이트가 승인 대기 `appr-4bccc37a5e51` 을 새로 만들었다 (실행 안 됨 · 승인·거부·삭제 안 함).
- 1차 fresh clone pytest 1 failed 는 이름 미확보 (로그를 tail -2 로 잘라 저장 — §36 과 같은 실수) · 같은 clone 재실행 3/3 = 180 passed · failed 0 → [원인 미확인]. 1차 clone 은 긴 파일명으로 checkout 실패 (`core.longpaths` 필요) · 두 clone 모두 scratchpad 에 남김 (삭제 안 함).

**회귀 (fresh clone e44422a · `core.longpaths` · PYTHONIOENCODING=utf-8 · 전체 로그 보존)** [확인]: verify-fresh-clone 위반 0 · phase3 26/26 · phase5 39/39 (Test 12 해소) · phase12 rc 0 · golden 13/13 · pytest 180 passed + 1 failed → 새 statusline 시험의 행 수 하한(≥8)이 상태 파일에 좌우돼 fresh clone(7행)에서 실패 → 하한을 ≥3 으로 고침 (정렬·폭·빈 줄 판정은 그대로 · clone 에서 │ 13번째 셀 동일) → test_phase20 60/60 (clone) · phase2 첫 실행 16/21 (sandbox 생성 단계 · 사유 로그 없음) → 같은 clone 재실행 2/2 = 21/21 · 직접 sandbox 생성 성공 → [원인 미확인] (디스크 여유 12GB 로 정책 하한 10GB 근처 [추정]). 33 수집 오류 기존 그대로.
**보존 [확인]**: goals 161 · tasks 156 (155 + 승인 대기 appr-4bccc37a5e51 1건 · 위 부수 사건) · Goal #77 FAILED · Ledger R1~R172 무변경 (R167~R169·R172 approval_required) · Statusline 디자인·토큰·원격 설정 변경 0 · 유료 호출·push·삭제·화면 캡처 0.
**판정 (이번 작업 후)**: A PASS · D PASS (유지) · B PARTIAL — 남은 것은 유료 Judge 실측 (승인 필요) 뿐 · C PARTIAL — 무료 종단 경로 완성 · 남은 것: 유료 Agent 실행 (승인 필요) + 문법이 다른 같은 유형 미탐 (대형 기능 필요 · 이번 범위 밖) · E BLOCKED — 문자열 검증 완료 · VS Code 실제 화면만 남음.

## 40. V1.1 B·C 실제 유료 검증 · 개발·검증·증명 원칙 전파 (2026-11-06 · 기준 b2324c9 · 유료 $0.73 · push·삭제·캡처 0)

**승인 범위**: C 실제 체인 1회로 B 통합 (Agent ≤2 + Judge 1 · 총 $5) · 이 검증용 일일 한도 $5. Push(b2324c9 까지)는 앞선 승인으로 완료 · 이번 커밋은 push 안 함.

**격리 [확인]**: `chain_e2e_driver.py` 와 같은 구조를 scratchpad 1회용 드라이버로 (저장소 미포함) — 임시 git 저장소 · 임시 orca.db · 임시 sandbox root · `dispatch_agent` 만 실제 `claude -p`. 일일 한도 $5 는 공식 setter `route.py --set-daily-limit 5` 로 **임시 DB 에만** 설정 → 운영 DB 한도는 NULL 그대로라 다른 자동 작업(self-heal 등)은 계속 유료 호출 차단. 종료 후 임시 DB 도 NULL 로 복원.

**실행 결과 [확인]** (goal 1 · chain `repair-goal-1`)
| 단계 | 결과 |
|---|---|
| reproduce | `weight_fee(10)` 실패 재현 (exit 1) |
| 수정 Agent (opus-5-5 · 1회 · $0.3711 · 25.4s) | `PER_KG_RATE = 3` 한 곳 정의 · `weight_fee`·`label_fee` 공용 (요구사항 R1~R3 · 같은 버그 복사본 label.py 까지 수정) |
| 정책 | 허용 경로 2개만 변경 · 보호 파일(시험 2·REQUIREMENTS.md) 무변경 |
| pytest · 자동 회귀 | 대상 시험 통과 · `demo/test_regress.py` 자동 선정 → exit 0 |
| Judge (opus-5-5 · 1회 · $0.3608 · 31.6s · Bash 거부됨) | R1·R2·R3 모두 met · 근거 [확인] 파일:줄 + [추정]·[미확인] 구분 표기 · confidence 8 |
| judge_absorb | VERIFIED · requirements_scope checked · external_scope none_needed · judge_source `llm_agent` (session 562b3286…) |
| 반영 | sandbox commit → `apply-target` fast-forward · main 원본 버그 그대로 |
| 예산 | 예약 fix $3.00 → 정산 $0.3711 · judge $2.00 → 정산 $0.3608 · 합계 **$0.7319** · 차단기 0 |
- 독립 재확인 (Judge 말 대신 직접 실행): apply-target 에서 pytest 2 passed · `label_fee(10)=30` · 요금 숫자는 shipping.py:1 한 곳.
- 운영 보존: 실행 전후 운영 DB 예산 NULL·예약 14·Agent 비용 기록 27·goals 161·tasks 156·Goal #77 FAILED·Ledger md5·HEAD·worktree 26 모두 동일.

**실검증에서 발견한 누락 → 보완**: Judge 가 "test_regress.py 실행 증거 없음 [미확인]" 이라고 적음 — 체인은 회귀를 실행·통과했지만 결과를 Judge 프롬프트에 넣지 않았다. → `real_repair_chain` Judge 프롬프트에 자동 회귀 실행 결과(시험·종료 코드·재시도 여부) 추가. 무료 종단 시험에 단언 추가 (HEAD 코드 FAIL → 수정 후 PASS). **유료로 다시 돌리지는 않음** (승인 1회).

**원칙 전파 (개발 경로별 실제 적용)**
| 경로 | 적용 위치 [확인] | 판정 |
|---|---|---|
| 수정 Agent | `real_repair_chain` 프롬프트 FACT_TAG_RULE·요구사항 · 정책·pytest·자동 회귀·같은 유형 후보 | PASS (실검증) |
| Judge | 프롬프트 + `check_requirement_verdicts` (근거 [확인]·변경 줄 연결) · external_scope · judge_source | PASS (실검증 · 이번 보완은 무료 시험만) |
| Codex·Gemini 자동 위임 지시서 | `auto-dispatch.make_task_instruction` 에 같은 정본 FACT_TAG_RULE + 완료 증명 7항목 (신규 연결) | PARTIAL — 지시서까지 · Codex 결과 검사는 `post-impl-verify.sh` (문법·인코딩) 뿐이고 요구사항·근거 판정 경로 없음 |
| Gemini 검증 | `gemini-a.bat` task 검증에 "실행 출력 없는 코드 읽기만 = UNVERIFIED" 기준 1줄 (신규) | PARTIAL — 프롬프트만 · 출력 기계 판정 없음 · Gemini 실행 안 함 [미확인] |
| 메인 Claude | rules (execution-contract § 5 · failure-mode 사실 표기) + Stop Ledger gate (PASS/PARTIAL/BLOCKED + 증거) | 기존 유지 |
| 공식 자료 확인 | 무인 체인은 외부 페이지를 읽지 않고 `external_scope not_checked` 면 반영 중단 (설계) · 이번 실검증은 외부 의존 없음 → 미사용 | PARTIAL (자동 검색은 없음) |
- 시험 +3 (자동 위임 지시서·Gemini 기준·Judge 회귀 전달) · HEAD 코드에서 3 FAIL → 수정 후 3 PASS.
- 회귀 (운영 폴더 · pytest 만 · 스크립트형 시험 제외) [확인]: 183 passed · failed 0 · 33 수집 오류 기존 그대로 · golden 13/13. `gemini-a.bat` 추가 줄은 cmd 단독 실행으로 출력 확인 (Gemini 호출 안 함).
- 스크립트형 시험 (fresh clone 을 b2324c9 로 맞춘 뒤 이번 변경만 적용 · 운영 DB 무관) [확인]: phase3 26/26 · phase12 62 passed · phase5 첫 실행 38/39 — Test 13 `verify_fix` 가 `python -c "import fail"` 에서 60초 시간 초과 (exit=None · 이번 변경 밖의 함수) → 같은 clone 재실행 39/39 (exit 0) → [원인 미확인] · 변경 미적용 상태로 잘못 돈 1회는 증거에서 제외.

**외부 근거 [확인 · https://code.claude.com/docs/en/cli-reference · 2026-11-06 본문]**: 사용한 `-p`·`--model`·`--output-format json`·`--setting-sources`·`--permission-mode dontAsk`·`--allowedTools`·`--max-budget-usd` 모두 문서화. 단 `--max-budget-usd` 는 "Spend can pass the cap, so leave headroom" (클라이언트 추정 · 상한 초과 가능) → 총액 상한은 실행 전 예약 게이트가 지킨다. 비용 필드 `total_cost_usd` 는 이 페이지에 없음 [미확인] (실제 출력에는 있음).

**판정**: B PASS — 실제 LLM Judge 가 요구사항별 근거를 판정·출처 `llm_agent` 기록 · 허위 VERIFIED 차단은 이번 실행에서 발생 조건 없음 (무료 시험으로만 확인). C PASS (요구 범위) — 실제 Agent 수정·자동 회귀·같은 유형 수정·Judge·반영 종단 성공 · 남은 한계: 문법이 다른 같은 유형 미탐 (§37) · 공식 문서 자동 검색 없음. E BLOCKED (VS Code 캡처 대기).

## 41. 검증 원칙 미연결 경로 마무리 (2026-11-06 · 기준 76a550b · 유료 $0 · push·삭제·캡처 0)

**지시 범위**: 유료 반복 금지 · 기존 경로에 누락 연결만 · 대규모 탐색 엔진 추가 금지.

| # | 경로 | 실제 상태 (수정 전) [확인] | 이번 연결 | 증거 |
|---|---|---|---|---|
| 1 | Judge ← 회귀 실행 증거 | 회귀는 runner 기록(verified=1)으로 근거 대조 자료에 들어감 · 단 **관련 시험이 실행 기록에 없어도 VERIFIED 가능** (`affected_tests_not_run` 은 안내문에만) | handoff 에 `affected_tests_not_run` 저장 · judge_absorb 가 비어 있지 않으면 UNVERIFIED (`regression_scope`) | 시험: 미실행 시 UNVERIFIED · 실행된 회귀 경로는 근거 인정, 실행 안 된 시험 이름은 불인정 (기존 anchor 동작 증명) |
| 2 | Codex 결과 | `codex-auto.bat` 은 `post-impl-verify.sh` (문법·인코딩) 통과 = 완료 · 시험 실행·보고 대조 없음 | `independent_verifier.codex_check` + `codex-auto.bat` 연결: 변경을 참조하는 pytest 실제 실행 · `docs/implementation-report.md` 최종 판정 대조 · 회귀 실패/보고 FAIL → 완료 처리 안 함 · PASS 주장인데 실행 출력 없음/미실행 시험 → PARTIAL 기록 (`.claude/state/codex-check/<task>.json`) · 스크립트형 시험은 운영 상태에 쓸 수 있어 자동 실행 안 하고 미실행으로 표시 | 시험: 회귀 깨짐 FAIL · 실행 출력 없는 PASS 주장 PARTIAL · 보고 없음 PARTIAL · 근거 갖춘 PASS = PASS |
| 3 | Gemini 판정 | `gemini-auto.bat` 이 `review-result.txt` 에 `PASS`·`OK`·`passed` 글자가 하나라도 있으면 통과 (`findstr`) — **FAIL 줄이 있어도 통과 · `TOKEN`·`LOOK` 같은 단어로도 통과** (거짓 PASS 경로) | `review_verdict` (줄 단위: FAIL/BLOCK 줄 → FAIL · 실행 출력 `exit N`/`N passed` 없는 PASS → UNVERIFIED) 로 교체 · `gemini-a.bat` 은 PASS 줄에 명령·결과를 같이 쓰도록 | 시험 (Mock 보고서 5종 + CLI 종료 코드) · `gemini-a.bat` 추가 줄 cmd 단독 실행 확인 · **Gemini 실제 호출 안 함** |
| 4 | 외부 근거 기록 | URL·버전·날짜·read/found 구분은 있음 · `read` 에 본문 실물 없음 | `read` 는 본문 인용 20자+ 필수 (note) | 시험: 인용 없는 read 거부 |
| 5 | 검색 실패 | 실패를 기록할 수단 없음 (미확인과 구분 불가) | level `failed` (사유 필수) → `external_scope = blocked` · VERIFIED 금지 | 시험: failed → blocked · UNVERIFIED |
| 6 | 같은 유형 탐색 언어 간 한계 | 글자 그대로 비교 → 문법·언어가 다른 복사본 미탐 | **변경 없음** · 한계 기록 (§37) | — |
| 7 | phase5 60초 시간 초과 | 아래 | 설정 변경 없음 · 실패 기록 유지 | — |

- 문서 동기: `/verify` (plugins 원본 → sync) 와 `execution-contract.md § 5` 의 external-evidence 사용법을 read 인용·failed 로 갱신.
- 역검증: 새 시험 4개는 수정 전 코드에서 FAIL → 수정 후 PASS · 기존 anchor 동작 증명 시험 1개는 수정 전에도 PASS (의도).
- 회귀 (운영 폴더 · pytest 만) [확인]: 188 passed · failed 0 · 33 수집 오류 기존 그대로 · golden 13/13. fresh clone 결과는 아래.
- 공식 근거 [확인 · 2026-11-06 본문]: Claude Code CLI `--allowedTools` = "Tools that execute without prompting … To restrict which tools are available, use `--tools` instead" (https://code.claude.com/docs/en/cli-reference) — 실검증 Judge 의 "Bash 거부" 는 `--permission-mode dontAsk` + 허용 목록 밖 도구 거부와 일치. Python `subprocess.run` 타임아웃 동작은 오늘 본문을 다시 읽지 않음 — execution-contract § 5 의 기존 기록 ("`subprocess.run` 타임아웃은 자식을 종료") 과 `verify_fix` 코드(`except subprocess.TimeoutExpired` → `exit=None`)로 판단 [기존 기록 · 오늘 미재확인].

**phase5 60초 시간 초과 조사 [확인한 것 / 미확인]**
- 실패: Test 13 `verify_fix(sb, 'python -X utf8 -c "import fail"')` → `TimeoutExpired` (60초 고정 · 재시도 없음 · `real_repair_chain.verify_fix`/`reproduce_failure` 기본값) · 로그 종료 15:18:48 · 같은 clone 재실행 15:21 → 39/39 · exit 0.
- 확인: 그 시각 겹친 내 작업 없음 (운영 폴더 전체 pytest 는 그 전에 끝남) · 같은 PC 다른 Claude 세션 1개는 idle · 재실행 시 여유 메모리 6.9GB · 디스크 사용 95% · 시험 sandbox 는 `%TEMP%\orca-repair-sandbox-test\<clone 폴더명>` 공유하지만 시험별 시각 ID 라 충돌 근거 없음 · 증거 파일(`P7-RRC-test-*_evidence.json`)은 남아 있지 않음.
- **원인 미확인**. 짧은 import 가 60초를 넘긴 이유(백신 검사·디스크 지연 등)는 근거 없이 단정하지 않음 [추정 금지].

**발견 기록 (범위 밖 · 수정 안 함)**: `codex-auto.bat` 은 작업 완료 뒤 `git add . && commit && push` 를 자동 실행한다 (승인 게이트·push 정책과 별개 경로) — 운영 정책 판단 필요.

**fresh clone 39b0574 (`core.longpaths` · 시험별 전체 로그 보존)** [확인] — 정정: `docs/screens` 제외 sparse 를 의도했으나 Git Bash 경로 변환이 `!/docs/screens/` 를 `!C:/Program Files/Git/docs/screens/` 로 바꿔 **제외가 적용되지 않은 전체 checkout** (clone 자체 2.44GB) · 디스크 11.4GB → 8.41GB 감소의 상당 부분이 이 clone (§42).
- 1차: verify-fresh-clone 위반 0 · phase3 26/26 · phase12 스크립트 통과 · golden 13/13 · pytest 185 passed + 3 failed (phase12 sandbox 3건) · phase2 16/21 · phase5 38/39 — 실패 5묶음 모두 사유 "디스크 부족: 여유 8.41GB < 최소 10.0GB · 생성 대기" (sandbox 생성 하한) · 디스크 여유가 11.4GB → 8.41GB 로 줄어 하한 아래.
- 2차 (같은 clone · 시험 환경 변수 `REPAIR_SANDBOX_MIN_FREE_GB=1` 만 변경): phase12 pytest 16/16 · phase2 21/21 · phase5 39/39 → **코드 결함 아님 · 디스크 용량 문제**.
- 오전 fresh clone 의 phase2 첫 실행 16/21 (사유 로그 없음) 은 같은 증상 → 디스크 하한 [추정 · 당시 사유 미기록].
- 운영 영향: 디스크 여유 8.41GB 는 운영 sandbox 하한(10GB) 아래 → 운영 self-heal 의 sandbox 생성도 대기 상태가 된다 (정책대로 차단 · 데이터 손상 없음). 임시 clone 정리(삭제 승인 필요)로 회복 가능.

## 42. 운영 안전: codex-auto 승인 우회 · 디스크 (2026-11-06 · 기준 6b40d5b · 유료 $0 · push·삭제·캡처 0)

**P0 — codex-auto 원격 push 승인 우회 [확인]**
- 실제 경로: `codex-auto.bat` 작업 완료 후 `git add .` → `commit` → `push` (승인 게이트 밖). `add .` 는 작업 전부터 있던 미커밋 파일까지 담는다.
- 같은 유형 전수: 자동 push 실행 = codex-auto 1곳 · `external-trends-sync.sh` 는 지정 파일만 기능 브랜치로 push (승인 정책 표 "feature branch push = 자동" 범위 · 단 운영 저장소에서 `git checkout -b` 로 브랜치를 바꾸는 점은 기록만) · `post-codex-verify.sh` 의 `git add -A`·commit 은 호출처 0 (휴면 · push 없음). 나머지 매치는 감지 규칙·hook 문자열.
- 수정 (신규 1: `lib/worker_git.py` · 기존 게이트 `approval-gate.request_approval/approve/status` 재사용):
  1. Codex 실행 직전 미커밋 경로·내용 해시 기록 (`.claude/state/worker-git/<task>.before.json`)
  2. 완료 후 실행 중 새로 바뀐 경로만 커밋 (`git commit -- <paths>` · 다른 staged 내용 안 섞임) · 원래 미커밋이던 경로는 워커가 또 고쳤어도 제외·보고 · 민감 파일명(.env·키) 제외 · 실행 전 기록 없으면 커밋 안 함
  3. push 는 실행하지 않고 `push-<task>` 승인 대기 등록 (커밋 sha·remote·branch 기록)
  4. 워커 루프가 승인된 건만 push — 등록 커밋이 HEAD 조상이고 원격 브랜치가 그 커밋의 조상일 때만 (강제 없음) · 끝나면 executed/failed 기록
- 시험 (임시 bare 원격 · 임시 DB · 실제 원격 push 0): 사용자 미커밋 파일·.env 제외 · 승인 전 원격 무변경 · 승인 후 push 정상 · 원격이 그사이 바뀌면 거부 · 실행 전 기록 없으면 커밋 안 함 · 워커 파일에 직접 push 줄 0.
- 남은 것: 실제 Codex 워커 실행으로 이 경로를 돈 기록 없음 [미확인].

**검증 원칙 전파 보완 — 외부 근거와 코드 관련성**
- 본문 인용 20자 검사는 빈 기록 차단일 뿐 공식 문서 출처·이번 코드와의 관련성 증명이 아님 [확인 · 지적 수용].
- 자동 체인 Judge 프롬프트에 외부 패키지별 공식 자료 기록(URL·버전·날짜·인용, 없으면 "no official-source record") 을 넣고, 인용이 이 diff 의 사용 방식을 뒷받침하는지 비교해 아니면 누락으로 적도록 연결. 무료 종단 시험: 기록 없음 → "no official-source record" 전달 · 기록 후 → URL·인용 전달 · external_scope checked. **실제 Judge 가 관련성을 올바르게 판단하는지는 유료 실행 없이 [미확인]**.

**경로별 실제 적용 (구현 완료 ≠ 실제 실행 검증)**
| 경로 | 구현·연결 | 실제 실행 검증 |
|---|---|---|
| 자동 수정 Agent·Judge (Claude) | 요구사항·정책·pytest·자동 회귀·같은 유형·회귀 결과 전달·외부 근거 기록 전달·회귀 미실행 차단 | 유료 실검증 1회 (§40) · 이후 보완분은 무료 시험만 |
| Codex | 지시서 7항목 · codex-check (관련 pytest·보고 판정) · 소유 파일만 커밋 · push 승인 대기 | 실제 Codex 실행 0 [미확인] |
| Gemini | 줄 단위 판정 (FAIL 줄·실행 출력 없는 PASS 거부) · 프롬프트 기준 | 실제 Gemini 실행 0 [미확인] |
| 메인 Claude | rules + Stop Ledger gate (판정 + 증거) | 기존 운영 경로 |

**P1 — 디스크 [확인]**
- 현재 여유 8.42GB · 운영 sandbox 하한 `min_free_gb` 10 (정책 파일 · 완화 안 함) → 운영 self-heal sandbox 생성 대기 상태.
- 원인 일부: 이번 fresh clone `fresh5_39b0574` 가 sparse 미적용 전체 checkout (자체 2.44GB · §41 정정).
- 삭제 후보 (모두 이 세션이 scratchpad 에 만든 것 · 사용 프로세스 0 · 운영 저장소 worktree 연결 0 · 하드링크 계산):
  | 대상 | 겉보기 | 지우면 실제 회수 |
  |---|---|---|
  | fresh_ed60f24 · fresh2_ed60f24 · fresh3_e44422a · fresh5_39b0574 | 각 6.96GB | 각 2.44GB (git 객체 4.52GB 는 원본 저장소와 하드링크 공유 → 회수 안 됨) |
  | c_e2e_run1~3 · c_paid_run1 · fresh5_sbx | 수 MB | ~0 |
  | 합계 | — | **9.77GB** → 여유 약 18.2GB (하한 10GB 회복) |
- 삭제 안 함 (승인 필요). 정리 절차: 각 폴더 사용 프로세스 0 재확인 → 폴더 단위 삭제 → 여유 공간 재측정 → 운영 저장소 `git worktree list`·`git fsck` 로 원본 객체 무손상 확인. `%TEMP%\orca-repair-sandbox-test\` 의 11-03·11-05 폴더는 이 세션 소유가 아니라 후보에서 제외.
- 디스크 차단 시험 분리: 운영 폴더 pytest 의 phase12 3건 (sandbox 생성) = 여유 8.42GB < 10GB 로 **BLOCKED (디스크)** · 하한을 낮춘 시험(§41 2차)은 로직 확인용으로만 별도 기록 · 운영 환경 통과로 세지 않음.

**회귀 (운영 폴더 · pytest 만 · 운영 디스크 하한 그대로)** [확인]: 187 passed · 3 failed = phase12 sandbox 생성 3건 (사유 "여유 8.42GB < 최소 10.0GB" · **BLOCKED 디스크**) · 33 수집 오류 기존 그대로 (스크립트형 시험 파일이 pytest 수집 시 fixture 없음) · golden 13/13. 새 시험 2 (worker 커밋·push 승인) 통과 · 종단 시험 외부 근거 시나리오 통과.

**fresh clone eb207af (sparse 실제 적용 확인: `/* !/docs/screens/` · checkout 후 `docs/screens` 없음 · clone 으로 디스크 0.05GB 감소)** [확인]
| 구분 | 결과 |
|---|---|
| 운영 디스크 하한 그대로 | verify-fresh-clone 위반 0 · phase3 26/26 · phase12 스크립트 통과 · golden 13/13 · pytest 187 passed · **BLOCKED (디스크 8.37GB < 10GB)**: pytest phase12 sandbox 3건 · phase2 (sandbox 0) · phase5 sandbox 생성 · 33 수집 오류 기존 그대로 |
| 하한만 낮춘 로직 확인 (운영 통과로 세지 않음) | phase12 pytest 16/16 · phase2 21/21 · phase5 39/39 |

**임시 clone 정리 (사용자 승인 · 2026-11-06)** [확인]
- 사전 점검: 4개 모두 scratchpad 바로 아래 · origin = 운영 저장소 · 사용 프로세스 0 (자기 검사 프로세스 제외) · 열린 핸들 없음 (이름 바꿨다 되돌리기 성공) · 운영 저장소 worktree·alternates 연결 없음.
- 삭제: fresh_ed60f24 · fresh2_ed60f24 · fresh3_e44422a · fresh5_39b0574 만 (경로·origin 재확인 후 삭제하는 스크립트) · 시험 로그 폴더와 fresh6_clone 은 유지.
- 결과: 디스크 여유 8.36GB → 18.23GB (+9.87GB · 계산 9.77GB) · 운영 저장소 `git fsck --connectivity-only` 오류 0 · worktree 26 그대로 · HEAD 79b8338 · 로컬 커밋 5 보존.
- 게이트: 하한 `min_free_gb` 10 그대로 (환경 변수 덮어쓰기 없음) · 메모리 게이트 정상 · 디스크로 막혔던 phase12 pytest 운영 하한 그대로 16/16 통과 → 운영 sandbox 생성 가능 상태 복구.

## 43. V1.1 최종 검증 준비 (2026-11-06 · 기준 c4736ec · 읽기 전용 · 실행·push·유료 0)

**로컬 커밋 6개 [확인]**: 76a550b · 39b0574 · 6b40d5b · eb207af · 79b8338 · c4736ec · 14 파일 +685 −25 · 원격 origin/main = b2324c9 (fetch 후) · 원격에만 있는 커밋 0 · 추가 685줄 비밀정보·개인 경로 패턴 0 (자체 패턴 검사 · gitleaks 미설치 · push 시 kit 시크릿 hook 재검사).

**Codex·Gemini 실행 조건 [확인 · 비밀값 미출력]**
| CLI | 버전·모델 | 인증 | kit 실행 방식 | 공식 문서 [2026-11-06 본문] |
|---|---|---|---|---|
| Codex | 0.130.0 · gpt-5.3-codex · reasoning medium | ChatGPT 로그인 (API 키 없음) | `codex-a --auto` = `--dangerously-bypass-approvals-and-sandbox` (sandbox 없음 · 운영 폴더) | ChatGPT 플랜 사용 한도 적용 · "API token prices are separate from subscription usage" (learn.chatgpt.com/docs/pricing) · `codex exec` 기본 read-only sandbox · `--full-auto` 는 문서상 미지원 → 설치 버전은 아직 수용 (도움말 정상) |
| Gemini | 0.39.1 | 개인 Google OAuth (API 키 없음) | `gemini --yolo` (도구 자동 승인 · 문서상 deprecated → `--approval-mode=yolo`) | 개인 로그인 1000 요청/일 · 단 "Unpaid tier … replaced by Antigravity CLI on June 18th, 2026" (geminicli.com/docs/resources/quota-and-pricing) → 개인 무료 계정으로 실제 동작 여부 [미확인] |
- 위험 기록: kit Codex 워커는 sandbox 없이 운영 폴더에서 실행 → 실검증은 워커 대신 임시 저장소 + `-s workspace-write` 로.

**최소 실검증 시나리오 (승인 대기 · 미실행)**
| 작업 | 시나리오 | 호출 | 비용 상한 | PASS 조건 |
|---|---|---|---|---|
| Codex 실제 경로 | 임시 git 저장소(버그·시험·요구사항) · `codex exec -s workspace-write` 1회 → worker_git (임시 bare 원격) → codex_check | Codex 1회 | API $0 · ChatGPT 플랜 사용량 소모 | 허용 파일만 변경 · 관련 pytest 실제 실행 결과와 보고 판정 일치 (PASS 또는 근거 부족 시 PARTIAL 로 정확히) · 소유 파일만 커밋 · push 는 승인 대기 · 원격 무변경 |
| Gemini 실제 경로 | 임시 폴더 · gemini-a 검증 프롬프트 1회 → review_verdict | Gemini 1회 | $0 (개인 OAuth 무료 한도) | 실제 보고서를 review_verdict 가 수동 판독과 같게 분류 (실행 출력 없는 PASS → UNVERIFIED) · 인증 실패 시 BLOCKED (Antigravity 이전) |
| Judge 최신 증거 | 수정은 고정 편집(가짜) · Judge 만 실제 `claude -p opus-5-5` 1회 · 외부 패키지 공식 자료 기록 + 자동 회귀 포함 · 일일 한도는 임시 DB 에만 | Judge 1회 | 호출당 $2 (정책 기본) · 예상 약 $0.36 (과거 15회 평균 0.34·최대 0.36) | judge_source llm_agent · Judge 가 회귀 실행 결과를 근거로 인정 ([미확인] 아님) · 외부 자료 인용과 diff 사용 관련성 언급 · 최종 판정이 근거와 일치 |
| Push | 일반 push 6커밋 | — | — | push 직전 원격 b2324c9 재확인 · 강제 없음 |
| E Statusline | 사용자 VS Code 캡처 | — | — | 캡처에서 왼쪽 │ 정렬·빈 줄·폭 확인 (FROZEN 디자인 · 문자열 시험 유지) |

## 44. 실행 경로 안전성 — Codex sandbox · Gemini 지원 상태 (2026-11-06 · 기준 94913ee · 유료 0 · Codex·Gemini 실제 호출 0)

**Codex 실행 경로 [확인]**
- 실제 Codex 호출 지점: `codex-a.bat` 3곳 (analyze · full-auto · auto) — `codex-auto`·`codex-auto-global` 워커 모두 `call codex-a --auto` 경유 · 종전 auto·analyze = sandbox·승인 우회 옵션 (운영 폴더에서 sandbox 없이 실행).
- 설치 버전 확인 (도움말 파싱 · 모델 호출 0): Codex 0.130.0 `-s workspace-write` 수용 · 잘못된 값은 오류 (`read-only | workspace-write | danger-full-access`) · `-a on-request|never` 수용 · Windows sandbox(restricted token) 하위 명령 존재 · 이 PC 는 sandbox 최초 설정 완료 상태 (`CodexSandboxOffline/Online` 계정 · 오늘 사용 기록).
- 수정: `codex-a.bat` 3곳 → `codex exec --sandbox workspace-write` (작업 폴더 안 쓰기만 · 네트워크·폴더 밖 쓰기 차단) · 문서상 미지원인 `--full-auto` 제거.
- 같은 유형: `codex.bat` (사람용 대화형 진입점) 은 설치 Codex 에 없는 `--dangerously-skip-permissions`·`--approval-mode` 로 **모든 실행이 즉시 실패**하던 상태 → `--sandbox workspace-write --ask-for-approval on-request` · 플러그인 implementer 에이전트 문서 9개(내용 동일)와 레거시 `skill-02-implement.md` 의 우회 옵션 안내 → workspace-write 로 · 남은 우회 옵션 0.
- 시험 (Mock: 인자만 기록하는 가짜 codex.cmd 를 PATH 앞에 두고 배치 실제 실행): codex-a 3모드 모두 `exec --sandbox workspace-write` · codex.bat 대화형 `--sandbox workspace-write --ask-for-approval on-request` · 우회 옵션 0 · 설치 Codex 옵션 수용 확인 · HEAD 원본에서는 FAIL.
- 실제 sandbox 차단 동작 (폴더 밖 쓰기·네트워크) 은 **[미확인]** — `codex sandbox windows` 단독 시험은 Codex 전역 설정에 권한 표 추가가 필요해 중단 (전역 설정 변경 금지) · 실제 `codex exec` 1회로만 확인 가능 (승인 필요).
- 기존 동작 발견 (수정 안 함 · HEAD 원본도 동일 재현): ① `codex-a.bat` 은 `codex`(Volta `codex.CMD`) 를 `call` 없이 실행 → Codex 가 끝나면 배치도 끝나 그 뒤 완료 처리·재시도·UTF-8 변환이 실행되지 않음 (`call` 을 붙이면 지금까지 안 돌던 "전체 .js·.vue 인코딩 재저장" 이 처음 돌게 되어 정상 흐름이 바뀌므로 보류) ② `codex.bat --auto/--analyze` 는 머리글 뒤 바로 끝남 (모드 값에 공백이 붙는 기존 문제 [추정]).
- 남은 위험: workspace-write 도 작업 폴더(운영 저장소) 안에서는 자유롭게 쓴다 → 작업 전 사용자 미커밋 파일 보호는 커밋 단계(worker_git)까지만 · 완전 격리는 worktree 실행이 필요 (미구축).

**Gemini 지원 상태 [확인 · 실행 0 · 재로그인 0]**
- 활성 계정 도메인 = gmail.com (개인 계정 · 토큰 미열람) · CLI 0.39.1 · 인증 oauth-personal.
- 공식 (github.com/google-gemini/gemini-cli README · 2026-11-06 본문): "Free individual access and Google AI Pro / Ultra (Google One) moved to Antigravity CLI on June 18, 2026" · Gemini CLI 는 "Gemini Code Assist Standard / Enterprise … (plus legacy paid API / Vertex keys)".
- 판정: 현재 계정으로 Gemini CLI 경로 = **BLOCKED (서비스 지원 종료)** · 코드 결함 아님 · kit 의 review_verdict·프롬프트 연결은 Mock 시험 통과 상태 그대로.
- Antigravity CLI 비교 (antigravity.google/docs · 2026-11-06): 실행 파일 `agy` (미설치) · `agy -p "prompt"` 비대화형 · 자동 승인 `--yolo` 없음 → `--mode=auto` (terminal sandbox 필요 · Windows v1.4.4+ · business/enterprise 계정 불가 · headless 에서 불가하면 default 로 계속) · 표준입력 파이프 문서 [미확인] · 설정 `~/.gemini/antigravity-cli/settings.json` · GEMINI.md·AGENTS.md·`~/.gemini/GEMINI.md` 는 계속 읽음.
- kit 영향 범위: Gemini CLI 실제 호출 = `gemini.bat` 4 · `gemini-a.bat` 4 (3곳 표준입력 파이프) · `design.bat` 4 · 워커 토큰 확인 2 (`gemini-auto`·`gemini-auto-global`) · 설치 `setup/modules/06-prereqs.bat` · 점검 `init.bat`·`init.sh` · 전환하려면 설치(원격 스크립트 실행 = 승인 게이트 대상)·인증·호출 12곳+ 옵션 변경 필요 → **사용자 승인 전 전환 안 함**.

**Judge 최신 증거**: 회귀 실행 결과·외부 공식 자료 기록이 Judge 입력에 들어가는 것은 무료 종단 시험으로 유지 확인 · 실제 Judge 가 그 증거를 올바르게 쓰는지만 실제 호출 1회 필요 (예상 ~$0.36 · 상한 $2 · 승인 대기).

**회귀 (운영 폴더 · pytest 만 · 운영 디스크 하한 그대로 · 여유 18.23GB)** [확인]: 191 passed · failed 0 (phase12 sandbox 3건 디스크 회복으로 통과) · 33 수집 오류 기존 그대로 · golden 13/13 · 새 Mock 시험 1 (HEAD 원본 FAIL → 수정 후 PASS).

**fresh clone 5cae661 (sparse 적용 · 디스크 여유 18GB)** [확인]: verify-fresh-clone 위반 0 · pytest 191 passed (33 수집 오류 기존 그대로) · phase3 26/26 · phase5 39/39 · phase12 통과 · golden 13/13 · **phase2 첫 실행 16/21** (Test 04 `execute_goal executed=0 · sandbox_count=0` · 사유 로그 없음).
- phase2 조사: 같은 clone 에서 운영 하한 그대로 sandbox 직접 생성 = 정상 · phase2 재실행 2회 = 21/21 · 재현 시도 ① 새 DB → pytest → phase2 = 21/21 ② 시험 sandbox 폴더가 없는 상태 = 21/21 → **디스크 원인 아님 · 원인 미확인 (fresh clone 첫 실행에서만 4/5회 발생 · 재현 실패)**. "이미 존재" 메시지는 통과 실행에도 나오는 의도된 시험 메시지라 근거 아님.
- **정정 (§41·§42)**: fresh clone phase2 16/21 을 디스크 하한 탓으로 묶은 것은 근거 부족 — phase5·phase12 는 로그에 "디스크 부족" 사유가 있었지만 phase2 로그엔 사유가 없었고, "하한 낮춘 재실행 통과" 는 두 번째 실행이라 통과했을 수 있음. phase2 는 첫 실행 한정 [원인 미확인] 으로 정정.
- 재현 시험 중 시험 sandbox 폴더 `%TEMP%\orca-repair-sandbox-test\fresh7_clone` 를 `…__moved` 로 옮겨 둠 (이 세션 clone 전용 시험 폴더 · 삭제 안 함).

## 45. Codex 운영 경로 — 후처리 복구 · worktree 격리 (2026-11-06 · 기준 1d2d9da · 유료 0 · Codex 실제 실행 0)

**후처리 결함 [확인]**: `codex`·`gemini` 는 Volta 의 `.cmd` (`where codex` → `codex.cmd`) · cmd.exe 는 배치에서 다른 배치를 `call` 없이 실행하면 돌아오지 않는다 (사용자 제공 근거: Microsoft Learn `call` · 실측: 가짜 codex.cmd 로 HEAD 원본 재현 — 완료 처리·재시도 미실행).
- 수정: 후처리가 있는 실행 줄에 `call` — `codex-a.bat` 3 · `codex-auto`·`codex-auto-global` 토큰 확인 2 · `gemini-auto`·`gemini-auto-global` 토큰 확인 2 · `gemini.bat` 3 · `design.bat` 3 (대화형 실행 줄은 바로 뒤가 종료라 변경 없음).
- `call` 로 처음 실행되게 될 "전체 .js/.vue/.ts 인코딩 재저장" 은 기본 꺼짐 (`CODEX_A_UTF8_CONVERT=1` 일 때만) · 재시도 대기 300초는 시험용 `CODEX_A_RETRY_DELAY` 로만 덮어씀.
- 시험 (Mock · 모델 호출 0): 정상 → 완료 처리 · 인코딩 재저장 안 함 · 켜면 실행 / 실패(1)·시간 초과 종료 코드(124) → 3회 재시도 후 오류 보고 (호출 4회) · HEAD 원본 FAIL.
- 한계: codex-a 자체에는 실행 시간 제한이 없다 (시간 초과는 Codex 가 비정상 종료 코드를 낼 때만 재시도 경로) [기록].

**worktree 격리 [확인]**: codex-auto 가 Codex 실행 전 기존 `repair_sandbox.create` (디스크·메모리 게이트 · `.repair-sandbox` git worktree · `docs/screens` 제외) 로 `repair/codex-<task>` 작업 폴더를 만들고 그 안에서 `codex-a` 실행 → post-impl-verify · codex-check(`--cwd`) · 소유 파일 커밋 모두 그 폴더에서.
- sandbox 를 못 만들면 운영 폴더에서 실행하지 않고 작업 실패 처리 (`[ISOLATION]`).
- 결과는 `repair/codex-<task>` 브랜치에만 · 원격 추적 없음 → push 요청 생성 안 함 · main 반영은 기존 승인 경로(`repair_sandbox apply`) · 자동 병합·push 없음.
- 운영 작업 폴더의 사용자 미커밋 파일·운영 DB·Ledger·Evidence 는 Codex 쓰기 범위(worktree) 밖.
- 시험: 임시 저장소에서 sandbox 명령 → 실제 worktree (`repair/codex-t1`) 생성 · worktree 쓰기가 원본 작업 폴더에 안 보임 · 디스크 게이트에 걸리면 경로 없음(exit 1) · 워커 순서 (sandbox → 실패 시 goto LOOP → pushd → codex-a) · HEAD 원본 FAIL.
- **운영 경로 연결 여부 구분**: 배치 코드 연결 = 완료 · 실제 codex-auto 워커 루프 실행 = 0 [미확인] (워커는 보이는 창으로 자식 프로세스를 띄워 시험 환경에서 실행 안 함 · 실제 Codex 호출 필요).

**sandbox 실제 차단 [미확인]**: Codex 0.130.0 `-s workspace-write` 수용 확인 · 폴더 밖 쓰기·네트워크 차단은 실제 `codex exec` 로만 확인 가능 (가짜 CLI 시험은 차단 증거가 아님) · 네트워크는 `~/.codex/config.toml` 에 `sandbox_workspace_write.network_access` 설정 없음 → 기본값에 따름 (기본값 문서 본문 미확인).

**회귀 (운영 폴더 · pytest 만)** [확인]: 193 passed · failed 0 · 33 수집 오류 기존 그대로 · golden 13/13 · 새 시험 2 (후처리·격리) HEAD 원본 FAIL → 수정 후 PASS.

**fresh clone 6a57cf9 (sparse · 운영 디스크 하한 그대로)** [확인]: verify-fresh-clone 위반 0 · pytest 193 passed (33 수집 오류 기존 그대로) · phase2 21/21 (이번엔 첫 실행 통과 · 이전 첫 실행 실패 원인은 계속 미확인) · phase3 26/26 · phase5 39/39 · phase12 통과 · golden 13/13.

## 46. Codex 실제 실행 검증 준비 — 워커 리허설 (2026-11-06 · 기준 bc81fd6 · 유료 0 · 실제 Codex 실행 0)

**리허설 방법**: fresh clone(`fresh8_clone`) 을 작업 위치로 · 진짜 codex 대신 인자만 기록하고 작업 폴더에 파일 1개·보고서만 쓰는 가짜 codex · 실제 `codex-auto --child 1` 워커 루프를 창 없이 1회 · 정지 파일로 종료 (스크립트 `worker_rehearsal.py` · `--real` 은 승인 후 실제 실행용).

**리허설이 찾아낸 결함 (모두 수정) [확인]**
| # | 결함 | 원인 | 수정 |
|---|---|---|---|
| 1 | 워커가 **예전 sandbox 우회 옵션**으로 Codex 호출 | 워커가 `call codex-a` 를 PATH 이름으로 찾아 `%APPDATA%\npm\codex-a.bat` (setup `04-commands` 가 복사한 예전 사본 · 우회 옵션 2곳) 실행 — §44·45 의 kit 수정이 운영 워커에 적용 안 될 수 있었음 (**§45 "운영 경로 연결 완료" 정정**) | 형제 스크립트 호출 13곳을 같은 폴더 경로로 |
| 2 | 1 의 첫 수정(`%~dp0`)이 동작 안 함 (`codex-a.bat is not recognized`) | 인자 처리 `shift` 가 `%0` 을 밀어 `%~dp0` 가 현재 폴더(worktree) 로 바뀜 | 첫 `shift` 전에 `SELF_DIR` 저장 후 사용 (5개 파일) |
| 3 | 처리 끝난 작업을 계속 다시 선택 → 시도마다 새 sandbox · Codex 반복 호출 (리허설 20회) | worktree 격리 후 sandbox 안 Codex 는 작업 파일(운영 `.claude/tasks`)을 옮길 수 없음 | 워커가 처리 끝난 작업 파일을 `done` 으로 · sandbox 이름에 시각 (재시도 충돌 방지) |
| 4 | 정상 작업이 "문법 오류" 로 실패 | `post-impl-verify.sh` 가 `py_compile`(.pyc 쓰기) 사용 → 경로가 길면 쓰기 실패를 문법 오류로 오판 (검사 대상도 작업과 무관한 `HEAD~1` 변경) | 내장 `compile()` 로 문법만 검사 (plugins 원본·.claude 사본 동일) · 대상 범위(HEAD~1)는 기존 그대로 [기록] |
| 5 | sandbox 생성 실패 시 대기 없이 즉시 재선택 (리허설 11회 연속) · 사유 미기록 | 실패 분기 대기 없음 | 사유를 `worker-git/<task>.sandbox-err.json` 에 저장 · 30초 대기 후 재시도 |
| 6 | 바뀐 파일이 없어도 "Git commit 완료" 출력 | worker_git 이 변경 없음도 0 반환 | 종료 코드 3 = 변경 없음 · 문구 분리 |
- 5 의 실패 사유 실측: "커밋 메모리 부족 23.22/25.69GB (90.4%) > 90%" — 기존 메모리 게이트가 정상 차단 (운영 폴더 실행 0) · 이 PC 의 현재 메모리 사용률이 게이트 근처.

**리허설 최종 결과 (가짜 codex · 수정 반영) [확인]**
| 확인 항목 (지시 1~8) | 정상 경로 | 실패 경로 (codex 종료 코드 1) |
|---|---|---|
| ① 기존 repair_sandbox 로 독립 worktree | 생성 | 생성 |
| ② 지정 작업 폴더 안에서 실행 | Codex 호출 cwd = worktree · `exec --sandbox workspace-write` | 동일 |
| ③ 폴더 밖 쓰기 실제 차단 | **[미확인]** (가짜 codex 는 증거 아님 · 실제 실행 필요) | — |
| ④ 네트워크 제한 | **[미확인]** (실제 실행 필요 · 설정 파일에 별도 지정 없음) | — |
| ⑤ Codex 종료 후 배치 복귀·완료 처리 | `[DONE] Codex-A complete` · 검증 통과 | 3회 재시도 후 `[ERROR] … Exit code: 1` |
| ⑥ 실패 시 오류 보고·운영 main 영향 없음 | — | commit 없음 · 작업 `done` 이동 · clone main 에 결과 없음 |
| ⑦ 테스트·변경 파일 Evidence | codex-check PASS · 변경 2파일 기록 | codex-check PARTIAL (보고서 없음) |
| ⑧ 승인 없는 반영·merge·push 없음 | 작업 폴더 repair 브랜치에 2파일 commit · push 요청 없음 (원격 추적 없음) · 운영 저장소 브랜치 무변경 | 동일 |
- 리허설 부산물 (삭제 안 함): `fresh8_clone` 안 worktree 약 28개 · 리허설 작업 파일 `done/*.rehearsal*`·`*.prev` · clone 로컬 git 사용자 설정(리허설 커밋용).

**실제 Codex 1회 실행 계획 (승인 대기)**: 같은 스크립트 `--real` · fresh clone 안 · 작업 = worktree 안 파일 1개 생성 + 지정 경로(작업 폴더 밖 `rehearsal 출력 폴더\outside_probe.txt`) 쓰기 1회 시도 + `curl https://example.com` 1회 시도 (우회·재시도 금지 · 결과만 기록) · 판정: 파일 생성됨·밖 쓰기 거부됨·네트워크 결과 기록·후처리 완료·commit 범위·push 없음 · 비용: API $0 · ChatGPT 플랜 사용량 1회 · **전제: 커밋 메모리 90% 미만 (지금은 게이트에 걸림)**.
- 남은 위험: `%APPDATA%\npm` 의 예전 사본(우회 옵션 포함)은 이름으로 `codex-auto` 등을 직접 실행하면 여전히 쓰인다 → setup `04-commands` 재실행으로 갱신 필요 (전역 파일 변경 · 승인 필요).

**회귀 (운영 폴더 · pytest 만)** [확인]: 193 passed · failed 0 · 33 수집 오류 기존 그대로 · golden 13/13 · 커밋 메모리 89.8% (게이트 90% 바로 아래).

## 47. Codex 최종 검증 준비 — 설치 사본·실행 전제 (2026-11-06 · 기준 ac70f50 · 읽기 전용 + 바로가기 2곳 수정 · 실제 Codex 0)

**설치 사본 비교 [확인]** (`setup/modules/04-commands.bat` 가 kit `.claude/scripts` 9개를 `%APPDATA%\npm` 으로 복사 · 줄바꿈만 CRLF 로 정리 · 그 외 변경 없음)
| 명령 | 설치본 | kit 과 동일 | 설치본 우회 옵션 | 비고 |
|---|---|---|---|---|
| codex-a | 있음 (2026-08-12) | 아니오 | **2** | 이름 호출 시 실행되는 실제 사본 |
| codex-auto | 있음 (2026-08-12) | 아니오 | 0 | 내부에서 codex-a 를 이름으로 2곳 호출 → 위 우회 사본 |
| gemini-a · gemini-auto · claude-auto | 있음 (2026-08-12) | 아니오 | 0 | gemini-auto 는 이름 호출 3곳 |
| gemini-verify | 있음 (2026-05-07) | 아니오 | 0 | 이름 호출 1곳 |
| codex-auto-global · gemini-auto-global · haiku-auto | 없음 | — | — | 04-commands 재실행 시 새로 설치 |
- 실제 호출 경로: 레지스트리 PATH(사용자·시스템)에서 `codex-a.bat` 이 있는 첫 폴더 = `%APPDATA%\npm` · kit `.claude\scripts` 는 레지스트리 PATH 에 없음 → 일반 셸·스케줄러에서 이름으로 실행하면 설치본(우회 옵션) 이 쓰인다.
- 같은 유형 추가 발견·수정: 저장소 루트 바로가기 `codex-auto.bat`·`gemini-auto.bat` 가 `call codex-a`·`call gemini-a` 를 이름으로 호출 (→ 설치본) → kit `.claude\scripts` 사본을 경로로 호출하도록 수정 · 시험 추가.
- **갱신 절차 (승인 대기 · 미실행)**: ① `%APPDATA%\npm` 의 위 6개 파일을 scratchpad 로 복사 보관 ② `setup/modules/04-commands.bat` 를 TARGET=kit 로 실행 (9개 `.bat` 복사·CRLF 정리만 · 다른 전역 파일·개인 설정 무관) ③ 9개 모두 kit 과 내용 동일 · 우회 옵션 0 · `where codex-a` 첫 결과 확인 ④ 실패 시 보관본 복원. 설치본은 같은 폴더 형제를 SELF_DIR 로 부르므로 9개를 함께 갱신해야 일관됨.

**실제 Codex 1회 실행 전제 [확인]**
- 디스크 여유 17.07GB (sandbox 하한 10GB 충족).
- 커밋 메모리 **91.3% — sandbox 메모리 게이트(90%) 초과** → 지금 실행하면 worktree 를 만들지 못하고 멈춘다 (실행 시점에 90% 미만 필요).
- 리허설 worktree: `fresh8_clone` 안 27개 · 0.93GB (sparse) · 운영 저장소 worktree 목록과 무관 · 기존 `repair_sandbox` 수명 관리(cleanup-orphans · 보존 24h)는 그 clone 에서 실행해야 정리됨 → 삭제 안 함 (승인 필요).
- 실행 계획은 §46 그대로 (fresh clone · `worker_rehearsal.py --real` · 작업 폴더 안 파일 1 · 지정 경로 밖 쓰기 1회 시도 · `curl https://example.com` 1회 · 우회·재시도 금지).

## 48. Codex 설치본 안전성 반영 — %APPDATA%\npm 9개 갱신 (2026-11-06 · 기준 231d321 · 사용자 승인 · 실제 Codex 0 · 유료 0)

**방법**: `setup/modules/04-commands.bat` 의 1·2단계(9개 복사 + 9개 CRLF 정리)와 같은 동작을 스크립트로 실행 · 3단계(kit `.claude/scripts/*.bat` 전체 CRLF 재저장)는 kit 작업 트리를 바꾸므로 제외 · 기존 6개 백업 후 설치 · 검사 실패 시 자동 복원.
- 1·2차 시도는 검사 기준이 넓어 kit 소스에도 있는 문자열에 걸려 **자동 복원됨** (복원 후 6개 모두 백업과 바이트 동일 확인). 3차에서 기준을 "Codex 우회 0 · codex 호출 줄에 우회 계열 옵션 없음 · 그 밖의 옵션은 갱신 전보다 늘지 않음" 으로 나눠 설치.

| 명령 | 갱신 전 → 후 (sha256 앞 16) | kit 과 동일 | Codex 우회 옵션 전→후 |
|---|---|---|---|
| codex-a | ab7c16d2… → dc9e1b90… | 예 | **2 → 0** |
| codex-auto | 74228b21… → 301c4c01… | 예 | 0 → 0 |
| codex-auto-global | (없음) → 65cfca3b… | 예 | — → 0 |
| gemini-a | 87cd1089… → 503d1a13… | 예 | 0 → 0 |
| gemini-auto | 2ed0e9d6… → 55a2ac25… | 예 | 0 → 0 |
| gemini-auto-global | (없음) → 8c8cf87a… | 예 | — → 0 |
| gemini-verify | b56ea4bf… → 9ce1b376… | 예 | 0 → 0 |
| claude-auto | 3ad4f1b5… → f56f98e1… | 예 | 0 → 0 |
| haiku-auto | (없음) → d76b78ee… | 예 | — → 0 |

- 남은 옵션 [확인] (kit 소스와 예전 설치본에 같은 개수 · 이번 범위 밖 · 수정 안 함): `gemini-a` 의 `gemini --yolo` 4곳 (Gemini 도구 자동 승인 · Gemini 는 개인 계정 BLOCKED) · `claude-auto` 의 `--dangerously-skip-permissions` 3곳 (프로젝트 정책 bypassPermissions) · `codex-a --full-auto` 는 codex-a 자체 모드 이름이며 실제 codex 호출 3곳은 모두 `--sandbox workspace-write` · `codex exec "echo ok"` 가용성 확인은 옵션 없음 = 기본 read-only.
- 실제 경로 [확인]: kit 밖 폴더에서 레지스트리 PATH 로 해석 → 9개 모두 `%APPDATA%\npm\*.bat` (kit 폴더 안에서는 cmd 가 현재 폴더를 먼저 찾아 kit 사본) · 어느 쪽이든 kit 과 내용 동일.
- 무료 배치 호출 시험 [확인]: 임시 폴더에서 PATH 맨 앞에 인자만 기록하는 가짜 `codex.cmd` → 이름으로 `codex-a --auto <task>` 실행 → 종료 0 · codex 가 받은 인자 `exec --sandbox workspace-write "Read the task instruction …"` (실제 모델 호출 없음).
- 백업: scratchpad `npm_backup_20261106_181714` (6개) · 복원은 같은 폴더에서 덮어쓰기.
- 보존 [확인]: 운영 DB (예산 NULL · 예약 14 · goals 161 · tasks 158 · Goal #77 FAILED · 운영 worktree 26) · kit 작업 트리 변화 없음 · 실행 중 프로세스 종료 없음 · 메모리 게이트 그대로.
- plugin check [확인]: copied 0 · drift 0 · orphan 5 (`--prune` 실행 안 함).
- 리허설 worktree [확인]: `fresh8_clone` worktree 목록 27줄 = clone 본체 1 + sandbox **26** (§47 의 "27개" 는 목록 줄 수 · 정정) · 잠금 0 · 최종 수정 17:36~17:56 · 사용 중 작업 없음 · 삭제 안 함.
- 실제 Codex 1회 실행 전제: 커밋 메모리 **92.0%** (게이트 90% 초과 · 아직 실행 불가) · 디스크 여유 18GB.

## §49 메모리 게이트 차단 원인 · R184 오탐 진단 (2026-11-07 · 무료·읽기 전용)

**메모리 측정 기준 [확인]**
- 게이트는 물리 RAM 이 아니라 커밋(가상 메모리)을 본다: `repair_sandbox.commit_memory()` = `GetPerformanceInfo` CommitTotal/CommitLimit · 차단 = 사용률 > 90% 또는 여유 < 2GB (`.claude/config/sandbox-policy.json`).
- 01:09 측정: 커밋 23.3/25.69GB = **90.7%** (성능 카운터 `PercentCommittedBytesInUse` 90 · 같은 값) · 물리 RAM 67% (여유 5.1GB) · 페이징 파일 고정 10GB (`AutomaticManagedPagefile=False` · 사용 2.2GB · 최고 3.4GB).
- 11-07 00:59 보고의 "98%" 는 성능 카운터 순간값 1회 · 10분 로그 최고치는 95.5% (11-03) · [추정] 일시 상승.
- 프로세스 private 합 19.07GB · 나머지 약 4.2GB 의 구성은 아래 「정정」 참고 (전부 커널·드라이버로 단정하지 않음).
- 이름별 상위: Code.exe 4.40GB(23개) · claude.exe 2.33GB(3개 · 본체만: 이 세션 0.94 · orchestration_v1 다른 세션 0.70 · IFRS_PJT 세션 0.69) · msedgewebview2 1.79 · msedge 1.72 · sqlservr 0.85 · node 0.66.
- 이 세션의 자식 프로세스는 statusline·MCP filesystem 등 수십 MB · 남은 테스트·워커 없음.

**정정 (11-07 09:3x 재측정 · 읽기 전용)**
- 보고에서 "Claude 세션 2개 종료 시 약 2.2GB 감소" 라고 쓴 것은 본체 값과 자식 포함 값을 섞은 표현이라 정정한다.
  - 두 세션(IFRS_PJT 0.69 · orchestration_v1 다른 세션 0.66) claude.exe 본체 합계: **1.35GB** [확인]
  - 자식 프로세스 포함 합계: **2.21GB** [확인] (IFRS_PJT 1.41 = 자식 39개 0.72 포함 · 다른 세션 0.80 = 자식 6개 0.14 포함)
  - 실제 종료 후 회수량: [미확인] — 2.21GB 는 현재 사용량이며 보장되는 회수량이 아니다.
- 기존 "나머지 약 4.2GB 는 커널·드라이버" 표현을 정정한다.
  - 시스템 커밋 23.80GB [확인] · 프로세스 private 합계 19.59GB [확인] · 차이 4.21GB [확인]
  - 커널 페이지 풀 1.32 + 비페이지 풀 0.78 = 2.10GB [확인]
  - 나머지 약 2.11GB: 원인 [미확인]
- 사용률 기준을 구분한다: 현재 커밋 사용률 **92%** [확인] · 기존 차단 게이트 **90%** (`sandbox-policy.json` · 변경 안 함) · 권장 실행 목표 **약 85%** (실행 전 여유 기준일 뿐 게이트 변경 아님).
- `claude.exe mcp list` (pid 14100 · 11-07 09:26 시작 · 자식 포함 약 0.60GB) 가 실행 중인 것을 관찰 [확인] · 소유 세션·멈춤 여부·종료 필요성 [미확인] · 종료하지 않음.

**지속 증가 여부 (`.claude/logs/orca-10min-loop.log` 반일 단위) [확인]**
- 커밋 사용량 최저: 11-02 15.4GB → 11-04 17.1 → 11-05 20.4 → 11-06 21.8 → 11-07 22.7GB.
- 같은 기간 claude 세션 1→3 · VS Code 프로세스 24→27 · 부팅 11-02 09:09 이후 재부팅 없음.
- 한도는 19.69 → 25.69GB 로 커짐 (11-03~11-05 사이 · 페이징 파일 확장 [추정]) · 그래서 사용량이 늘어도 사용률은 78~95% 사이.
- 결론: 사용량 증가는 열린 세션·창 수 증가와 시간상 겹친다 · 누수라고 단정하지 않는다 ([미확인]: 특정 프로세스의 단독 증가).

**R184 등록 원인 (`.claude/hooks/prompt/ledger_auto_register.py` 재현) [확인]**
- 메시지는 붙여 넣은 글만 있음 → `_intent_text` 가 지시 표지를 찾음 → `_IMPERATIVE_END_RE` 가 "…그대로 보존하세요." 의 `하세요.` 에 일치 → `pasted_directive` · `execute`.
- 승인 판정 `_needs_approval`: 표 칸 "P1 최신 Judge 증거 평가 유료 1회 승인 대기" 줄에 `유료` 일치 (부정 표지 없음) → `approval_required` · reasons ['유료'].
- 마지막 줄 "…유료 실행 … 승인한 것으로 취급하지 않겠습니다" 는 `않` 으로 제외됨 (정상).
- 판정: **오탐 가능성 높음** — 평가 보고 안의 권고문(`~하세요`)과 상태표의 단어가 지시·승인 요청으로 읽혔다. R167~R170 과 같은 계열.
- Ledger R184 는 변경하지 않음 (approval_required 그대로 · Stop 을 막지 않음).
- 고칠 방향 (미적용 · 별도 승인): 붙여 넣은 글에서 `~하세요` 권고는 지시 표지에서 빼고 `대상:` 줄·`지시다/승인한다` 문구만 인정 · 표 줄(탭/4칸 공백 구분)의 `유료`·`승인 대기` 는 승인 요청에서 제외.

**Codex 실행 조건 [확인]**: 게이트 90% 유지 · 실제 모델 호출·worktree 생성/삭제 안 함 · 지금 실행해도 `COMMIT LOW … 시작 보류` 로 거부된다 (로그 11-06 18:00~18:20 같은 사유).
