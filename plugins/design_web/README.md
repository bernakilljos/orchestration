# design_web — 웹사이트·랜딩·블로그 템플릿 자동 생성 (HTML·Tailwind·SEO)

> **Prefix**: `design_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 1

## ⚠️ 현재 상태

**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.

## 📋 커맨드

- `/landing` ⭐ 기본 — 랜딩페이지 자동 생성 (헤드라인·CTA·증명)
- `/blog-template` — 블로그 템플릿 (Tistory·Ghost·Jekyll)
- `/portfolio` — 포트폴리오 사이트 생성
- `/seo-meta` — 메타태그·OG·JSON-LD 자동 삽입

## 🧠 스킬

- `skill-web-seo` — 웹 SEO 최적화 (메타·구조화 데이터·Core Web Vitals)
- `skill-web-conversion` — 전환율 높이는 랜딩 패턴

## 🔗 의존성

- **플러그인**: `exec_orch`
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env)

## 상세 스펙

### 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 📝 참조

- 로드맵: `docs/2026-04-19/로드맵.md`
- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
- `docs/architecture-patterns.md`
- `.claude/rules/file-naming.md`
