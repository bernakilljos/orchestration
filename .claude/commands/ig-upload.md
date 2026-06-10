---
description: "Instagram Graph API v22 게시 — Reels·피드·캐러셀·스토리 (3-step container flow)"
allowed-tools: Bash, Read, WebFetch
---

# /ig-upload

> **Status**: spec — 실구현은 플랫폼에서. Graph API v22.0 (2026 stable).

## 목적

Instagram Graph API v22 로 콘텐츠 게시. Professional account (Business/Creator) 필수 — Basic Display API 는 2024-12 종료.

## 사용법 (예정)

```text
/ig-upload <type> <media_url> [--caption "..."] [--hashtags "..."]

type:
  feed        # 이미지·캐러셀 (carousel = 단일 post)
  reels       # 5~90초 9:16 (그 외는 일반 video 로 발행)
  story       # 24시간 스토리
```

## 3-step container flow (Graph API v22)

```bash
# 1. Container 생성
POST /{ig-user-id}/media
  media_type=REELS  # 또는 IMAGE / VIDEO / STORIES
  video_url=<public_url>
  caption=...
→ {container-id}

# 2. Status polling
GET /{container-id}?fields=status_code
→ FINISHED (또는 IN_PROGRESS / ERROR)

# 3. Publish
POST /{ig-user-id}/media_publish
  creation_id={container-id}
→ {media-id}
```

## 제한

- **24h posting limit**: 100 posts/계정/24시간 (`media_publish` 시점 enforced)
- **Reels 탭 자격**: 5~90초 + 9:16 비율만. 외 = 일반 video post
- **Carousel**: Reels 혼합 X (Reels 는 carousel 안 들어감)
- **공개 media_url 필수**: 임시 S3 또는 CDN URL

## OAuth (2026)

- Professional account + Instagram Login 또는 Facebook Login
- token 만료 자동 갱신 (mcp_social-auth 스킬)
- 권한: `instagram_business_content_publish`

## 참조

- `../skills/skill-social-platform.md` § Instagram
- Meta docs: developers.facebook.com/docs/instagram-platform/content-publishing
- 인사이트: `/ig-analytics`
- 트렌드: `/ig-research`
