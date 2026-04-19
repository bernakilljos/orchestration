# design_video — 영상 편집 — 자막·쇼츠·썸네일 (유튜브 수익화 직결)

> **Prefix**: `design_` | **버전**: 0.1 | **Status**: spec-only | **Phase**: 2

## ⚠️ 현재 상태

**spec-only** — 스펙 + 기본 공통 헬퍼(`scripts/common.sh`) 만 있음. 도메인 로직은 플랫폼에서 구현.

## 📋 커맨드

- `/video-edit` ⭐ 기본 — 영상 편집 (자르기·합치기·자막)
- `/video-subtitle` — 자막 자동 생성 (Whisper + 번역)
- `/video-template` — 유튜브 인트로·아웃트로 템플릿
- `/video-shorts` — 롱폼 → 쇼츠 자동 추출
- `/video-thumbnail` — 썸네일 A/B 3안 자동 생성

## 🧠 스킬

- `skill-video-remotion` — Remotion 프로그래매틱 영상 (design_ppt 에서 이관)
- `skill-video-retention` — 시청지속률 높이는 편집 패턴

## 🔗 의존성

- **플러그인**: `exec_orch`, `mcp_media`
- **공통 헬퍼**: `scripts/common.sh` (dry-run·로깅·env)

## 📝 참조

- 스펙: `SPEC.md`
- 로드맵: `docs/2026-04-19/로드맵.md`
