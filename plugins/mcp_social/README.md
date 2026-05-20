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

## 상세 스펙

### 목표

- 소셜 플랫폼 MCP — YouTube·Instagram·TikTok·X·Naver·Tistory
- **Phase 1 (현재)**: YouTube Data API v3 스펙 정의
- **Phase 2 (2026-05)**: Instagram·TikTok·X 추가 예정
- **Phase 3 (2026-06)**: Naver·Tistory 한국 플랫폼 추가 예정

### 환경변수 (Phase 1 YouTube)

```text
YOUTUBE_API_KEY=<YOUR_KEY>
YOUTUBE_CLIENT_ID=<YOUR_CLIENT_ID>
YOUTUBE_CLIENT_SECRET=<YOUR_SECRET>
YOUTUBE_REDIRECT_URI=http://localhost:3000/callback
```

### MCP 상태 조회 (Phase 계획)

#### Phase 1: YouTube
- **상태**: ✅ Google Data API v3 공식 지원
- **라이브러리**: `googleapis@^136.0.0`
- **인증**: OAuth 2.0 (refresh token 기반)
- **Quota**: 10,000 requests/day (기본)
- **MCP 가능성**: Google 공식 MCP 확인 중

#### Phase 2: Instagram
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `instagram-api` (비공식) 또는 Instagram Graph API 직접 호출
- **인증**: OAuth 2.0 (Facebook Business 필요)
- **제한**: 국가별 정책 (한국 제약 가능성)

#### Phase 2: TikTok
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: TikTok API (제한적 access) 또는 playwright 크롤링
- **인증**: API Key + Secret (개발자 신청 필요)
- **제한**: Rate limit 매우 낮음 (개발자 tier)

#### Phase 2: X (Twitter)
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `tweepy@^4.0`, `twitter-api-v2` 또는 X API v2 직접 호출
- **인증**: Bearer Token (OAuth 2.0 또는 API Key)
- **제한**: Post/Like 권한 유료 (Academic/Pro tier)

#### Phase 3: Naver
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: `naver-api` (커뮤니티) 또는 REST API 직접 호출
- **인증**: OAuth 또는 API Key (블로그·카페·지도)
- **지원**: 블로그, 카페, 지도, 웨일

#### Phase 3: Tistory
- **상태**: ❌ 공식 MCP 없음
- **라이브러리**: Tistory API (공식 REST API)
- **인증**: OAuth 2.0 (Tistory 플랫폼 필요)
- **지원**: 블로그 포스트 CRUD, 카테고리, 댓글

### 구현 체크리스트 (플랫폼 install 후)

- [ ] 멱등성 (재실행 안전, 중복 업로드 없음)
- [ ] `--dry-run` 옵션 지원
- [ ] 인증 토큰 갱신 (OAuth refresh_token)
- [ ] Rate limit 대응 (지수백오프, 재시도)
- [ ] 에러 복구 (state 파일 기반, interrupted 작업 재개)
- [ ] 시크릿 관리 (`.env`: YOUTUBE_API_KEY, INSTAGRAM_TOKEN 등)
- [ ] 비용 관측 (API 쿼터 로깅, 월 비용 추정)
- [ ] JSON 구조화 로그 (타임스탐프, level, message, metadata)

### 데이터 스키마 (예상)

#### YouTube Upload 응답
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

### 다음 단계 (Phase 진입 조건)

**Phase 2 진입 (2026-05)**:
1. Phase 1 (YouTube) 구현 완료 및 테스트
2. Instagram·TikTok·X 공식 또는 커뮤니티 MCP 조사 완료
3. 각 플랫폼별 OAuth 인증 흐름 설계

**Phase 3 진입 (2026-06)**:
1. Phase 2 완료
2. 한국 플랫폼 (Naver·Tistory) API 문서 검토
3. 멀티 언어 지원 (한글 메타데이터)

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 인증 실패 | 잘못된 API Key 또는 OAuthToken | `.env` 재확인, 토큰 갱신 |
| Rate limit 도달 | API 호출 과다 | 지수백오프 확인, quota 사용량 모니터링 |
| 토큰 만료 | refresh token 만료 | `/auth youtube` 로 재인증 |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 확인 |
| 드라이런 실패 | `--dry-run` 미지원 | `is_dry_run "$@"` 헬퍼 추가 |

## 📚 참조

- 로드맵: `docs/2026-04-19/로드맵.md` § Phase 1~3
- YouTube API: `https://developers.google.com/youtube/v3`
- 공식 MCP: `modelcontextprotocol.io`
- `.claude/rules/skill-design.md` (Anthropic 스킬 표준)
- `.claude/rules/plugin-structure.md`
