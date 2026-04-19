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

## 📝 참조

- 스펙: `SPEC.md`
- 로드맵: `docs/2026-04-19/로드맵.md`
