# Migration Map — Old → New (Plugin-Centric Restructure)

> 작성일: 2026-04-15  
> 버전: v2.x → v3.0 (plugin-centric)

## 개요

기존 `.claude/` 자산을 plugin-centric 구조로 재정리한 내역.
기존 파일은 **레거시 alias**로 유지되며 삭제하지 않는다.
신규 파일은 접두사 규칙(`exec_`, `design_`, `review_`, `route_`, `state_`, `hook_`)을 따른다.

---

## 1. 신규 파일 (이번 마이그레이션에서 생성)

| 신규 파일 | 역할 | 통합/승격된 레거시 |
|----------|------|-----------------|
| `.claude-plugin/plugin.json` | 플러그인 메타데이터 + 진입점 선언 | 신규 |
| `.claude-plugin/docs/migration-map.md` | 이 문서 | 신규 |
| `.claude/hooks/hooks.json` | 훅 등록 manifest | `.claude/settings.json` hooks 섹션 |
| `.claude/state/.gitkeep` | 상태 디렉터리 (신규) | 신규 |
| `.claude/state/README.md` | 상태 파일 가이드 | 신규 |
| `.claude/skills/exec_orca-auto.md` | Orca 워커 관리 (START/STOP/STATUS) | `/orcauto-start`, `/orcauto-stop` command 로직 |
| `.claude/skills/state_session.md` | 세션 상태 관리 (SNAPSHOT/RESTORE/STATUS) | `skill-09-memory-reset` + `check-agents` command 로직 |
| `.claude/skills/route_dispatch.md` | AI 라우팅·판단 (자동 감지) | (구 `vibe-loop` 로직 흡수, 2026-04-19 command 제거) + CLAUDE.md Multi-Agent Auto-Detection |

---

## 2. Command Wrapper 슬림화 (로직 제거 → skill 참조)

| Command | 변경 전 | 변경 후 | 참조 Skill |
|---------|--------|--------|-----------|
| `/orcauto-start` | 직접 실행 로직 포함 (7단계) | wrapper (3줄) | `exec_orca-auto` · START |
| `/orcauto-stop` | 직접 실행 로직 포함 (4단계) | wrapper (3줄) | `exec_orca-auto` · STOP |
| ~~`/vibe-loop`~~ | 직접 판단 로직 포함 | **삭제됨 (2026-04-19)** — 세션 시작 시 `exec_orca-auto` 자동 실행으로 불필요 | — |
| `/check-agents` | 직접 상태 조회 로직 포함 | wrapper (3줄) | `state_session` · STATUS |

---

## 3. 기존 Skills 매핑 (레거시 → 권장 신명칭)

현재 `.claude/skills/skill-NN-*.md` 파일은 **유지됨**.  
아래는 향후 전체 마이그레이션 시 권장하는 새 이름 체계.

| 기존 파일 | 권장 신명칭 | 분류 접두사 |
|----------|-----------|-----------|
| `skill-01-research.md` | `exec_research.md` | `exec_` |
| `skill-02-implement.md` | `exec_implement.md` | `exec_` |
| `skill-03-review.md` | `review_code.md` | `review_` |
| `skill-04-context-summary.md` | `exec_context-summary.md` | `exec_` |
| `skill-05-deploy.md` | `exec_deploy.md` | `exec_` |
| `skill-06-test.md` | `exec_test.md` | `exec_` |
| `skill-07-rollback.md` | `exec_rollback.md` | `exec_` |
| `skill-08-design.md` | `design_ui.md` | `design_` |
| `skill-09-memory-reset.md` | `state_memory-reset.md` | `state_` (→ `state_session`으로 통합) |
| `skill-10-quality-verify.md` | `review_quality.md` | `review_` |
| `skill-11-personas.md` | `route_personas.md` | `route_` |
| `skill-12-domain-detect.md` | `route_domain-detect.md` | `route_` |
| `skill-13-parallel-dispatch.md` | `exec_parallel-dispatch.md` | `exec_` |
| `skill-14-auto-detail.md` | `route_auto-detail.md` | `route_` |
| `skill-15-theme-factory.md` | `design_theme.md` | `design_` |
| `skill-16-brand-guidelines.md` | `design_brand.md` | `design_` |
| `skill-17-debugging-canvas.md` | `review_debug.md` | `review_` |
| `skill-18-web-artifacts.md` | `exec_web-artifacts.md` | `exec_` |
| `skill-19-skill-creator.md` | `exec_skill-creator.md` | `exec_` |
| `skill-20-claude-seo.md` | `exec_seo.md` | `exec_` |
| `skill-21-marketing.md` | `exec_marketing.md` | `exec_` |
| `skill-22-remotion.md` | `exec_remotion.md` | `exec_` |
| `skill-23-owasp-security.md` | `review_security.md` | `review_` |
| `skill-24-ai-handoff.md` | `exec_ai-handoff.md` | `exec_` |
| `skill-25-media-enhance.md` | `exec_media-enhance.md` | `exec_` |
| `skill-26-file-protection.md` | `hook_file-protection.md` | `hook_` |
| `skill-27-mandatory-verify.md` | `review_mandatory-verify.md` | `review_` |
| `skill-28-changelog.md` | `exec_changelog.md` | `exec_` |
| `skill-29-api-tester.md` | `exec_api-tester.md` | `exec_` |
| `skill-30-docker.md` | `exec_docker.md` | `exec_` |
| `skill-31-i18n.md` | `exec_i18n.md` | `exec_` |
| `skill-32-db-migration.md` | `exec_db-migration.md` | `exec_` |
| `skill-33-github-actions.md` | `exec_github-actions.md` | `exec_` |
| `skill-34-code-docs.md` | `exec_code-docs.md` | `exec_` |
| `skill-35-performance-profiler.md` | `exec_perf-profiler.md` | `exec_` |
| `skill-36-data-viz.md` | `exec_data-viz.md` | `exec_` |
| `skill-37-error-tracker.md` | `exec_error-tracker.md` | `exec_` |
| `skill-38-token-watchdog.md` | `state_token-watchdog.md` | `state_` |

---

## 4. 기존 Agents 매핑 (레거시 → 권장 신명칭)

| 기존 파일 | 권장 신명칭 | 역할 분류 |
|----------|-----------|---------|
| `agent-01-team-lead.md` | `route_team-lead.md` | `route_` (설계/판단) |
| `agent-02-implementer.md` | `exec_implementer.md` | `exec_` (구현) |
| `agent-03-reviewer.md` | `review_reviewer.md` | `review_` (검증) |
| `agent-04-architect.md` | `route_architect.md` | `route_` (아키텍처) |
| `agent-05-monitor.md` | `exec_monitor.md` | `exec_` (모니터링) |
| `agent-06-designer.md` | `design_designer.md` | `design_` (디자인) |

---

## 5. 상태 파일 위치

| 파일 | 현재 위치 | 향후 이동 계획 |
|------|---------|------------|
| `orca-enabled` | `.claude/` 루트 | `.claude/state/` (미래) |
| `orca-stopped` | `.claude/` 루트 | `.claude/state/` (미래) |
| `orca-heartbeat` | `.claude/` 루트 | `.claude/state/` (미래) |
| `orca-workers` | `.claude/` 루트 | `.claude/state/` (미래) |
| `retry-count.json` | `.claude/state/` (신규) | — |
| `worker-status.json` | `.claude/state/` (신규) | — |

이동 시 CLAUDE.md + exec_orca-auto.md + command 파일의 경로 참조 일괄 업데이트 필요.

---

## 6. 접두사 규칙 요약

| 접두사 | 용도 | 예시 |
|-------|------|------|
| `exec_` | 실행 계열 (구현, 배포, 테스트 등) | `exec_deploy.md`, `exec_test.md` |
| `design_` | 디자인/PPT/UI 계열 | `design_theme.md`, `design_brand.md` |
| `review_` | 검증/리뷰/보안 계열 | `review_code.md`, `review_security.md` |
| `route_` | 라우팅/판단/도메인 감지 | `route_dispatch.md`, `route_team-lead.md` |
| `state_` | 상태 저장/복구/감시 | `state_session.md`, `state_token-watchdog.md` |
| `hook_` | 훅 관련 (파일 보호 등) | `hook_file-protection.md` |

---

## 7. 깨질 수 있는 부분 & 수동 확인 포인트

| 위험 | 원인 | 확인 방법 | 대처 |
|------|------|---------|------|
| `/orcauto-start` 동작 변화 | wrapper → exec_orca-auto.md 참조 | 실행 후 워커 시작 확인 | exec_orca-auto.md START 섹션 검토 |
| `/check-agents` 출력 형식 | state_session.md STATUS로 통합 | 실행 후 표 형식 확인 | state_session.md STATUS 섹션 조정 |
| settings.json hooks 경로 | `.claude/hooks/` 경로 유지됨 | hooks.json은 manifest 전용 | 별도 조치 불필요 |
| orca-* 파일 경로 | `.claude/` 루트에 유지 | 파일 존재 확인 | 이동 시 전체 참조 일괄 수정 |
| CLAUDE.md Loading Order | 신규 3개 파일 추가 | 파일 존재 확인 | 이미 반영됨 |
