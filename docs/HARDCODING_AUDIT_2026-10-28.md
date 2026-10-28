# 하드코딩 전수 감사 보고 (2026-10-28)

> **근거**: 사용자 지시 "예시를 요구사항으로 하드코딩하지 마라 · 1단계 진단 전용 · 코드 수정 금지".
> **범위**: 11 영역 (Ledger · UserPrompt · Queue · Supervisor · Router · Runner · Workflow · Agent Registry · Technology Discovery · Verification Gate · Repair/Self-Healing · Statusline data layer).
> **방법**: Explore agent 4개 병렬 전수조사.

## 핵심 지적 (사용자)

사용자가 든 예시 (예: `1→3→7→2`) 는 **원칙 설명 사례** 일 뿐 · 숫자·순서·개수의 처리 요구 X.
Claude 가 이 예시를 **구현 명세로 받아들여 하드코딩** 하는 패턴 반복.

## 종합 결과

| 영역 | 결함 | 합법 | CRITICAL |
|---|---|---|---|
| Ledger·UserPrompt·Queue | 5 | 2 | 2 |
| Supervisor·Router·Runner | 12 | 8 | 5 |
| Workflow·Agent·Discovery | 11 | 6 | 2 |
| Verify·Repair·Statusline | 7 | 5 | 5 |
| **합계** | **35** | **21** | **14** |

## CRITICAL 결함 Top 5

### 1. verification 자동 PASS 매핑

- **파일**: `.claude/scripts/request-ledger.py:148`
- **코드**: `r["verification"] = verification or "PASS"`
- **문제**: `verification=""` (미제공) → `"PASS"` 자동 설정 · UNKNOWN 을 PASS 로 매핑
- **영향**: 모든 R 가 증거 없이 완료 처리 · 전수 감사 매번 거짓 PASS 발견 (R11·R23 사례)
- **수정안**: 4단계 상태 (`pending → implemented → verified → completed`) · verification 명시 요구

### 2. substring=truth 검증 (5건)

- **파일**: `.claude/scripts/lib/supervisor.py:453` · `.claude/scripts/integrated-audit.py:397,403,519`
- **코드**: `"PASS" in out or "OK" in out or "passed" in out`
- **문제**: "FAILED but PASS" 같은 혼재 출력도 성공 간주 · 문자열 포함만으로 검증 결과 단정
- **영향**: 테스트 결과 오탐 · 자동 실행 경로 거짓 성공
- **수정안**: word boundary (`\bPASS\b`) + fail-closed 로직 (supervisor.py:566 `_verify_output_passed` 이미 있음 — 공유 라이브러리로 승격 후 재사용)

### 3. standing-requirements 자동 PASS

- **파일**: `.claude/scripts/standing-requirements.py:94`
- **코드**: `return True  # 자동 검증 안 함 (수동 확인 전제)`
- **문제**: `verify_pattern` 없으면 **무조건 PASS**
- **영향**: standing requirements gate 가 실제 검증 안 함
- **수정안**: verify_pattern 없는 요구사항은 상태 `unverified` (PASS X) · 수동 검증 flag 요구

### 4. 미측정을 0 반환 (statusline)

- **파일**: `.claude/scripts/statusline_context.py:171`
- **코드**: 로그 폴더 없음 → `return 0, 0, 0, 0, ""`
- **문제**: 미측정을 "0" 으로 표시 (⏳ 아이콘 X)
- **영향**: 헌장 § 9 "미측정 ≠ 정상" 위반 · 실제 측정 X 인데 "오류 0" 처럼 보임
- **수정안**: ⏳ 명시 반환 + statusline fallback 변경 (디자인 FROZEN 유지 · 데이터 공식만)

### 5. ALLOWED_CMD_PREFIXES 임시 추가

- **파일**: `.claude/scripts/lib/supervisor.py:474-489`
- **코드**: `"touch .repair-sandbox/"`, `"mkdir -p .repair-sandbox/"` 등 Self-Healing 전용 prefix 하드코딩
- **문제**: Self-Healing 예시 작업 지원하려고 prefix 추가 · 향후 변경 시 전수 수정 필요
- **수정안**: `.claude/config/approved-commands.json` 외부화

## HIGH 결함 (7건)

| # | 파일:라인 | 내용 |
|---|---|---|
| H1 | `router.py:141-170` | 토큰 임계값 200·500k·800k 하드코딩 (근거 없음) |
| H2 | `router.py:133,201,216` | thinking_budget 8000/4000 하드코딩 |
| H3 | `route.py:231,252` | fable-5 특수 분기 (20% cap · 모델 이름) |
| H4 | `router.py:43-51` vs `route.py:113-124` | AiChoice enum (7) vs status (8) 불일치 |
| H5 | `classify-task.py:31,34,46` | 300줄·3-5파일·500k 라우팅 트리거 근거 없음 |
| H6 | `supervisor.py:636-641` | 긍정 신호 regex 하드코딩 (nUnit 등 다른 프레임워크 누락) |
| H7 | `supervisor.py:625-630` | 금지 패턴 14개 하드코딩 (새 에러 패턴 추가마다 수정) |

## MEDIUM / LOW 결함 (23건)

- window_s=10 (중복 감지 · 임시 해결책 · 메시지 ID 없음)
- 60/200자 분류 경계 (다국어 미흡)
- max_retry=3 (근거 없음)
- STALE_SEC = 6h 고정
- technology discovery SEED_DOMAINS 20개 (seed only · 자동 확장 미구현)
- workflow 8 YAML (문서는 9-chain 주장)
- max_hops=10 workflow depth 고정
- Agent 분산 (19 global + plugin · 중앙 registry 없음)

## 수정 계획 (2단계 · 사용자 승인 후 실행)

| Phase | 범위 | NEW/CHANGE | 영향 |
|---|---|---|---|
| **P0a** | CRITICAL Top 5 (verification + substring + standing + statusline + ALLOWED_CMD) | CHANGE 5 · NEW 1 (`approved-commands.json`) | 핵심 거짓 PASS 재발 방지 |
| **P0b** | HIGH 7건 (router/classify 임계값 · AiChoice 불일치) | CHANGE 7 · NEW 1 (`ai-registry.yaml`) | 라우팅·모델 등록 일원화 |
| **P1** | MEDIUM 23건 (window·classify 다국어·workflow·agent registry) | 분할 처리 · 다음 세션 | 설정 외부화·동적 발견 |

## 반례 테스트 (범용 Orchestration 검증 · 이번 세션)

**다중 지시 종단 6/6 PASS** (숫자·개수 하드코딩 X 확인):

| Test | 결과 |
|---|---|
| N 가변 (1·2·5·10·30) | PASS |
| 10s 윈도우 멱등성 (1차 신규 · 2차 1s 중복 · 3차 11s 신규) | PASS |
| 실행 중 신규 유입 (3→5) | PASS |
| 임의 15개 random 숫자·순서 | PASS |
| 세션 격리 (sess_A·sess_B 같은 내용 신규) | PASS |
| 분류 커버리지 (execute·report·status·cancel·redo) 8/8 | PASS |

**Approval Gate 회귀 18/18 PASS** (regex 보완 후).

## 결론

- Claude 가 예시를 실제 명세로 받아들여 **35 결함** 생성 (CRITICAL 14)
- 가장 심각: CRITICAL Top 5 — 모두 "거짓 PASS 재발" 근본 원인
- **1단계 진단 완료** · 2단계 수정 계획 제시 · 3단계 수정은 **사용자 승인 후**
- 범용 다중 지시 종단은 이번 세션 PASS (6/6) · 하드코딩 제거 후에도 유지해야

## 관련

- `.claude/rules/complete-output.md` (D21 완전본 원칙 — 예시 1건 X · 같은 종류 전체)
- `.claude/rules/consistency.md` (기준 일관성)
- `.claude/state/next-actions.md` (P0 수정 이월)
- commit `19f5790` (이전 세션 · Approval Gate + Ledger report_request + 계정 분리)
