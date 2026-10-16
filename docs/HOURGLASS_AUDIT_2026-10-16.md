# ⏳ 상태 세분화 감사 — 2026-10-16 17:01

상태 매트릭스: ✅ 정상 · ❌ 실패 · ⚠ 읽기/실행 실패 · ⏳ 측정 대기 · ↻ 실행 중 · ? 소스 불명 · — 측정 불가

| 항목 | 현재상태 | 데이터소스 | 측정가능 | 실제원인 | 수정필요 |
|---|---|---|---|---|---|
| test | ⏳ | package.json scripts.test / pyproject.toml pytest / golden-test.py (kit 전용) | YES | 소스 있음 · 아직 실행 X | YES |
| build | — | N/A | no | kit 는 build 단계 없음 (python/bash script · 컴파일 X) | no |
| lint | ⏳ | ruff/pyproject | YES | 소스 있음 · 아직 실행 X | YES |
| type | — | N/A | no | kit 는 type checker 미설정 (python 동적 타입) | no |
| 컴포넌트 재사용 | ? | N/A | no | kit 자체는 UI 컴포넌트 X · install 대상 프로젝트에서 측정 | no |
| 공통 우회 | ? | N/A | no | 공통 컴포넌트 우회 감지는 target 프로젝트 전용 | no |
| CSS 중복 | — | N/A | no | kit 는 CSS 자산 X · UI 프로젝트 전용 지표 | no |
| 신규공통 | ? | N/A | no | '신규 공통 컴포넌트 생성' 추적 소스 없음 | no |
| 영향도 | ✅ | git diff --stat | YES | 1 파일 변경 | no |
| breaking | ? | N/A | no | breaking change 자동 감지 소스 없음 (semver bump + CHANGELOG 수동) | no |
| golden | ⏳ | golden-test.py | YES | 스크립트 존재 · 실행 OK (13/13) · cache 없음 | YES |
| Codex 검증 | ⏳ | .claude/state/orca.db tasks 테이블 | YES | DB 존재 · 자동 검증 집계 미구현 | YES |
| Web 검증 | ? | N/A | no | Claude Web 검증 결과 자동 수집 소스 없음 | no |

## 요약

- ?: 5건
- —: 3건
- ⏳: 4건
- ✅: 1건

## 수정 계획

1. ⏳ (측정 가능 · 미실행) → 실제 측정 실행 or source 추가
2. ? (소스 불명) → 측정 소스 식별 또는 — 로 변경
3. — (측정 불가) → statusline 에서 아예 제거 또는 '해당 없음' 표시
4. ⚠ (실행 실패) → 원인 조사 · 재시도

## 적용 원칙

- ⏳ 를 기본 fallback 으로 사용 X
- 각 지표 소스를 명시
- '측정 대기' vs '불러오는 중' vs '소스 없음' vs '측정 불가' 구분
