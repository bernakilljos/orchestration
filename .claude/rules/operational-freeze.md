# 운영 동결 룰 (Operational Freeze · SoT)

> **근거**: 2026-10-16 사용자 지시 — "1차 감사 → 2차 안정화 → 골든 테스트 → **FREEZE** → 실제 개발 시만 수정".
> **왜**: Claude 가 매번 "뭔가 추가" 성향 → 1년 안 hooks 500+·skills 500+ 폭주 위험. FREEZE 로 구조 안정화.

## 동결 선언

**현재 orchestration 구조를 안정화 완료 상태로 간주한다.**

## statusline FREEZE 범위 (2026-10-16 사용자 명시 재확인)

- **레이아웃** (6쌍 + 토큰·비용 단독 · 9 라인)
- **색상 체계** (ANSI color code · 강조 · 배경 · 라벨 색 · 값 색)
- **구분자** (│ · »»»»)
- **들여쓰기** (앞 공백 2칸 · col 15)
- **이모지** (🧠·🎨·💻·🧪·🧩·📊·📋·🛑·✅·🔐·🎯·📡·🚨·🤖·🔒·💰)
- **지표 소유** (한 지표 = 한 줄 · 중복 금지)
- **전파** (sync-to-team · install-to-target · merge-to-target 정책)

- Operating Principles · Execution Contract · Request Ledger · recurrence-tracker · scope-lock 모두 정상 작동
- 2차 안정화 감사 완료 (ORCHESTRATION_AUDIT_2026-10-16.md § 다음 권장 포함)
- 골든 테스트 10개 PASS

**이후 "인터넷 뒤져서 더 보완해" 류 요청으로 hook/rule/skill/subagent 를 추가하지 않는다.**

## 추가·수정 허용 조건 (OR · 하나 이상 만족)

1. **실제 재발 문제** — recurrence-tracker 가 3회+ 승격 알림 발생
2. **검증 실패** — 골든 테스트 10개 중 하나 FAIL
3. **성능 병목** — 측정값이 임계 초과 (SessionStart >5s · prompt-dispatch >2s)
4. **공식 Claude Code 기능 변경** — Anthropic 공식 changelog 알림 ( 이상 자율 적용)
5. **크리티컬 5가지** — 시크릿·데이터손실·보안·비용·시스템손상 긴급 대응

**위 5가지 외는 "좋아 보인다"는 이유로 추가 X**.

## FREEZE 모드 운영 규칙

### 금지 (기본)

- 신규 hook 추가 (기존 수정만)
- 신규 rule 추가 (`.claude/rules/*.md`)
- 신규 skill 추가 (반복 작업 절차 외)
- 신규 subagent 추가 (기존 4개 역할 재사용 우선: investigator / implementer / reviewer / verifier)
- "WebSearch 로 더 찾아봐" 류 자율 확장

### 허용 (상시)

- 기존 룰 수정 (중복 제거·명확화)
- 발견사항 기록 (`.claude/state/audit-findings-*.md`)
- 사용자 명시 요청 (단, Change Budget NEW ≤2 · CHANGE ≤5 안)
- 외부 감사 결과 반영

## 운영 모드 전환 흐름

```text
1차 구조교정 (ORCHESTRATION_AUDIT_2026-10-16)
         ↓
2차 안정화 감사 (R13 15섹션 PASS/PARTIAL/FAIL)
         ↓
골든 테스트 10개 (T01~T10 회귀 테스트)
         ↓
안정성 90+ 확인
         ↓
FREEZE (이 룰 활성)
         ↓
실제 개발 중 재발·검증 실패·성능 병목·공식 변경 시만 수정
```

## 해제 조건

- 사용자 명시 지시 — `/unfreeze` 또는 "동결 해제" 선언
- 구조적 결함 발견 (설계 수준 재검토 필요)
- Change Budget 상한 해제가 필요한 상황 사용자 승인

**동결 해제 후** = 다시 2차 안정화 감사부터 재실행 → FREEZE 복귀.

## 관련

- `operating-principles.md` (10 원칙 · Change Budget)
- `execution-contract.md` (Request Ledger · n/n 완료)
- `docs/ORCHESTRATION_AUDIT_2026-10-16.md` (1차 감사)
- `.claude/scripts/golden-test.py` (10 회귀 테스트 — 다음 세션 작성)
- 외부 감사 § "안정화 완료 후 운영 모드로 전환"
