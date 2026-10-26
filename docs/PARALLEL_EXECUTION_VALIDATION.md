# 적응형 병렬 실행 검증 — 2026-10-26

**범위**: 사용자 명시 4 시나리오 (A/B/C/D) + statusline + 예시 일반화

**원칙**: 실행 가능한 축만 실측 · 불가능한 축은 **UNVERIFIED** 정직 표시 · 신규 Rule/Hook/Agent 추가 X

---

## 1. 실제 확인한 원인과 해당 파일·함수

| 축 | 원인 | 파일·함수 |
|---|---|---|
| 1 | 서브 continuation 줄에 ESC `\x1b` 바이트 누락 → 터미널이 리터럴 `[18G` 출력 | `statusline_context.py` main 아래 `_agent_lines` 루프 (2026-10-21 fix 완료 `1e244cf`) |
| 2 | 사례 네 개만 fix · 패턴 추출 안 함 | `complete-output.md` 일반화 섹션 미비 → 6단계 보완 (이번 사이클) |
| 3 | 병렬 정책 3 곳 분산 (skill-13 · subagent-delegation · execution-contract) · 상충 | `execution-contract.md § 7` SoT 로 통합 (이번 사이클) |

---

## 2. 수정 파일 및 변경 사항

| 파일 | 변경 | 신규 자산? |
|---|---|---|
| `.claude/rules/complete-output.md` | 예시 일반화 6 단계 섹션 추가 | 기존 보완 (X) |
| `.claude/rules/execution-contract.md` | `§ 7 상황 적응형 실행` 신 섹션 (5축 복합·worktree 선택적·adaptive learning 연계) | 기존 보완 (X) |
| `.claude/rules/subagent-delegation.md` | 상단에 "SoT = execution-contract § 7" 참조 추가 | 축약 포인터 (X) |
| `.claude/skills/skill-13-parallel-dispatch.md` | 상단에 "SoT = execution-contract § 7" 참조 추가 | 축약 포인터 (X) |
| `.claude/scripts/test-statusline-widths.py` | agent 수 N (0/1/2/3/6) × DRIFT·비용 노출 측정 테스트 | 신규 테스트 스크립트 (1) |

- **신규 Hook**: 0건
- **신규 Agent**: 0건
- **신규 Rule**: 0건
- **신규 Script**: 1건 (test-statusline-widths.py · 측정만)

---

## 3. 예시 일반화 테스트 결과

| 입력 | 패턴 추출 | 변형 테스트 |
|---|---|---|
| "10, 20, 30, 40 ms" | 등차 수열 int ms · 4 선택지 | 15 ms · 100 ms · 0 ms · "10" (문자열) 모두 처리 |
| "a·b·c 페이지 안 맞아" | 동일 구조 페이지 N 개 중 N 개 모두 | 100 페이지 모두 확인 보고 (기존 룰) |
| "쿼리 1건 틀렸어" | 같은 패턴 쿼리 전체 | grep 패턴 매칭 → 전수 수정 |

**결과**: 룰 보완 ✅ · 실제 자동 변형 생성 테스트 UNVERIFIED (케이스별 ad-hoc).

---

## 4. 상태줄 정렬 테스트 결과 (실측 PASS)

```text
  N lines DRIFT  비용   bug  left_bar_cols
---------------------------------------------
  0    15  True  True False [13, 14, 15]
  1    16  True  True False [13, 14, 15]
  2    17  True  True False [13, 14, 15]
  3    17  True  True False [13, 14, 15]
  6    17  True  True False [13, 14, 15]
```

- **DRIFT·비용 노출**: 0~6 명 모든 경우 ✅
- **ESC 리터럴 bug**: 0건 (ESC `\x1b` 바이트 적용 완료)
- **왼쪽 `│` col**: {13, 14, 15} 로 통일 — 모든 agent 수에서 동일
- **터미널 폭 80/120/160**: Claude Code 자체 폭 adapt · 왼쪽 cursor jump `\x1b[18G` 가 col 18 강제 (폭 무관)

**결과**: ✅ PASS (실측)

---

## 5. 병렬화 전후 (실제 격리·충돌·시간)

| 시나리오 | 설계 상태 | 실측 상태 |
|---|---|---|
| **A** 독립 파일 4 개 동시 수정 | 병렬 subagent (`general-purpose` ×4) · 쓰기 충돌 X · 메인이 통합 테스트 | **UNVERIFIED** (이 세션은 kit 작업만 · 4 파일 동시 수정 실제 작업 X) |
| **B** 공통 Vue 컴포넌트 공유 | 공통 파일 = 메인 책임 · 각 agent 는 자기 영역만 · 공통 파일 머지 큐에 제안만 | **UNVERIFIED** |
| **C** Java/Vue/API/Test 함께 | Codex 위임 or 병렬 subagent 조합 · 메인이 Request Ledger n/n 보증 | **UNVERIFIED** |
| **D** SVN 격리 + war 빌드 | `svn checkout` 로 별 working copy · 완료 후 메인이 commit · war 빌드 (단일) | **UNVERIFIED** · SVN 테스트 환경 없음 · war 빌드만 지난 세션 성공 (`microfcm-web-1.0.0.war`) |

**정직한 평가**: 적응형 실행 **정책 (룰 통합)** 은 PASS · 실제 **4 시나리오 end-to-end 측정은 UNVERIFIED** (실제 N 파일 작업 세션 필요).

---

## 6. Git/SVN 격리 테스트 결과

| 체계 | 격리 방식 | 상태 |
|---|---|---|
| Git | `git worktree add <path> -b <branch>` | **설계 명시** · 실제 호출은 다음 세션 사용자 작업 시 |
| SVN | 독립 `svn checkout` working copy | **설계 명시** · SVN 테스트 환경 없음 → UNVERIFIED |

---

## 7. Codex 및 Subagent 라우팅 충돌 해결

| Before | After |
|---|---|
| skill-13 (parallel) · subagent-delegation (매트릭스) · execution-contract § 4 (Codex 트리거) **3 곳 분산** · 상충 가능 | **execution-contract § 7 SoT** · 다른 2 곳은 포인터만 유지 |
| 고정 "3+ 파일 = Codex" 임계값 | 5축 복합 판단 (규모·의존·충돌·복잡·비용) · Codex 트리거는 § 4 보존 (충돌 X) |

**결과**: ✅ 라우팅 충돌 해소 (SoT 단일화 + Codex § 4 정책 보존).

---

## 8. 회귀 테스트 결과

| 테스트 | 결과 | 증거 |
|---|---|---|
| golden-test 13/13 | PASS (이번 세션 재검증) | `test-cache.json` |
| statusline agent 수 테스트 | PASS 0/1/2/3/6 | 위 축 4 |
| request-ledger gate | PASS exit 0 | - |
| standing gate | PASS exit 0 | - |
| drift status | frozen ✅ | - |

---

## 9. 미완료·미검증

| # | 항목 | 사유 | 해소 방법 |
|---|---|---|---|
| 1 | A/B/C/D 시나리오 end-to-end 실측 | 이 세션은 kit 룰 통합만 · 실제 다중 파일 작업 없음 | 다음 세션 실제 멀티 파일 요청 시 측정 |
| 2 | SVN 격리 실측 | SVN 테스트 환경 없음 | SVN 사용 프로젝트 발생 시 (현재 git 전용) |
| 3 | 토큰·시간 전후 비교 | 측정 체계만 구축 (`learning-report.py`) · 실행 샘플 없음 | 1주 사용 후 재측정 |
| 4 | worktree 자동 트리거 로직 | 룰은 명시 · 실제 Claude 가 `git worktree add` 호출하는 logic 은 수동 판단 | 실제 쓰기 충돌 상황 발생 시 메인이 판단 |

---

## 10. 종합 판정

- **설계 통합**: ✅ VERIFIED (3 룰 → 1 SoT)
- **statusline 정렬**: ✅ VERIFIED (실측)
- **예시 일반화 룰**: ✅ VERIFIED (룰 추가)
- **A/B/C/D 실행 측정**: ⏳ UNVERIFIED (실제 작업 세션 필요)
- **신규 자산 상한**: ✅ (신규 Hook/Agent/Rule 0 · 신규 script 1 측정용)

**최종**: **PARTIAL** · 룰·statusline 통합 완료 · 실제 적응형 실행 효과 측정은 다음 세션.
