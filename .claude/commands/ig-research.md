---
description: "Instagram 트렌드·해시태그·경쟁 채널 리서치 (Graph API v22 + instagrapi 비공식)"
allowed-tools: Bash, Read, WebFetch
---

# /ig-research

> **Status**: spec — 실구현은 플랫폼에서.

## 목적

Instagram 트렌드·해시태그·경쟁 채널 리서치. 공식 Graph API (한정) + instagrapi (비공식 보완).

## 사용법 (예정)

```text
/ig-research hashtag <tag>         # 해시태그 검색 (Graph API v22)
/ig-research competitor <username> # 경쟁 채널 public insights
/ig-research trends [--region kr]  # 지역별 트렌드 (instagrapi)
/ig-research reels-top [--niche fashion]  # 인기 Reels (niche 별)
```

## 공식 vs 비공식

| 도구 | 공식 | 데이터 |
|---|---|---|
| Graph API v22 Hashtag Search | ✅ | 최근 24h top + recent posts (제한적) |
| Graph API v22 Business Discovery | ✅ | public competitor data (follower 등) |
| instagrapi (비공식) | ❌ | trends·explore·suggested — 약관 위험 |

**권장**: 공식 우선. 비공식은 디자인 트렌드 리서치 같은 비-게시 용도만.

## 워크플로우 예

```bash
# 1. 해시태그 분석
/ig-research hashtag "AI엔지니어링"
→ top posts, recent posts, engagement rate

# 2. 경쟁 채널 비교
/ig-research competitor "openai" --fields followers_count,media_count

# 3. niche 트렌드
/ig-research reels-top --niche tech --region kr
```

## 참조

- `/ig-upload` (게시)
- `/ig-analytics` (자기 채널 분석)
- `../skills/skill-social-platform.md` § Instagram
- Meta docs: developers.facebook.com/docs/instagram-platform/hashtag-search
- 트렌드 sync: 우리 `.claude/scripts/external-trends-sync.sh` (있을 경우)
