---
description: "YouTube Data API 업로드 (--dry-run 지원)"
allowed-tools: Bash, Read, WebFetch
---

# /yt-upload

> **Status**: spec-only — 실구현은 플랫폼에서.

## 목적

YouTube Data API v3 업로드 (--dry-run 지원). Shorts·일반 영상 자동 분기.

## 사용법 (예정)

```text
/yt-upload [args]
```

## Shorts 자동 분류 (2026 기준)

- 세로 영상 + 60초 미만 = Shorts 로 자동 분류 (Videos.insert 동일 endpoint)
- 9:16 비율 + ≤60s 권장
- Shorts 전용 metric 은 Shorts API first-class endpoint 로 별도 조회 (`/yt-analytics` 참조)

## OAuth 주의 (2026)

- 더 granular 한 permission scope 필요
- Silent token expiry 가 prod 실패 1순위 → explicit refresh 필수 (mcp_social-auth 스킬 참조)

상세는 `../SPEC.md` 참조.
