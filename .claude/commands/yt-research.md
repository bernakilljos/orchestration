---
description: "트렌드·키워드 리서치 (급상승·경쟁채널·검색량)"
allowed-tools: Bash, Read, WebFetch
---

# /yt-research

> **Status**: spec-only — 실구현은 플랫폼에서.

## 목적

트렌드·키워드 리서치 (급상승·경쟁채널·검색량). Shorts·일반 트렌드 분리.

## 사용법 (예정)

```text
/yt-research [args]              # 통합 트렌드
/yt-research --shorts [args]     # Shorts 트렌드 전용 (2026 Shorts first-class endpoint)
```

## 2026 변경점

- YouTube Data API v3 doc 최근 업데이트 2026-06-01
- Shorts metric 은 long-form 과 **분리 조회** (creator vetting 필수)
- OAuth granular scope 요구 — 토큰 explicit refresh 의무

상세는 `../SPEC.md` 참조.
