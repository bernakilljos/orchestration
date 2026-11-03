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
