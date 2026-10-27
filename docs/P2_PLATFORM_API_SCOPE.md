# P2 · Platform API — Scope 문서 (설계만 · 2026-10-27)

> **근거**: 외부 감사 `docs/ORCHESTRATION_AUDIT_1027.md § F Platform` — multi-tenant·auth·API 미구현.
> **상태**: SCOPE 만 · 실제 구현 X · 다음 세션 (별도 goal) 에서 결정 후 착수.
> **왜 지금 구현 X**: 세션 1~2일로 불가 (DB 설계·auth·multi-tenant·외부 노출·OAuth·과금 전부 필요). 사용자 "빨리 push" 명시 상태에서 큰 신규 설계는 핑퐁 위험.

## 범위 (Change Budget 참고 · NEW 2 상한)

### Phase 1 (MVP · 다음 세션 2~3 턴)
- `plugins/platform_api/` 신규 플러그인
- Flask·FastAPI 중 하나 (저자 결정 · FastAPI 추천 · async·OpenAPI 자동)
- Endpoints:
  - `POST /goal` — 외부 사용자 goal 등록 (API key 인증)
  - `GET /goal/{id}` — 상태 조회
  - `GET /workflow/{chain}` — 체인 메타 (public)
- 저장소: `.claude/state/orca.db` 확장 (`api_tenants` · `api_requests` 테이블)
- 인증: API key (header `X-Api-Key`) · 단순 lookup · multi-tenant X (MVP)
- 배포: 로컬 only (`127.0.0.1:9090`) · 외부 노출 X

### Phase 2 (운영 · 1~2주)
- Multi-tenant (tenant_id 분리 · DB row-level filter)
- OAuth 2.0 (Google·GitHub) 또는 Clerk·Auth0 통합
- Rate limit (per tenant · token bucket)
- Usage tracking (`api_usage` 테이블 · 매 요청 토큰·비용 집계)
- 과금 (Stripe · 월 subscription + usage overage)
- Admin dashboard (`/admin` · super admin)
- 배포 (Fly.io·Railway·Vercel 중 저자 선택)

### Phase 3 (엔터프라이즈 · 3~4주)
- SSO (SAML·Okta)
- Audit log (compliance)
- SLA (99.9% uptime)
- Private deployment (Docker Compose · Kubernetes)
- SOC 2 Type II 준비

## 의존성 (Phase 1 기준)

- Python 3.12+ (`fastapi>=0.115 uvicorn[standard] pydantic>=2.9 python-jose[cryptography]`)
- `.claude/state/orca.db` 확장 (migrate 스크립트 필요)
- Standing Requirement **PLAT-SEC-001** 신규 — API key 저장 시 bcrypt hash · plaintext 저장 금지
- Standing Requirement **PLAT-COST-001** 신규 — tenant 별 월 budget cap (초과 시 429)

## 금지 (설계 단계부터)

1. plaintext API key 저장 X (bcrypt·argon2)
2. tenant 간 데이터 교차 조회 X (row-level filter 강제)
3. 외부 노출 전 OWASP Top 10 scan 통과 X
4. multi-tenant 없이 production 배포 X (단일 tenant = 사실상 단일 사용자 kit · platform 아님)
5. Platform 사용자 데이터를 kit 저자 memory 에 저장 X (data separation)

## 결정 필요 (저자)

- [ ] Framework (FastAPI vs Flask · 추천 FastAPI)
- [ ] Deployment (self-hosted Docker · Fly.io · Railway · AWS Lambda · 저자 선호)
- [ ] Auth provider (API key · Clerk · Auth0 · 자체 JWT)
- [ ] 과금 모델 (free tier · subscription · pay-as-you-go · hybrid)
- [ ] Pricing (per API call · per workflow run · flat monthly)

## 관련

- `docs/ORCHESTRATION_AUDIT_1027.md` (외부 감사 § F)
- `plugins/exec_orch/` (내부 kit · platform 과 분리)
- `.claude/workflows/*.yaml` (P1-A · platform 이 호출할 체인)
- `.claude/rules/execution-contract.md` (Request Ledger · platform 요청에도 적용)
- `.claude/rules/operational-freeze.md` (platform 구현 전 kit FREEZE 유지)
