# P0b 상태 매트릭스 (엄격 분류 · 2026-10-29)

> **근거**: 사용자 지시 — "완료 / 부분 / Scaffold / 검증 미완료 엄격 구분". 전체 완료 뭉뚱그림 금지.
> **원칙**: 코드만 바꿈 ≠ VERIFIED. 종단 테스트 통과 + Registry 변경 반영 확인 후 VERIFIED.

## 상태 레이블 정의

| 레이블 | 의미 |
|---|---|
| **VERIFIED** | 코드 반영 + 종단 테스트 통과 + Registry 변경에 반응 (예시 숫자 하드코딩 X) |
| **IMPLEMENTED** | 코드 반영 완료 · 자동 테스트 PASS · 운영 반영 전 |
| **PARTIAL** | 핵심 수정 완료 · 완전 중앙화는 scaffold (호환 어댑터로 유지) |
| **SCAFFOLD** | 뼈대만 존재 · 실제 참조 경로 미연결 |
| **NOT_A_DEFECT** | 재감사 결과 결함 아님 (설계 의도 문서화) |
| **BLOCKED** | 외부 의존 (API key, 계정, 상용 소스) 미해결 |

## P0b HIGH 7건 (H1~H7)

| ID | 결함 요지 | 수정 요지 | 상태 (2026-10-29) | 종단 증거 |
|---|---|---|---|---|
| **H1** | router.py 토큰 임계값 200·500k·800k 하드코딩 | `ai-registry.yaml routing_thresholds` 참조 (`get_routing_threshold`) | **VERIFIED** | test-h1-h2-h4-e2e.py §2 PASS · YAML 변경 → Router 임계값 반영 |
| **H2** | router.py thinking_budget 8000·4000 하드코딩 | `ai-registry.yaml thinking_budget` 참조 (`get_thinking_budget`) | **VERIFIED** | test-h1-h2-h4-e2e.py §3 PASS |
| **H3** | route.py fable-5 특수 분기 20% cap | 모델 자체 속성 `budget_cap_pct` 로 일원화 | **VERIFIED** | test-h1-h2-h4-e2e.py §8 PASS · 어떤 모델에도 cap 추가 가능 |
| **H4** | AiChoice enum (7) ↔ route.py MODELS (8) 불일치 · 모델 추가 시 두 곳 수정 | ① route.py 하드코딩 리스트 제거 (`list_models` 참조) ② router.py `registry_preferred()` 추가 · `_registry_resolve()` 어댑터 ③ Registry 결과로 preferred 승격 가능 ④ fallback_chain Registry 기반 재구성 | **PARTIAL** | ✅ route.py 리스트 제거 (test §5 PASS) · ✅ 모든 active 모델 enum resolve 커버 (test §4 · 14/14 PASS) · ✅ fallback_chain 전수 registered (test §7 · 27/27 PASS) · ⚠ AiChoice enum 멤버 자체는 호환 유지 (완전 교체는 외부 호출자 깨짐 위험 — scaffold) |
| **H5** | Classifier 재감사 요청 | 재검토 결과 설계상 결함 아님 | **NOT_A_DEFECT** | docs/HARDCODING_AUDIT_2026-10-28.md § 재감사 |
| **H6** | verify-patterns 단일 프레임워크 | 다중 프레임워크 지원 (pytest/junit/mocha/etc) | **VERIFIED** | commit 3383862 테스트 17/17 PASS |
| **H7** | verify-patterns negative test X | negative=regex 승격 + "0 failed" 제외 | **VERIFIED** | commit 3383862 테스트 17/17 PASS |

## 중앙 Registry (ai-registry.yaml) 성숙도

| 항목 | 상태 | 비고 |
|---|---|---|
| 모델 등록 (14 active + 2 provisional) | **VERIFIED** | `list_models()` 전수 반환 |
| `tier` 분류 (default/fallback/balanced/fast_verify/long_context/external_coder/mythos_class 등) | **VERIFIED** | `select_by_tier()` 작동 |
| `budget_cap_pct` 특수 분기 속성화 | **VERIFIED** | fable/mythos cap 적용 (test §8) |
| `routing_thresholds` (small/medium/large/recall) | **VERIFIED** | Router Step 3 참조 |
| `thinking_budget` (low/medium/high/xhigh/mythos) | **VERIFIED** | Router Step 3·4 참조 |
| `classifier` 임계값 | **VERIFIED** | classify-task.py 참조 (commit 3383862) |
| `verified_from` · `verified_at` · `verification_method` | **IMPLEMENTED** | 14 active 모두 docs_only 근거 명시 (2026-10-29) |
| `api_id` (표시명 ≠ 실 API ID 구분) | **IMPLEMENTED** | 14 active + 2 provisional 모두 명시 |
| 실제 API 호출 가용성 검증 (Models API) | **BLOCKED** | API key 미설정 세션 · docs 근거만 |

## 모델별 가용성 분류 (2026-10-29)

| 모델 | availability | verification_method | blocked_reason |
|---|---|---|---|
| claude-opus-5-5 | active | docs_only | — |
| claude-opus-5 | active | docs_only | — |
| claude-opus-4-8 | active | docs_only | — |
| claude-opus-4-7 | active | docs_only | — |
| claude-fable-5-1 | active | docs_only | — |
| claude-fable-5 | active | docs_only | — |
| claude-mythos-5-1 | active | docs_only | access-gated · 30-day retention |
| claude-sonnet-5-5 | active | docs_only | — |
| claude-sonnet-5 | active | docs_only | — |
| claude-sonnet-4-6 | active | docs_only | — |
| claude-haiku-5-5 | active | docs_only | breaking: temp/top_p 미지원 |
| claude-haiku-4-5 | active | docs_only | — |
| codex | active | cli_installed | — |
| gemini | active | cli_installed | — |
| **grok** | **provisional** | docs_only | xAI API key 미설정 — Models API 실호출 BLOCKED |
| **gpt-5.2** | **provisional** | docs_only | OpenAI API key 미설정 — Models API 실호출 BLOCKED |

## MEDIUM/LOW 재분류 (사용자 지적 반영)

**원 보고 "23건"** 은 추상적 집계. 실제 리스트 항목 **8건**. 각 항목을 **결함 / 설계상 / 재분류** 로 재분류:

| # | 원 지적 | 재분류 | 사유 |
|---|---|---|---|
| 1 | window_s=10 (중복 감지) | **설계상 (keep)** | ledger F2AE4D5 커밋에서 "10s 윈도우 + content_hash" 로 설계 확정 · "메시지 ID 없음" 은 모든 LLM 공통 제약 |
| 2 | 60/200자 분류 경계 (다국어 미흡) | **결함 → MEDIUM** | 한국어 토큰 분포 왜곡 · 다음 세션 `classify-task.py` 토큰 기반 전환 (글자수 X) |
| 3 | max_retry=3 (근거 없음) | **설계상 (keep)** | 지수 backoff 상한 · industry standard · 재시도 비용 vs 성공률 trade-off |
| 4 | STALE_SEC = 6h 고정 | **결함 → LOW** | artifact-freshness-check.md 유통기한 매트릭스에 통합 가능 · 다음 세션 |
| 5 | technology discovery SEED_DOMAINS 20개 | **설계상 (keep)** | seed 는 bootstrap 용 · 자동 확장은 WebSearch 통합 별도 feature (R42) |
| 6 | workflow 8 YAML (9-chain 문서 불일치) | **결함 → MEDIUM** | 문서-구현 drift · docs 또는 yaml 중 하나 교정 |
| 7 | max_hops=10 workflow depth | **설계상 (keep)** | 재귀 폭증 방지 안전 상한 · 운영 안전 |
| 8 | Agent 분산 (중앙 registry 없음) | **결함 → MEDIUM** | agents/* 와 plugin/agents/* 통합 등록 · R41 과 연계 (실행 큐 통합) |

**결론**: 23건 추상 집계 → 실 **MEDIUM 결함 3건 (#2, #6, #8)** + **LOW 결함 1건 (#4)** + **설계상 keep 4건 (#1, #3, #5, #7)**.

### 다음 세션 처리 우선순위

1. **#2 다국어 분류 임계값** — `classify-task.py` 가 이미 `ai_registry.get_classifier_threshold` 참조. YAML 안 `implement_small_tokens` 가 토큰 기반이지만 호출부가 글자수로 변환? 재확인 필요.
2. **#8 Agent 중앙 Registry** — R41 (9영역 ↔ Agent/Skills 매핑) 과 통합.
3. **#6 Workflow 문서-구현 drift** — docs/2026-04-19/로드맵.md vs plugins/exec_orch/workflows/.
4. **#4 STALE_SEC** — artifact-freshness-check.md 유통기한 매트릭스 통합.

## 종단 테스트 결과 (2026-10-29)

**`.claude/scripts/test-h1-h2-h4-e2e.py`**:
- 9 섹션 · 68 체크 · **68 PASS / 0 FAIL**
- 특정 모델명·숫자 하드코딩 assert 없음 (Registry 변경에 반응)
- 설정 손상 시뮬레이션 (`_CACHE = {}`) 에도 Router 는 fail-closed enum fallback 로 작동

## 보완 필요 (BLOCKED/scaffold)

| 항목 | 상태 | 해제 조건 |
|---|---|---|
| grok · gpt-5.2 실 API 호출 검증 | BLOCKED | xAI · OpenAI API key 환경 설정 후 `models.list()` 호출 |
| AiChoice enum 완전 제거 (완전 중앙화) | SCAFFOLD | 모든 호출자 (orchestrator, hook, skill) 를 string API ID 로 전환하는 큰 리팩터링 — 사용자 명시 승인 후 별도 세션 |
| classify-task 다국어 토큰 기반 | 미착수 | 다음 세션 R? |
| Workflow 9-chain docs/yaml 일치 | 미착수 | 다음 세션 |

## 관련

- `docs/HARDCODING_AUDIT_2026-10-28.md` (원 감사)
- `.claude/config/ai-registry.yaml` (중앙 Registry)
- `.claude/scripts/lib/ai_registry.py` (helper)
- `.claude/scripts/lib/router.py` (라우팅)
- `.claude/scripts/route.py` (CLI)
- `.claude/scripts/test-h1-h2-h4-e2e.py` (종단 검증 · 68/68 PASS)
- `.claude/rules/operating-principles.md` § 6 완료 증명 · § 9 미측정 ≠ 정상
