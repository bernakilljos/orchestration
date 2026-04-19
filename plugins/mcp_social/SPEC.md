# mcp_social — 상세 스펙 (Phase 1)

> **Status**: spec-only — 이 플러그인은 킷에 스펙만 있음. 실구현은 install 후 플랫폼에서.

## 목표

- 소셜 플랫폼 MCP — YouTube·Instagram·TikTok·X·Naver·Tistory (Phase 1: YouTube 한정)

## 커맨드 스펙

### `/install`

소셜 MCP 설치 (Phase 1: YouTube Data API v3)

**시그니처 (예정)**:
```
/install [args] [--flag]
```

### `/auth`

OAuth 2.0 인증 플로우 (토큰 자동 갱신)

**시그니처 (예정)**:
```
/auth [args] [--flag]
```

### `/status`

API 쿼터·토큰 만료일 체크

**시그니처 (예정)**:
```
/status [args] [--flag]
```

## 의존성

- **upstream (필수)**: exec_orch

## 구현 가이드라인 (install 후 플랫폼 참조용)

- [ ] 멱등성 보장
- [ ] `--dry-run` 옵션 지원
- [ ] Rate limit 대응 (지수백오프)
- [ ] 에러 복구 (state 파일 기반 재시작)
- [ ] 시크릿 관리 (환경변수·vault)
- [ ] 비용 관측 (토큰·API 호출 로깅)

## 참조

- 로드맵: `docs/2026-04-19/로드맵.md`
- 의존 플러그인: plugins/exec_orch
