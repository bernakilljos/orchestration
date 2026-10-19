# Adaptive Learning Baseline — 2026-10-19 10:10

**원칙**: 신규 시스템 X · 측정만 · 사용자 Phase 1 결정 전 바닥선 확정

## 1. 저장량
| 테이블 | 레코드 수 |
|---|---|
| `conversations` | 1473 |
| `session_summary` | 84 |
| `problem_solutions` | 62 |
| `decisions` | 76 |
| `recurrence_rules` | 7 |
| `recurrence_events` | 42 |
| `file_audit` | 476 |

## 2. 재사용률 (problem_solutions)
- 총 solution: **62건**
- 한 번이라도 재사용 (hit_count > 0): **24건 (38.7%)**
- 평균 hit 수: 3.9 · 최대: 32
- 최근 30일 안 hit: **24건 (38.7%)**

## 3. 검증률
- 검증된 (verified=1): **16건 (25.8%)**
- reusable_score 분포: {'10': 9, '9': 2, '8': 5, '6': 8, '5': 38}

## 4. 재발 원인 저장률
- recurrence_rules: 7건 · 상세 description (20자+): **100.0%**
- recurrence_events: 42건 · 상세 detail: **0.0%**
- `root_cause` 컬럼 존재: False

## 5. 검색 적중률
- 최근 로그 1000줄 중 검색: 0건 · hit: 0건 · 적중률 **0%**

## 6. Standing Requirements
- 총 0건 · ACTIVE 0건 · verify_pattern 설정 0건

## 7. Golden Test
- 최근: 13/13 · 2026-10-19T10:08:12

## 8. Experience 분류 체계
- 현재 category 분포: {'commit': 16, 'db': 3, 'file': 1, 'general': 22, 'hook': 5, 'mcp': 10, 'skill': 4, 'ui': 1}
- 사용자 제안 분류 (TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE/IMPROVEMENT_CANDIDATE): **없음**

## 바닥선 판정 (Phase 1 결정 참고)
- ⚠ 재사용률 38.7% (70% 미만 · 검색·활용 체계 약함)
- ✅ 검증률 25.8%
- ✅ root_cause 저장률 100.0%
- ❌ 검색 적중률 0% (<50%)

## Phase 1 후보 (사용자 승인 후만)
1. `recurrence_events` 테이블 `root_cause` 컬럼 ALTER (스키마 1 변경)
2. `problem_solutions` 에 `experience_type` 컬럼 ALTER (TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE 분류)
3. `recurrence_improvements` 신규 테이블 (pre/post metric · verified flag)
4. `/learning-report` 커맨드 (상세 지표)
5. 신규 Hook ❌ · 신규 Subagent ❌ · 기존 Stop hook 에만 '학습 후보 검출' 로직 추가