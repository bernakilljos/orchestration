---
name: social-platform-integration
description: |
  소셜 플랫폼 MCP 통합 스킬 — YouTube·Instagram·TikTok·X·Naver·Tistory 자동화.
  사용자가 "소셜 미디어", "유튜브 업로드", "인스타 게시", "틱톡", "블로그 포스팅" 등 소셜 플랫폼 관련 요청 시 활성화.
---

# Social Platform Integration Skill

## 트리거
- 소셜 미디어 콘텐츠 게시/관리 요청
- YouTube 영상 업로드/분석
- Instagram 포스트/스토리/릴스
- TikTok 영상 관리
- X(Twitter) 트윗/스레드
- Naver 블로그/카페 포스팅
- Tistory 블로그 포스팅
- 소셜 애널리틱스 조회

## 플랫폼별 MCP 도구

### YouTube (Phase 1 — 활성)
| 기능 | MCP 도구 | 설명 |
|---|---|---|
| 영상 업로드 | YouTube Data API v3 | 제목·설명·태그·썸네일 |
| 분석 | YouTube Analytics API | 조회수·구독자·수익 |
| 댓글 관리 | YouTube Data API | 댓글 조회·답글·필터 |
| 재생목록 | YouTube Data API | 생성·편집·순서 변경 |

### Instagram (Phase 2) — Graph API v22.0 (2026 stable, quarterly versioning)
> **중요**: Basic Display API 는 **2024-12 종료**. Professional (Business/Creator) account 필수.

| 기능 | 도구 | 설명 |
|---|---|---|
| 피드 게시 | Graph API v22 `/media` → `/media_publish` | 이미지·캐러셀·태그 (carousel 단일 post, 100 posts/24h 제한) |
| Reels 게시 | Graph API v22 (`media_type=REELS`) | POST `/media` → poll `/{container-id}?fields=status_code=FINISHED` → POST `/media_publish`. 5~90초 + 9:16만 Reels 탭 표시 |
| 스토리 | Graph API v22 (`media_type=STORIES`) | 24시간 스토리 |
| 인사이트 (확장) | Graph API v22 Insights | **신규 metric**: reposts·saves·shares·aggregated views/likes/comments (cross-placement: Instagram + crossposted FB + boosted) |
| Collaborative media | Graph API v22 | 사용자가 collaborator 로 추가/수락된 media 조회 endpoint |
| Like/Unlike | Graph API v22 | Feed posts·Reels·comments·replies on behalf of user |
| DM 자동화 | Graph API v22 + ManyChat / CreatorFlow | 키워드 트리거 자동 응답 |
| 트렌드 수집 | instagrapi (비공식) | 디자인 트렌드 크롤링 |

### TikTok (Phase 2)
| 기능 | 도구 | 설명 |
|---|---|---|
| 영상 게시 | TikTok for Developers | 업로드·설명·해시태그 |
| 분석 | TikTok Analytics | 조회수·좋아요·공유 |

### X / Twitter (Phase 2)
| 기능 | 도구 | 설명 |
|---|---|---|
| 트윗/스레드 | X API v2 | 게시·스레드·미디어 첨부 |
| 분석 | X Analytics | 인상·참여·팔로워 |
| 리스트 관리 | X API v2 | 리스트 생성·팔로우 |

### Naver (Phase 3)
| 기능 | 도구 | 설명 |
|---|---|---|
| 블로그 | Naver Blog API | 글 작성·이미지·태그 |
| 카페 | Naver Cafe API | 게시·댓글 |
| 검색 통계 | Naver SearchAdvisor | 키워드 트렌드 |

### Tistory (Phase 3)
| 기능 | 도구 | 설명 |
|---|---|---|
| 블로그 | Tistory API | 글 작성·카테고리·태그 |
| 통계 | Tistory API | 방문자·페이지뷰 |

## 워크플로우 패턴

### 1. 멀티플랫폼 동시 게시
```text
콘텐츠 생성 → 플랫폼별 최적화 (비율·해시태그·길이) → 동시 게시
```

### 2. 콘텐츠 리퍼포징
```text
YouTube 영상 → 인스타 릴스 (세로 편집) → TikTok (15~60초) → X 스레드 (요약)
```

### 3. 애널리틱스 통합
```text
전 플랫폼 지표 수집 → 통합 대시보드 → 인사이트 생성
```

## 설치 확인
```bash
# Phase 1 (YouTube)
npm view @anthropic-ai/youtube-mcp 2>/dev/null && echo "OK" || echo "설치 필요"
```

## 참조
- `plugins/cost_youtube/` — YouTube 수익화 전용
- `plugins/mcp_media/` — Whisper STT, TTS, FFmpeg
- `docs/user-categories-800.json` — 소셜 관련 카테고리
