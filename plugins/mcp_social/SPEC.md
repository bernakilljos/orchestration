# mcp_social — 상세 스펙 (Phase 1~3 로드맵)

> **상태**: spec-only (Phase 1: YouTube) — 이 플러그인은 킷에 스펙만 있음. 실구현은 install 후 플랫폼에서.

## 목표

- 소셜 플랫폼 MCP — YouTube·Instagram·TikTok·X·Naver·Tistory
- **Phase 1 (현재)**: YouTube Data API v3 스펙 정의
- **Phase 2 (2026-05)**: Instagram·TikTok·X 추가 예정
- **Phase 3 (2026-06)**: Naver·Tistory 한국 플랫폼 추가 예정

## 커맨드 스펙 (Phase 1)

### `/install [platform]`

소셜 플랫폼 선택 설치

**옵션 (예정)**: `youtube` (Phase 1), `instagram` (Phase 2), `tiktok` (Phase 2), `x` (Phase 2), `naver` (Phase 3), `tistory` (Phase 3)

**Phase 1 구현**:
```bash
# YouTube Data API v3 설치
npm install googleapis

# 또는 커뮤니티 MCP
# claude mcp add youtube-mcp -s user -- npx ...
```

**환경변수**:
```
YOUTUBE_API_KEY=<YOUR_KEY>
YOUTUBE_CLIENT_ID=<YOUR_CLIENT_ID>
YOUTUBE_CLIENT_SECRET=<YOUR_SECRET>
YOUTUBE_REDIRECT_URI=http://localhost:3000/callback
```

### `/auth [platform]`

OAuth 2.0 인증 플로우 (토큰 자동 갱신)

**Phase 1 YouTube**:
```bash
/auth youtube
# → OAuth 로그인 링크 생성
# → 브라우저 인증 후 refresh token 저장
# → .env 또는 secure storage 에 저장
```

**공통 사항**:
- 토큰 만료 시 자동 갱신
- refresh token 보안 저장 (`.env.local` 또는 credential manager)
- 인증 상태 persist (`.state/<platform>-token.json`)

### `/status [platform]`

API 쿼터·토큰 만료일 체크

**Phase 1 YouTube**:
```bash
/status youtube
# 결과:
# - API Quota: 10,000 requests/day (used: 234, remaining: 9766)
# - Token expires: 2026-05-23 14:30:00 UTC
# - Last synced: 2026-04-23 08:15:22 UTC
```

## MCP 상태 조사 (Phase 계획)

### Phase 1: YouTube
- **상태**: ✅ Google Data API v3 공식 지원
- **라이브러리**: `googleapis@^136.0.0`
- **인증**: OAuth 2.0 (refresh token 기반)
- **Quota**: 10,000 requests/day (기본)
- **MCP 가능성**: Google 공식 MCP 확인 중

### Phase 2: Instagram
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `instagram-api` (비공식) 또는 Instagram Graph API 직접 호출
- **인증**: OAuth 2.0 (Facebook Business 필요)
- **제한**: 국가별 정책 (한국 제약 가능성)

### Phase 2: TikTok
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: TikTok API (제한적 access) 또는 playwright 크롤링
- **인증**: API Key + Secret (개발자 신청 필요)
- **제한**: Rate limit 매우 낮음 (개발자 tier)

### Phase 2: X (Twitter)
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `tweepy@^4.0`, `twitter-api-v2` 또는 X API v2 직접 호출
- **인증**: Bearer Token (OAuth 2.0 또는 API Key)
- **제한**: Post/Like 권한 유료 (Academic/Pro tier)

### Phase 3: Naver
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `naver-api` (커뮤니티) 또는 REST API 직접 호출
- **인증**: OAuth 또는 API Key (블로그·카페·지도)
- **지원**: 블로그, 카페, 지도, 웨일

### Phase 3: Tistory
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: Tistory API (공식 REST API)
- **인증**: OAuth 2.0 (Tistory 플랫폼 필요)
- **지원**: 블로그 포스트 CRUD, 카테고리, 댓글

## 구현 체크리스트 (플랫폼 install 후)

- [ ] 멱등성 (재실행 안전, 중복 업로드 없음)
- [ ] `--dry-run` 옵션 지원
- [ ] 인증 토큰 갱신 (OAuth refresh_token)
- [ ] Rate limit 대응 (지수백오프, 재시도)
- [ ] 에러 복구 (state 파일 기반, interrupted 작업 재개)
- [ ] 시크릿 관리 (`.env`: YOUTUBE_API_KEY, INSTAGRAM_TOKEN 등)
- [ ] 비용 관측 (API 쿼터 로깅, 월 비용 추정)
- [ ] JSON 구조화 로그 (타임스탐프, level, message, metadata)

## 데이터 스키마 (예상)

### YouTube Upload 응답
```json
{
  "videoId": "dQw4w9WgXcQ",
  "title": "Sample Video",
  "description": "Sample Description",
  "status": "UPLOADED|PROCESSING|READY|FAILED",
  "uploadedAt": "2026-04-23T08:15:22Z",
  "quota_used": 1234,
  "quota_remaining": 8766
}
```

## 의존성

- **필수 플러그인**: `exec_orch`
- **공통 헬퍼**: `.claude/scripts/common.sh` (dry-run, env 로드, 로깅)
- **구현 선택사항** (설치 후 플랫폼):
  - YouTube: `googleapis@^136.0.0`
  - Instagram: `instagram-api` (커뮤니티) 또는 Graph API
  - TikTok: TikTok API (제한적) 또는 `playwright` 크롤링
  - X: `tweepy@^4.0` 또는 `twitter-api-v2`
  - Naver: REST API 직접 호출
  - Tistory: Tistory API (공식)

## 다음 단계 (Phase 진입 조건)

**Phase 2 진입 (2026-05)**:
1. Phase 1 (YouTube) 구현 완료 및 테스트
2. Instagram·TikTok·X 공식 또는 커뮤니티 MCP 조사 완료
3. 각 플랫폼별 OAuth 인증 흐름 설계

**Phase 3 진입 (2026-06)**:
1. Phase 2 완료
2. 한국 플랫폼 (Naver·Tistory) API 문서 검토
3. 멀티 언어 지원 (한글 메타데이터)

## 참조

- 로드맵: `docs/2026-04-19/로드맵.md` § Phase 1~3
- YouTube API: `https://developers.google.com/youtube/v3`
- 의존 플러그인: `plugins/exec_orch`
- 공식 MCP: `modelcontextprotocol.io`
- Anthropic 스킬 가이드: `.claude/rules/skill-design.md`

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 인증 실패 | 잘못된 API Key 또는 OAuthToken | `.env` 재확인, 토큰 갱신 |
| Rate limit 도달 | API 호출 과다 | 지수백오프 확인, quota 사용량 모니터링 |
| 토큰 만료 | refresh token 만료 | `/auth youtube` 로 재인증 |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 확인 |
| 드라이런 실패 | `--dry-run` 미지원 | `is_dry_run "$@"` 헬퍼 추가
