# Architecture Patterns — 설계 원칙 9가지

> **목적**: 이 킷의 핵심 설계 결정을 박제. 새 플러그인·기능 추가 시 이 원칙 위반 금지.
> **영감**: CMDS (cmds-system-files) 의 Architecture Patterns 패턴 + 본 프로젝트 자체 학습.

---

## 1. Source of Truth (단방향 동기화)

- `plugins/` 가 원본, `.claude/` 는 sync 결과물
- 편집은 `plugins/` 에서만. `.claude/` 직접 수정 시 다음 sync 에서 덮어씀
- sync 스크립트: `.claude/scripts/sync-plugins.sh`
- 검증: orphan·drift 자동 탐지 (종료 코드 2)

## 2. Prefix 네임스페이스

- 모든 플러그인은 `<prefix>_<feature>` 명명
- prefix 등록 위치: `.claude-plugin/plugin.json` § `prefix_convention`
- 커맨드·스킬 충돌은 rename map 으로 해결 (`install.md` → `mcp_dev-install.md`)

## 3. Phase 기반 성숙도

| Phase | 의미 | 예시 |
|---|---|---|
| 0 | 완성·운영 중 | 현재 14개 플러그인 |
| 1 | 실구현 대상 스펙 | exec_scheduler, mcp_social, cost_youtube |
| 2 | 설계 대기 | cost_instagram, perf_monitor ... |
| 3 | 아이디어 | ai_, sec_, infra_ 계열 |

`plugin.json.phase` + `status` 조합으로 플러그인 생애주기 표현.

## 4. Status = 가시성 + 품질 보증

- `stable` — 운영 가능, 실제 동작 코드 있음
- `experimental` — 동작하나 인터페이스 변경 가능
- `spec-only` — 스펙만. 실구현은 플랫폼에서
- `deprecated` — 제거 예정. 대체재 안내 필수

## 5. Dependencies 명시 + 위상정렬

- `plugin.json.dependencies.plugins` 배열로 의존 선언
- `resolve-plugin-order.py` 가 위상정렬 → sync 순서 결정
- 순환 의존 금지 (스크립트가 경고)

## 6. Precedence (파일 충돌 해결 우선순위)

- 같은 정보가 여러 파일에 있을 때 누가 이기는가
- `plugin.json.metadata.precedence` (정수, 낮을수록 우선)
- 기본값: 플러그인 수준 10, 코어(`exec_orch`) 수준 1

예: CLAUDE.md (precedence 1) > `.claude/rules/*.md` (5) > plugin README (10)

## 7. Token Estimate (비용 관측)

- `plugin.json.metadata.token_estimate` — 플러그인 전체 로드 시 대략 토큰 수
- 세션 시작 시 어떤 플러그인을 우선 로드할지 판단 기준
- Claude Code 가 자동 컨텍스트 압축 시 낮은 가치/높은 비용 플러그인부터 제외

## 8. Entry Points (진입점 명확화)

- `plugin.json.entry_points.default_command` — 인자 없이 호출 시 기본 동작
- `plugin.json.entry_points.core_skills` — 이 플러그인 핵심 스킬 (자동 로드 우선)
- 루트 `.claude-plugin/plugin.json.entry_points` 에 킷 전역 진입점 (session_start, task_route 등)

## 9. Shared Rules (횡단 관심사 분리)

- `.claude/rules/*.md` — 여러 플러그인이 따르는 공통 규칙
- 현재: `indentation`, `frontmatter`, `file-naming`, `plugin-structure`, `sync-workflow`
- 각 플러그인 README 에서 필요한 규칙 링크 (CMDS 의 `@include` 개념 경량화 버전)

---

## 이 원칙이 보호하는 것

- **스코프 폭주 방지** — precedence·phase·status 로 "지금 할 것 vs 나중"
- **충돌 무재화** — prefix + rename map + dependencies 위상정렬
- **비용 관측** — token_estimate 로 세션 시작 시 로드 비용 가시화
- **유지보수성** — shared rules 로 중복 제거, SoT 규칙으로 드리프트 방지

## 이 원칙이 *하지 않는* 것

- **런타임 동작 보장** — 스펙만 정의, 실행 환경은 플랫폼에서
- **CMDS `@include` 메커니즘** — 런타임 include 안 함 (sync 로 충분)
- **STATIC/DYNAMIC 캐시 섹션 구분** — 과한 최적화 (이 킷 규모에서 불필요)
- **`memory-type` 분류** — Claude Code auto memory 시스템이 이미 담당

## 참조

- `.claude/rules/` — 실제 규칙 파일
- `.claude-plugin/plugin.json` — 킷 전역 메타
- `.claude-plugin/plugin-schema.json` — plugin.json JSON Schema
- `docs/2026-04-19/로드맵.md` — Phase 1~3 계획
