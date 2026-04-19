# design_pdf — PDF 생성·양식·서명·암호화 (mcp_docs 는 파싱만)

> **Prefix**: `design_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2

## ⚠️ 현재 상태

**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.

## 📋 커맨드

- `/pdf-generate` ⭐ 기본 — HTML·Markdown → PDF 변환
- `/pdf-fill` — 양식(form) 자동 채우기
- `/pdf-sign` — 전자서명·직인 삽입
- `/pdf-secure` — 암호화·워터마크

## 🧠 스킬

- `skill-pdf-form` — PDF 양식 필드 매핑·검증
- `skill-pdf-compliance` — 전자서명 법적 요건 (전자서명법)

## 🔗 의존성

- **플러그인**: `exec_orch`
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env)

## 📝 참조

- 스펙: `SPEC.md`
- 로드맵: `docs/2026-04-19/로드맵.md`
