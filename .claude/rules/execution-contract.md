# Execution Contract — 실행 계약 (SoT)

> **근거**: 2026-10-16 외부 감사 (`docs/ORCHESTRATION_AUDIT_2026-10-16.md`) — 5대 결함 해결.
> **SoT**: 이 파일. 다른 룰 (auto-planner · complete-output 등) 은 이 계약 안에서만 세부 지침.
> **왜 신설**: 기존 룰 간 충돌 (범위·보고 시점·Codex 라우팅) 로 Claude 가 세션마다 다르게 동작 → 사용자 "다 해라" 와 실제 "일부만 하고 보고" 가 매번 어긋남.

## 1. Request Ledger (요청 원장 · n/n 완료 강제)

**원칙**: 사용자 1 턴 메시지에서 **독립 요청 N개** 를 ledger 에 기록 → **N/N 완료 전 최종 보고 금지**.

### 흐름

```text
사용자 메시지
      ↓
[request-ledger] N 개 request 추출 (R1, R2, R3 ...)
      ↓
.claude/state/request-ledger.json 저장
      ↓
R1 실행 → 완료 체크
R2 실행 → 완료 체크
R3 실행 → 완료 체크
      ↓
N/N 완료 확인 (Stop hook gate)
      ↓
최종 1회 보고
```

### Request 추출 규칙

- 번호 리스트 (`1. 2. 3.`) · 각 항목 1 request
- 명령형 동사 (`해줘`·`수정`·`만들어`·`확인`·`전파`·`커밋`) · 각 1 request
- 1 턴 메시지 안 여러 지시 → 각 1 request
- "다 해"·"전부"·"계속" = 이전 ledger 미완료 request 전부 실행

### SoT

- 저장: `.claude/state/request-ledger.json`
- CLI: `.claude/scripts/request-ledger.py` (add/complete/status)

## 2. n/n 완료 전 보고 금지 (중간보고 폐지)

### 금지

- 각 request 완료 후 중간 보고
- "A/B 플랜 선택" 요청 (사용자가 이미 "다" 결정했음)
- "남은 결정사항" 질문 (크리티컬 5 외)
- 5단계 plan **출력** (내부 실행만 · 사용자 노출 X)

### 허용 (유일)

- **크리티컬 5가지** 긴급 알림 (시크릿·데이터손실·보안·비용·시스템손상)
- N/N 완료 **후** 1회 최종 보고

### Stop hook Request Ledger Gate

- Stop hook 이 `request-ledger.json` 읽음
- 미완료 request 있음 → Claude 에게 "N/M 완료 · 미완료 request 계속" 지시
- 모두 완료 → Stop 허용

구현: `.claude/hooks/stop-request-ledger-gate.sh`

## 3. 범위 lock (인접 시스템 자동 확장 금지)

### 폐지 (기존 auto-planner)

- "사용자 명시 안 한 인접 시스템도 포함" ❌
- "전역까지 모든 위치 훑기" (전수조사 범위 자동 확장) ❌

### 신 원칙

- **직접 의존성만 조사** (요청 대상 파일 + 그 파일이 import/require/call 하는 파일 1 hop)
- **임의 범위 확대 금지** · 의존성 밖은 **발견사항 기록만**
- "전수조사" 는 **요청 범위 안** 전수 (범위 밖 전수 X)

### Operating Principles § 2 (범위 lock) 정합

이 섹션이 operating-principles § 2 보다 **구체화된 세부** · 상충 X.

## 4. Codex 라우팅 (명시 트리거 확장)

### 기존 결함

- `route_dispatch`: Codex = 800k+ 또는 quota fallback (사실상 X)
- CLAUDE.md: 500줄+도 Claude general-purpose subagent 1순위
- `classify-task`: Codex 트리거 좁음

### 신 Codex 트리거 (OR)

Claude 직접 처리 **대신** Codex 위임:

1. 사용자가 "Codex" 명시
2. **3+ 파일** 동시 수정 필요
3. 반복 패턴 (×4+ 유사 구현)
4. **300줄+ 예상** 구현
5. 독립 코드 리뷰 필요한 작업
6. 대량·마이그레이션·전체 파일 수정

### 실행 흐름 (orchestrator 자동 호출)

```bash
task-instruction.md 생성 (Claude)
      ↓
auto-dispatch → Codex worker (자동 spawn if 꺼짐)
      ↓
Codex 결과 회수 (완료 알림)
      ↓
Claude 가 diff/test 로 재검증
```

### 금지

- "task-instruction.md 작성 · 사용자가 터미널에서 실행" (Zero-touch 위반) ❌
- "Codex 권장" systemMessage 만 출력 (실제 dispatch X) ❌

## 5. Web/Codex 교차검증

- Claude 복잡 설계·결정 → Codex 로 구현 → Claude 검증 → (옵션) Web 비교
- Web 리서치는 **실측 가능한 외부 사실** 만 (라이브러리 버전·공식 docs·벤치)
- Claude 가 혼자 "다 안다" 가정 X · 외부 소스 cross-check

## 6. 고객용 UI = 업무 흐름 중심

### 원칙

- 고객 화면 **메인** = 사용자 업무 플로우 (`증빙 수신 → 유형 확인 → 자동 인식 → 신뢰도 → 일치 여부 → AI 판정 → 결과 저장`)
- **내부 구현 세부** (OCR · 텍스트레이어 · Tesseract · parser · pipeline) → **상세·도움말·관리자 설정·기술정보** 로 숨김

### 금지

- 기술 용어 (`PDF 추출 파이프라인`·`텍스트레이어 우선`·`OCR fallback`) 를 **고객용 메인 화면** 에 노출 ❌
- 개발자 설명 = 좋은 설명이지만 고객 화면이 아님 (분리 필수)

### Reviewer 체크리스트 (customer-facing)

Reviewer agent 가 UI PR 검토 시 추가 체크:

- [ ] 메인 화면에 기술 용어 노출 없음
- [ ] 업무 플로우 순서가 명확
- [ ] 각 단계 "사용자 관점" 설명 (내부 구현 설명 X)
- [ ] 상세·도움말 패널로 기술 세부 분리

## 7. Change Budget (Operating Principles 상속)

- NEW ≤ 2 · CHANGE ≤ 5 · REMOVE 무제한
- 사용자 명시 상한 해제 가능

## 관련

- `operating-principles.md` (10 원칙 · 역할 분리 · Change Budget)
- `complete-output.md` (완전본 원칙 · n/n 완료)
- `auto-planner.md` (범위·보고 시점 제거 적용 — 2026-10-16)
- `codex-rules.md` (task-instruction 생성)
- `.claude/scripts/request-ledger.py` (SoT CLI)
- `.claude/hooks/stop-request-ledger-gate.sh` (Stop gate)
- 외부 감사: `docs/ORCHESTRATION_AUDIT_2026-10-16.md`
