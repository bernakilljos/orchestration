# mcp_social — 소셜 플랫폼 MCP — YouTube·Instagram·TikTok·X·Naver·Tistory (Phase 1: YouTube 한정)

> **Status**: spec-only (Phase 1) | **Prefix**: `mcp_` | **버전**: 0.1 | **현황**: YouTube API v3 스펙만 완료

## ⚠️ 현재 상태

**spec-only** — 이 플러그인은 킷에 **스펙만** 있습니다. 실제 구현은 설치 후 플랫폼에서 진행.

공식/커뮤니티 MCP:
- ✅ **YouTube** — Google Data API v3 (토큰 기반) — `@google/youtube-mcp` (찾아볼 예정)
- ❌ **Instagram** — 공식 MCP 없음 → Instagram Graph API 직접 호출 또는 playwright 기반
- ❌ **TikTok** — 공식 MCP 없음 → TikTok API (제한적) 또는 커뮤니티 크롤러
- ❌ **X (Twitter)** — 공식 MCP 없음 → X API v2 직접 호출
- ❌ **Naver** — 공식 MCP 없음 → Naver API (블로그·카페) 직접 호출
- ❌ **Tistory** — 공식 MCP 없음 → Tistory API 직접 호출

## 📋 커맨드 (예정)

- `/install` — 소셜 플랫폼 선택 설치 (Phase 1: YouTube)
- `/auth` — OAuth 2.0 인증 플로우 (토큰 자동 갱신)
- `/status` — API 쿼터·토큰 만료일 체크

## 🔗 의존성

- **플러그인**: `exec_orch` (필수)
- **구현 시 선택**: `googleapis` (YouTube), instagram-api, tweepy (X), naver-api, tistory-api

## 📝 다음 단계

1. **Phase 1 (YouTube)** — 공식 MCP 또는 googleapis 라이브러리 활용
2. **Phase 2** — Instagram·TikTok·X 추가 (2026-05 예정)
3. **Phase 3** — 한국 플랫폼 (Naver·Tistory) 추가 (2026-06 예정)

상세 스펙: [`SPEC.md`](SPEC.md)

## 📚 참조

- 로드맵: `docs/2026-04-19/로드맵.md` § Phase 1~3
- YouTube API: `https://developers.google.com/youtube/v3`
- 공식 MCP: `modelcontextprotocol.io`
