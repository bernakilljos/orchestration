---
description: "Instagram Insights — engagement·reposts·saves·shares·cross-placement aggregated (v22 신규 metric)"
allowed-tools: Bash, Read, WebFetch
---

# /ig-analytics

> **Status**: spec — 실구현은 플랫폼에서. Graph API v22 Insights endpoint.

## 목적

Instagram media·account insights 조회. **2026 신규 metric** 포함 (reposts·saves·shares·aggregated cross-placement).

## 사용법 (예정)

```text
/ig-analytics media <media_id> [--include reposts,saves,shares]
/ig-analytics account [--period day|week|days_28]
/ig-analytics reels <reel_id> [--metrics views,reach,plays,completion]
```

## 2026 신규 metric (Graph API v22)

| metric | 의미 | 위치 |
|---|---|---|
| **reposts** | 다른 사용자가 repost 한 횟수 | media |
| **saves** | 저장 횟수 | media |
| **shares** | 공유 횟수 | media |
| **aggregated views** | IG + crossposted FB + boosted 합산 | media |
| **aggregated likes** | 위와 동일 합산 | media |
| **aggregated comments** | 위와 동일 합산 | media |
| collaborative media | collaborator 추가/수락된 콘텐츠 별도 조회 | account |

## 워크플로우 예

```bash
# 1. 최근 30일 모든 reel insights
/ig-analytics reels --since "30 days ago"

# 2. 특정 reel 완주율
/ig-analytics reels <id> --metrics completion,reach,plays

# 3. account 전체 (28일)
/ig-analytics account --period days_28
```

## quota

- Graph API rate limit: app-level + per-user
- Business Use Case (BUC) rate limit 적용 (200 calls/hour/user 일반)

## 참조

- `/ig-upload` (게시)
- `/ig-research` (트렌드)
- `../skills/skill-social-platform.md` § Instagram
- Meta docs: developers.facebook.com/docs/instagram-platform/insights
