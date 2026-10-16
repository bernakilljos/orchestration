# Operating Principles — Claude Code 운영 10 원칙 (SoT)

> **근거**: 2026-10-16 사용자 지시 — "변경할 필요가 없으면 변경 안 함 · 설정 수정이 목표 X · 단순·안정·검증 가능이 목표".
> **SoT**: 이 파일. CLAUDE.md § 0 는 요약·참조. 다른 룰은 본문 중복 X · `[[operating-principles]]` 링크로.
> **Anthropic 공식**: Help Center "반복 워크플로우 = Skill · 결정적 자동화·차단 = Hook · 독립 판단 = Subagent" 정합.

## 목표

**많이 수정하는 것이 아니라, 요청 범위를 정확히 이해하고 최소 변경으로 완성도 높은 결과.**

## 10 원칙

### 1. 먼저 조사, 그다음 수정

- 수정 전에 관련 코드·공통 컴포넌트·공통 CSS·기존 구현 **검색** 필수
- 원인 미확인 상태로 추측 수정 X
- 이미 존재하는 구현을 새로 만들기 전에 **재사용 가능 여부 반드시 확인**
- 조사 없이 구현 들어간 경우 **작업 품질 실패** 로 간주

### 2. 요청 범위 lock

- 사용자가 요청하지 않은 기능·디자인·구조·이름·파일 임의 변경 X
- 더 좋은 방법 있어도 요청 범위 넘어가면 수정 X **제안만**
- 관련 없어 보이는 문제 발견해도 현재 작업에 포함 X
- 예상 수정 범위 커지면 먼저 영향 범위 판단
- **강제**: `.claude/scripts/scope-lock.py` (`/scope`)

### 3. 최소 변경 원칙

- 문제 해결에 필요한 최소 파일·최소 코드만 변경
- 불필요한 리팩터링 X
- 기존 정상 동작 유지가 새 구조 만드는 것보다 **우선**
- 한 문제 해결하면서 새 구조·규칙 임의 도입 X

### 4. 공통화 우선 (재사용 증명)

- 새 컴포넌트·함수·CSS·유틸리티 만들기 전에 기존 공통 구현 **검색**
- 동일 역할 구현 있으면 **재사용**
- 페이지별 CSS 복제·비슷한 컴포넌트 중복 생성 **금지**
- **새 코드 작성 전 "이미 이 기능이 존재하는가?" 먼저 증명**

### 5. 디자인 임의 해석 X

- 디자인 변경 요청 없으면 기존 UI 유지
- 동일 유형 페이지의 위치·여백·크기·헤더·버튼·폼 규칙 일치
- 임의 margin·padding·width·height·색상·아이콘 추가 X
- 기존 design token·공통 CSS·공통 컴포넌트 우선

### 6. 완료는 증명해야 한다

- "될 것 같다"·"수정했다"·"문제없다" = **완료 근거 아님**
- 완료 주장에는 실제 코드·diff·build·test·lint·typecheck 또는 실행 결과 필요
- 실행 가능한 검증 수행 X → **"미검증"** 표시
- 실패 항목 존재 → 완료 보고 X

### 7. 구현자와 검증자 분리

- 구현 결과는 가능하면 별도 **reviewer·verifier subagent** 가 다시 확인
- reviewer 는 구현 의도 **옹호 X · 결함 찾기** 역할
- 확인 항목: 요구사항 누락·범위 위반·중복 구현·공통화 우회·하드코딩·회귀 가능성
- **검증 agent 성격**: "너의 목적은 구현을 승인하는 것이 아니라 구현에서 틀린 부분을 찾아내는 것. 구현자 설명을 사실로 가정하지 말고 코드·실행 결과만 근거로 판단"

### 8. 재발 = 품질 실패

- 사용자가 이전에 지적한 동일 문제 다시 발생 → **재발 기록**
- 반복 발생한 문제는 단순 경고 X · **rule·hook 강화 후보로 승격**
- 같은 유형 실수 반복되면 원인 분석 + 방지 규칙 추가
- **자동 승격 (SoT: `.claude/scripts/recurrence-tracker.py`)**:
  - 1회 → log 만
  - 2회 → warn (promoted_level=1)
  - 3회 → CLAUDE.md 규칙 승격 후보 (`.claude/state/rule-promotion-candidates.md`)
  - 5회 → Hook 강제 차단 후보 (`.claude/state/hook-enforcement-candidates.md`)

### 9. 미측정 ≠ 정상

- 검사하지 않은 항목을 0 또는 정상으로 기록 X
- 상태는 **정상 / 실패 / 미측정** 3 분류
- 미측정 항목이 핵심 검증 포함 → READY 완료 상태 X

### 10. 작업 종료 조건

다음 **전부** 만족해야 완료:

- [ ] 요청사항 누락 없음
- [ ] 범위 밖 임의 변경 없음
- [ ] 관련 공통 구현 확인 완료
- [ ] 실행 가능한 검증 완료
- [ ] 신규 critical·error 없음
- [ ] 알려진 실패 항목 명시
- [ ] 변경 영향 확인
- [ ] 증거가 있는 완료 보고

**우선순위**: 속도보다 정확성 · 대규모 수정보다 최소 변경 · 추측보다 증거 · 새 구현보다 재사용.

## 역할 분리 (엔트로피 낮춤 · SoT · 중복 금지)

| 층 | 책임 | 중복 금지 원칙 |
|---|---|---|
| **CLAUDE.md** | 기본 원칙 선언 · SoT 참조 | 500 줄 이하 · 본문 중복 X · 참조만 |
| **Rule (`.claude/rules/*.md`)** | 영역별 규칙 (판단 기준) | 1 규칙 = 1 SoT 파일 · 다른 파일은 `[[참조]]` |
| **Hook (`.claude/hooks/`)** | 반드시 막거나 자동 실행 (deterministic) | 경고·알림은 Hook 금지 → Skill·Subagent |
| **Skill (`.claude/skills/`, `plugins/*/skills/`)** | 반복 작업 절차 | 1회성·실험 Skill 금지 |
| **Subagent (`.claude/agents/`, `plugins/*/agents/`)** | 독립 조사·리뷰·검증 (판단) | 1 역할 = 1 agent · 범용 agent 금지 |
| **Statusline (`.claude/statusline.sh`, `scripts/statusline_*.py`)** | 관측·표시 | 지시·행동 금지 (관측만) |

### 중복 발견 시 처리

1. SoT 파일 1개 지정
2. 다른 파일은 본문 삭제 → `[[SoT-slug]]` 링크 1줄
3. 사용자 승인 후 REMOVE
4. 감지: `.claude/scripts/recurrence-tracker.py stats` + grep

## 변경 예산 (Change Budget · 매 세션)

- **NEW**: 최대 2개 (사용자 명시 승인 시 상한 해제)
- **CHANGE**: 최대 5개
- **REMOVE**: 무제한 (엔트로피 낮춤 장려)

**변경할 필요 없으면 변경 안 함.** 설정 수정이 목표 X · 단순·안정·검증 가능이 목표.

## 작업 패턴 (/audit-claude 참고)

**감사 → 증명 → 필요할 때만 수정**:

```text
1. 조사 (현재 상태 전수)
2. 공식 문서 (Anthropic 공식·GitHub·Help Center) 확인
3. 증명 (문제점·근거·공식 근거·필요 여부·기대 효과·부작용)
4. 중복 제거 (SoT 통합)
5. 변경 기준 체크 (반복 문제 방지·누락·중복 제거·공식 기능 대체·비용·검증 신뢰도)
6. 최소 변경 (NEW 2 · CHANGE 5 · REMOVE 무제한)
7. 변경 전 보고 (KEEP·CHANGE·REMOVE·NEW 분류 표)
8. 수정 후 검증 (문법·hook·agent·skill·중복·충돌·회귀·테스트 가능 실제 실행)
9. 최종 결과 (유지·변경·제거·신규·근거·검증·미확인·다음 재검)
```

**중요**: 변경할 필요 없으면 "현재 구성이 더 낫기 때문에 변경하지 않음" 결론 OK.

## 관련

- CLAUDE.md § 0 (요약·참조 · SoT 는 이 파일)
- `.claude/rules/scope-lock*` (범위 lock)
- `.claude/rules/verify-after-edit-mandatory.md` (완료 증명)
- `.claude/rules/no-false-report.md` (검증 신뢰도)
- `.claude/rules/consistency.md` (중복 금지)
- `.claude/scripts/recurrence-tracker.py` (재발 추적)
- `plugins/exec_orch/commands/audit-claude.md` (감사 skill)
- Anthropic Help Center — "반복 워크플로우는 Skill, deterministic 자동화는 Hook, 독립 판단은 Subagent"
