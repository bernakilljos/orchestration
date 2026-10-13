# 리스크 기반 플랜 룰 (Risk-Based Planning)

> **근거**: 2026-10-12/13 사용자 지시 — PM 표준 의사결정 패턴
> **표준**: PMBOK Risk Management · ISO 31000 · Agile Risk Management

## 절대 룰

**모든 의사결정·플랜 제시 시 A(보수·순차) vs B(공격·병행) 2개 안 필수.** B 선택 시 **리스크 등급 + 증명 근거** 명시.

## 핵심 포맷

```text
## 플랜 A — 안전 (사용자 확인 후)
- 단계 1: [설정]
- 단계 2: [테스트 · smoke test]
- 단계 3: [적용]
일정: X분
리스크 등급: 0 (기준: 공식 문서 / 검증 완료 / 이전 성공 사례)

## 플랜 B — 병행 (리스크 증명 완료 시)
- 단계 1: [설정 + 테스트 동시]
- 단계 2: [적용]
일정: Y분
리스크 등급: N (낮음·중간·높음)
근거: [공식 문서 URL / 코드 분석 / 테스트 통과 증거]
롤백 계획: [역조작 X분 · 비용 0]

👉 사용자 선택: A 또는 B
```

## 리스크 등급 정의

| 등급 | 설명 | 근거 유형 | B 제시 가능 |
|---|---|---|---|
| **0** | 증명완료 · 100% 안전 | 공식 문서 · 변경이력 분석 · 반복 성공 | YES (즉시) |
| **1** | 낮음 · 대체안·롤백 명확 | 코드 분석 · 비슷한 사례 · 격리됨 | YES (조건부) |
| **2** | 중간 · 영향도 제한적 | 부분 테스트 · 근처 파일 영향 가능 | YES (감시 필수) |
| **3** | 높음 · 영향도 광범 | 미검증 · 다중 시스템 | NO (A 권장) |
| **4** | 극 · 돌이킬 수 없음 | 데이터 손실·배포 장애·보안 | NO (절대) |

## 근거 작성 (필수 요소)

### 등급 0 근거
```text
공식 문서 기반:
- ag-grid v31 migration guide 섹션 2.1
- "frameworkComponents 는 v31 에서 제거되었으나 breaking change 아님"
- 우리 코드: ComponentRegistry 이미 직렬화됨 → 호환성 우려 0

결론: 등급 0 · B 안 즉시 가능
```

### 등급 1 근거
```text
코드 분석:
- git grep "frameworkComponents" → 3 파일만 참조
- 각 파일에 mock/test 환경만 (production X)
- test coverage 95%

근거: 영향 범위 좁음 · 테스트 완전 · rollback 10분

결론: 등급 1 · B 안 테스트 완료 후 가능
```

### 등급 2 근거
```text
부분 검증:
- 변경 영향도: 5 파일 (부분 영향)
- 테스트: 수동 테스트만 했음 (자동화 테스트 없음)
- 배포 대상: 3 곳 중 1 곳만 (dev)

근거: dev 환경만 → prod 배포 전 명확한 테스트 필요

결론: 등급 2 · B 안 dev 환경에서만 · 모니터링 필수
```

## 적용 영역 매트릭스

| 영역 | 기본 등급 | 증명 시 하락 |
|---|---|---|
| 라이브러리 업그레이드 | 1 | 공식 migration guide → 0 |
| 설정 변경 (hooks·settings) | 1 | dry-run·테스트 → 0 |
| DB migration | 2 | 백업·dry-run→롤백 명확 → 1 |
| 배포 (install·sync) | 1 | 체계적 단계·검증 → 0 |
| 코드 리팩 | 1 | 테스트 100% · git revert 명확 → 0 |
| 데이터 작업 | 2 | 백업 있고 검증 됨 → 1 |
| 신규 기능 | 2 | 단위 테스트·integration test → 1 |

## 자동 트리거

| 상황 | 자동 A/B |
|---|---|
| auto-planner.md Step 5 (보고) | 필수 추가 |
| `/brainstorm` 모든 응답 | A/B 선택지 제시 |
| "OK?" "되나?" 사용자 질문 | A/B 제시 후 선택 권유 |
| 2개 이상 선택지 존재 | A/B 포맷 자동 |

## 금지

1. **A만 제시** — 사용자가 2번 지시해야 B 나옴 = 지연 · 위반
2. **B 리스크 명시 X** — "그냥 될 것 같음" 모호 표기 · 위반
3. **근거 없는 등급** — 공식 문서·코드 분석·테스트 증거 없이 등급 박음 · 위반
4. **등급 3/4 에 B 제시** — A 우선 · 위반

## PM 표준 정합

### PMBOK Risk Management
- Identify Risks (A/B 모두 식별)
- Perform Qualitative Risk Analysis (등급 산정)
- Plan Risk Responses (A는 회피·미루기, B는 대응)
- Monitor and Control (B 선택 시 감시)

### ISO 31000 Risk Management
1. **Context**: A/B 양쪽 다 계획
2. **Identification**: 리스크 요소 명시 (등급)
3. **Analysis**: 근거 문서화
4. **Evaluation**: A vs B 판정 (사용자가)
5. **Treatment**: 선택된 안 실행

### Agile Risk Management
- 2개 parallel track (A/B)
- Pull-based 결정 (push 아님)
- 투명한 trade-off (일정·품질·비용)

## 사례 모음

### 사례 1: ag-grid v31 업그레이드 (등급 0)
**상황**: "ag-grid v31 로 업그레이드 할까?"

```text
## 플랜 A — 보수
1. release notes 읽기 (10분)
2. 로컬 dev 에서 npm update 후 테스트 (30분)
3. git commit (5분)
4. 다른 팀원 코드 리뷰 (2시간)
5. main 병합 (5분)
일정: 2.5시간
리스크: 0 (공식 migration guide 기반 · frameworkComponents 제거 하지만 breaking 아님)

## 플랜 B — 공격
1. npm update (5분)
2. npm test · 통과 확인 (10분)
3. git commit (5분)
4. 즉시 deploy (5분)
일정: 25분
리스크: 0
근거:
- ag-grid 공식 릴리스: "v31 frameworkComponents 제거는 breaking 아님"
- 우리 코드: ComponentRegistry 이미 모덴화 → 호환성 문제 0
- test suite 95% coverage · 모든 변경 포착
롤백: package.json revert · npm install · git push (5분)

👉 선택: B 가능 (등급 0 · 롤백 명확)
```

### 사례 2: Hook 등록 (등급 2)
**상황**: "SessionStart 새 hook 등록할까?"

```text
## 플랜 A — 보수
1. hook script 작성 (dev branch)
2. 로컬 테스트 (여러 세션 시뮬레이션) (30분)
3. 로그 검증 (10분)
4. code review (1시간)
5. main 병합
6. 다른 머신 배포 (setup/modules 업데이트)
일정: 2시간
리스크: 0

## 플랜 B — 공격
1. hook script 작성 · 로컬만 테스트 (20분)
2. 즉시 등록 (.claude/settings.json)
3. 다음 세션 모니터링
일정: 20분
리스크: 2 (높음)
근거:
- 다른 머신 배포 미포함 → dev 환경만
- 로그 모니터링 필수 (다음 10 세션)
- 문제 발생 시 설정 revert (2분)
롤백: .claude/settings.json 제거 · SessionStart hook 단계 스킵

👉 선택: A 권장 (dev 환경 2주 테스트 후 배포)
```

### 사례 3: DB migration (등급 1→0)
**상황**: "users 테이블에 status 컬럼 추가 할까?"

```text
## 플랜 A — 보수
1. 스키마 변경 스크립트 작성
2. backup 받기
3. dev DB 에서 dry-run
4. 검증 (SELECT COUNT(*) 전후)
5. staging 배포
6. production 배포 (backup 확인 후)
일정: 1시간
리스크: 0

## 플랜 B — 공격
1. 스키마 변경 (ADD COLUMN)
2. 마이그레이션 스크립트 (seed 자동)
3. 즉시 배포
일정: 10분
리스크: 1 (중간)
근거:
- ALTER TABLE 은 lock-free (MySQL 8.0+)
- backup 있음 · rollback `DROP COLUMN` (2분)
- test suite 커버 (신규 컬럼 스키마 검증)
근거 부족점: dry-run 모니터링 없음 → staging 테스트 필수

👉 선택: B 가능 (staging 에서만 먼저 · prod 다음 주)
```

## 관련

- CLAUDE.md § 7-D (의사결정·존중·고집 금지)
- `.claude/rules/d8-no-stubborn.md` (결정 존중 · A 정하면 그대로 진행)
- `plugins/exec_orch/skills/auto-planner.md` (Step 5 A/B 포맷 추가)
- `feedback_risk_based_decision.md` (memory · 사용자 패턴)

## 참고

- PMBOK 5th Edition § Chapter 11. Project Risk Management
- ISO 31000:2018 Risk management — Principles and guidelines
- Agile Risk Management Framework (Rally Software)
- Site Reliability Engineering § 34. Risk Management
