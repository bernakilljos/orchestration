# 화면·기능 검증 룰 (Smoke Test 의무)

> **근거**: CLAUDE.md § 7-24. 사용자 지적 (2026-06-10): "화면 검증·기능 검증은 너가 해, 난 최종만 할 거야".
> **이유**: NPE (NULL 컬럼 + null-unsafe Java) 같은 기본 에러는 smoke test 한 번이면 잡힘. AI 가 "다음부터는 검증할게요" 라고만 약속하고 또 같은 패턴 반복 = 농땡이.

## 절대 룰

**DB / API / 프론트 변경 후 사용자에게 "확인해 주세요" 금지.** 자동 smoke test → PASS 후 보고.

## 검증 매트릭스 → [[verify-after-edit-mandatory]]

SoT: `.claude/rules/verify-after-edit-mandatory.md` — 증명 체인 5단계 (pre→수정→post→작동 테스트→보고).
Operating Principles § 6 '완료는 증명' · § 10 '종료 조건' 정합. 중복 본문 삭제 (2026-10-16 · 사용자 지시 '엔트로피 쫌 낮추자').
## NPE 패턴 자동 검출 (NULL 컬럼 + null-unsafe)

DB 컬럼이 NULL 가능 + Java/JS/Python 코드가 null check 안 함 = NPE 시한폭탄.

검출 패턴:
```bash
# 1. NULL 가능 컬럼 추출
grep -rE "ADD COLUMN \w+|NULL DEFAULT NULL" *.sql

# 2. 해당 컬럼 참조하는 코드 찾기
grep -rE "rs\.getString|getColumn|columns\['\w+'\]" src/

# 3. 매치되는 곳에 null check 있는지
# - Java: != null / Optional.ofNullable
# - Python: is None / .get(key, default)
# - JS: ?. / != null
```

매치 없음 + null check 없음 = WARN.

## 호출 흐름 (자동)

```bash
# PostToolUse hook (.claude/settings.json 등록됨)
# Edit/Write 가 .sql/.java/.py/.html/.tsx 파일 변경 시:
bash .claude/scripts/smoke-test-screen.sh <changed_file>

# 내부:
# 1. 파일 확장자 분류
# 2. .sql → schema 추출 → 영향 endpoint 식별 → curl
# 3. controller → endpoint 찾기 → curl + jq null check
# 4. 프론트 → Playwright → console error grep
# 5. PASS/FAIL 로그 + 사용자 보고
```

## "다음부터는" 약속 금지 (안티 패턴)

사용자가 NPE 발견 → AI: "다음부터는 smoke test 하겠습니다" = **농땡이 반복**.

올바른 행동:
1. 사용자 발견 즉시 → smoke test 룰 시스템에 박기 (이 문서 + skill + hook)
2. 같은 패턴 재발 = rule + hook 강화
3. 약속만 X, 코드/룰/hook 으로 강제

## 사용자 vs AI 역할 (명확화)

| 단계 | AI | 사용자 |
|---|---|---|
| 코드 수정 |  | — |
| 기능 검증 (curl·smoke) |  | — |
| 화면 검증 (Playwright render) |  | — |
| 에러 발견 시 자동 재수정 |  (max 3) | — |
| **최종 시각 확인** | — |  |
| 비즈니스 로직 결정 | — |  |

AI 가 사용자에게 "기능 검증해 주세요" 요청 = 룰 위반.

## 금지

1. **"확인해 주세요" 떠넘김** — AI 가 직접 curl·render·log 점검
2. **"다음부터는" 약속만** — 코드/룰/hook 으로 시스템화
3. **smoke test 결과 PASS 무시** — FAIL 이면 자동 재시도 (max 3회)
4. **null check 없는 코드 PASS** — NPE 패턴 grep 으로 사전 차단
5. **endpoint 영향 분석 skip** — DB 변경 시 모든 endpoint 추적

## 도구

- 스크립트: `.claude/scripts/smoke-test-screen.sh`
- skill: `plugins/exec_orch/skills/skill-smoke-test.md`
- hook: `.claude/settings.json` PostToolUse Edit/Write
- 로그: `.claude/logs/smoke-test.log`

## End-to-End 완결성 (DB → join → API → 화면) — 2026-08-12 사용자 강조

**"DB 추가 하라고 하면 DB 만 추가하고 화면에 안 나오는거·조인 걸어서 나오는 거 반영 안 한다"** = 완결성 위반.

### 원칙

DB·backend·frontend 변경 지시 시 **모든 레이어 자동 반영**:

| 변경 종류 | 반영 대상 (자동 감지) |
|---|---|
| DB 컬럼 추가 | ORM/DTO → repository → service → controller → API response → frontend model → 화면 표시 |
| DB 테이블 추가 | migration → seed → repository → service → API endpoint → frontend list/detail 화면 |
| API endpoint 추가 | controller → route registration → OpenAPI/swagger → frontend service call → 화면 |
| frontend 컴포넌트 추가 | route → menu → i18n → 권한 체크 → CSS 토큰 반영 |

### 감지 도구

DB 변경 감지 시 자동 grep:
```bash
# 컬럼명이 어디 참조되는지
grep -rn '<column_name>' src/ frontend/src/ resources/mapper/ *.xml *.sql
# 관련 화면·API 목록화 → 각각 반영 확인
```

### 사용자 참조 페이지 100% 반영

**"내가 관련 페이지도 주는데 반영 안 한다"** — 사용자가 참조 URL·파일 경로·PPT slide 번호·화면 명 주면 **100% Read + 관련 요소 다 반영**. 부분 반영 = 위반.

- 참조 파일 있으면 → `Read` tool 로 처음~끝 (`.claude/rules/full-survey.md` 100% Read 원칙 정합)
- 참조 화면명 있으면 → 화면 내 요소·필터·컬럼·이벤트 모두 나열 후 반영
- 참조 PPT 있으면 → 슬라이드 png export → 각 슬라이드 시각 검증

## RPA / Desktop UI (C/S) / Legacy SAP 검증 추가 (2026-10-27 사용자 지시 P0-2 반영)

**근거**: 2026-10-26 RPA 보고에서 사용자에게 "C/S 녹화·SAP 녹화 직접 해 봐 주십시오" 요청 = 이 룰 위반.

### 환경 제약 분리 보고 포맷 (떠넘김 패턴 유일 예외)

AI 가 **직접 검증 못 하는 유일한 경우** = 외부 의존 (사용자 계정·실제 SAP 접속·물리 장비). 그 외는 모의/테스트 더블로 수행.

```text
[보고 포맷 — 3구분 필수]
1. 자체 검증 완료: <테스트 환경·시나리오·실행 결과·증거 경로>
2. 환경 제약 미검증 (모의 수행): <부족 계정/장비/권한 + 모의 테스트 결과>
3. 사용자 최종 승인 요청: <자체 검증 완료 기능만 · 외부 의존 분리>
```

### C/S (Windows Desktop) 검증 매트릭스

| 대상 | AI 자체 검증 방법 |
|---|---|
| 테스트용 Windows 프로그램 실행 | `subprocess.Popen` + `psutil` + exit code |
| 클릭·입력·창 전환 | `pywinauto` · `pyautogui` headless (듀얼 모니터 주의 — `no-visible-windows.md` 정합) |
| 녹화 저장/재불러오기 | 파일 I/O + hash 비교 |
| 로그인 중복 방지 | 모의 세션 토큰 + mock DB |

### SAP (실제 접속 불가) 검증 매트릭스

| 대상 | AI 자체 검증 방법 |
|---|---|
| VBS 녹화 로직 | 테스트 더블 (`sap_mock.py`) · 샘플 VBS 파싱·변환·재생 |
| COM 호출 | `unittest.mock.MagicMock` 로 SAP COM object 대체 |
| 실제 SAP 접속 | **BLOCKED_EXTERNAL_DEPENDENCY** 분리 보고 |

### Supervisor 연결 (완료 판정 조건 오류 fix)

**구현 완료 ≠ 테스트 완료 ≠ 사용자 승인** 원칙 Supervisor 에 연결:
- 코드 작성 (RUNNING) → 자체 검증 통과 (`verify:<flag_path>`) → VERIFIED
- 환경 제약 발견 시 → `supervisor.py block <goal_id> "<사유>"` → BLOCKED (다른 goal 은 계속)
- BLOCKED 상태는 사용자 계정 제공 시 PLANNING 으로 복귀

### 2000+ 전체 시스템 반영 범위 (사용자 명시)

이 매트릭스 = RPA 특정 X · 모든 `.exe`·desktop UI·외부 시스템 통합 작업 공통. Universal Technology Discovery 결과 평가도 동일 원칙:
- 코드 작성 ≠ L4 (종단 간 실측)
- "기능 수 많음" ≠ 완성도 높음
- 테스트 증거 없이 L4 선언 금지

## 참조

- `CLAUDE.md § 7-24` (절대 룰)
- `CLAUDE.md § 7-21` (수정·빌드 후 자동 검증) — 디자인 산출물 검증과 정합
- `.claude/rules/best-practices.md` § 검증 후 보고
- `.claude/rules/failure-mode.md` § 회피 안티패턴
- `.claude/rules/no-visible-windows.md` (듀얼 모니터 창 숨김)
- `.claude/scripts/lib/supervisor.py` (BLOCKED 상태 · `block <goal_id> <reason>`)
- 메모리: `feedback_screen_verify_required.md`
