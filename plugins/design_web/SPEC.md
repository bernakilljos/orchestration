# design_web — 상세 스펙 (Phase 1)

## 목표

- 웹사이트·랜딩·블로그 템플릿 자동 생성 (HTML·Tailwind·SEO)

## 커맨드 스펙

### `/landing`

랜딩페이지 자동 생성 (헤드라인·CTA·증명)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/blog-template`

블로그 템플릿 (Tistory·Ghost·Jekyll)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/portfolio`

포트폴리오 사이트 생성

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/seo-meta`

메타태그·OG·JSON-LD 자동 삽입

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

## 스킬 스펙

### `skill-web-seo`

웹 SEO 최적화 (메타·구조화 데이터·Core Web Vitals)

### `skill-web-conversion`

전환율 높이는 랜딩 패턴

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

## 의존성

- upstream: exec_orch
- 공통 헬퍼: `scripts/common.sh`

## 참조

- `docs/architecture-patterns.md`
- `.claude/rules/file-naming.md`
