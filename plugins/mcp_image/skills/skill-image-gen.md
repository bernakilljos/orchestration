---
name: image-gen
description: |
  Pollinations.ai 무료 이미지 생성 자동 호출. 빌더 (build-*-html-diagrams.py / design_word / design_ppt)
  가 한글 keyword 로 일러스트 필요한데 docs/screens/illustration/ 에 매치 없으면 자동으로
  Pollinations.ai (flux 모델) 호출하여 1024×1024 jpg 생성. 무료·인증X·캐시 자동.
  
  사용자가 "기린 그림 넣어줘"·"차트 시각화"·"5살 비유 일러스트" 같은 요청 시.
license: MIT
metadata:
  category: media
  version: 1.0
  triggers:
    - "이미지 생성"
    - "그림 그려"
    - "일러스트"
    - "image generation"
    - "DALL-E"
    - "pollinations"
---

# Image Generation Skill (Pollinations.ai)

## 트리거

빌더 스크립트 (`build-korean-html-diagrams.py`, `build-arch-lecture-doc.py`, design_word, design_ppt) 안에서:

```python
from illustration_lookup import find

img = find("기린", auto_generate=True, brand_cluster="warm-editorial")
# 1. docs/screens/custom/기린-*.jpg 있으면 즉시 반환
# 2. illustration/animal/ 에서 매치 → 반환
# 3. 둘 다 없으면 Pollinations 자동 호출 → custom/ 캐시 → 반환
```

## 자동 vs 수동

| 모드 | 트리거 | 결과 |
|---|---|---|
| **자동** (`auto_generate=True`) | 빌더 안에서 매치 안 됨 | 30초 후 Pollinations 호출 → custom/ 캐시 |
| **수동** (`/image-generate`) | 사용자 명령 | 즉시 호출 → custom/ 저장 |

## 캐시 전략

- **위치**: `docs/screens/custom/<keyword>-<8자 hash>.jpg`
- **재사용**: 같은 keyword + 같은 seed → 같은 파일 (재호출 X)
- **메타**: `.claude/state/image-cache/<keyword>-<hash>.json` (prompt·brand·seed·timestamp)

## Brand Cluster Style Hint

빌더가 `brand_cluster` 인자 전달 시 Pollinations prompt 끝에 style hint 자동 추가:

| cluster | 추가 hint |
|---|---|
| warm-editorial | warm cream background, editorial illustration |
| dark-minimal | dark minimalist, neon accent |
| corporate-blue | corporate blue, professional, geometric |
| neon-acid | vibrant neon, electric energy |
| colorful | bright vibrant playful colors |

→ 71 brand 토큰 (`brand_tokens.py`) 의 cluster 와 일치.

## Hook 자동화

PostToolUse Edit/Write 후 빌더 파일 (`build-*.py`) 가 호출되면 자동:
1. 빌더 import `illustration_lookup` + `pollinations_client`
2. `find(keyword, auto_generate=True)` 호출 시 자동 fallback
3. 결과 jpg 절대경로 반환 → 빌더가 그대로 임베드

## 성능

- Pollinations.ai 평균: 5-30 초 / 이미지 (flux 모델)
- turbo 모델: 3-10 초 (품질 약간 낮음)
- 캐시 적중: <100ms (디스크 read)

## 금지

- 광고·spam·NSFW 프롬프트 X (Pollinations community policy)
- 1 keyword 당 100+ 회 재호출 X (캐시 활용)
- Production 의무: 단순 빌더 보조용. SaaS 핵심 X (별도 paid API 필요)

## 참조

- 코드: `.claude/scripts/lib/pollinations_client.py`
- lookup: `.claude/scripts/lib/illustration_lookup.py`
- brand 토큰: `.claude/scripts/lib/brand_tokens.py`
- README: `plugins/mcp_image/README.md`
