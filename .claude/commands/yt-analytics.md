---
description: "수익·조회수·시청지속시간 리포트"
allowed-tools: Bash, Read, WebFetch
---

# /yt-analytics

> **Status**: spec-only — 실구현은 플랫폼에서.

## 목적

수익·조회수·시청지속시간 리포트. **Shorts vs 일반 영상 분리 metric** 지원 (2026 신규).

## 사용법 (예정)

```text
/yt-analytics [args]                # 통합 metric
/yt-analytics --shorts-only [args]  # Shorts 전용 (조회·engagement·completion rate)
/yt-analytics --longform [args]     # 일반 영상 전용
```

## 2026 변경점

- **Shorts API first-class endpoint**: Shorts 전용 metric (views·engagement·completion rate) 별도 조회 가능 — influencer marketing platform 의 short-form creator 평가 필수
- **Quota**: 10,000 units/day per Google Cloud project (기본값 유지, 증액 승인 강화)

상세는 `../SPEC.md` 참조.
