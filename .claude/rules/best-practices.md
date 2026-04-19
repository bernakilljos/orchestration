# Best Practices — Claude Code 프로젝트

> **출처**: docs/upgrade § 이미지 6 (Brij Kishore Pandey)

## 반복 개발 (Iterative Development)
- 작게 시작, 확인 후 확장 (no big-bang)
- 실패 빠르게 (fail fast) — 드라이런 활용
- Git 워크플로우 (feature branch → PR → merge)

## 명확한 Git 흐름
- commit 메시지: `feat/fix/refactor/docs/chore` 접두사
- PR 단위 작게, 리뷰 가능한 수준
- 커밋 전 검증: `validate-plugin-schema.py` + `check-agents`

## 모듈식 설계
- 단일 책임 (한 플러그인 = 한 목적)
- 플러그인 간 느슨한 결합 (dependencies 명시적)
- 공유 로직 → `.claude/rules/`, 공통 헬퍼 → `scripts/common.sh`

## 정기 테스트·감사
- 주 1회: `bash .claude/scripts/sync-plugins.sh --check` (드리프트·orphan)
- 주 1회: `python .claude/scripts/validate-plugin-schema.py --strict`
- 월 1회: CLAUDE.md + guide.txt 갱신
- 월 1회: 로드맵 리뷰 (Phase 이동 여부)

## Extended Thinking 활용 (Claude 4.x)
- 복잡한 아키텍처 결정 시: 긴 추론 모드 활성화
- 트레이드오프 비교 시: Extended Thinking 로 깊이 있는 분석
- 단순 구현 시: 빠른 모드 (Sonnet)

## 1M Token Window 활용
- 대용량 리팩토링: 프로젝트 전체 컨텍스트 로드 가능
- 코드리뷰: 여러 파일 동시 비교
- 단순 작업: 굳이 1M 불필요 — 비용 효율 고려

## Artifacts / Skills / Plugins / Commands 구분

| 형태 | 용도 | 예시 |
|---|---|---|
| **Artifact** | 한 번 생성되는 산출물 | PPT, 코드 파일, HTML |
| **Skill** | 자동 활성화되는 추론 로직 | `skill-rag-patterns`, `skill-arch-selector` |
| **Command** | 사용자가 명시적 호출 | `/check`, `/excel-make` |
| **Plugin** | 위 3가지를 묶은 단위 | `plugins/ai_rag/`, `plugins/bundles_cowork/` |

## 시크릿 관리
- `.env` 로드 (`scripts/common.sh load_env`)
- 절대 하드코딩 금지
- `.env` 는 gitignore

## 참조

- `.claude/rules/plugin-structure.md` — 플러그인 구조
- `.claude/rules/sync-workflow.md` — sync 플로우
- `docs/architecture-patterns.md` — 설계 원칙 9가지
