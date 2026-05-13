# mcp_image — 무료 이미지 생성 plugin

> Pollinations.ai (flux 모델) 기반 무료·인증X 이미지 생성. 빌더 자동 통합.

## 핵심

- **Pollinations.ai** — 무료, no auth, no rate limit (합리적 사용 시), flux/turbo 모델
- **자동 캐시** — `docs/screens/custom/<keyword>-<hash>.jpg`
- **빌더 자동 호출** — `illustration_lookup.find(kw, auto_generate=True)` 매치 없으면 자동
- **Brand style hint** — `warm-editorial`/`dark-minimal`/`corporate-blue`/`neon-acid`/`colorful` cluster 일치

## 명령

| 명령 | 동작 |
|---|---|
| `/image-generate "<prompt>" [keyword] [cluster]` | Pollinations 호출 → docs/screens/custom/ 저장 |
| `/image-cache --list` | 캐시 list |
| `/image-cache --stats` | 캐시 통계 |

## API (Python)

```python
from pollinations_client import generate, generate_to_file

# 직접 호출
binary = generate("cute giraffe, flat design", model="flux", seed=42)

# 파일 저장 (캐시 자동)
path = generate_to_file(
    prompt="기린 일러스트, cream background",
    keyword="giraffe-lecture",
    brand_cluster="warm-editorial",
)
# → docs/screens/custom/giraffe-lecture-<hash>.jpg
```

## 빌더 통합

```python
from illustration_lookup import find

# 매치 우선순위:
# 1. docs/screens/custom/<keyword-*>.jpg (이전 생성·import)
# 2. docs/screens/illustration/<sub>/ (collectui/dribbble 4694 jpg)
# 3. auto_generate=True 면 Pollinations 자동 호출

jpg_path = find("기린", auto_generate=True, brand_cluster="warm-editorial")
# 매치 없으면 ~30초 후 docs/screens/custom/기린-XXX.jpg 반환
```

## 비용·한도

- **무료** — API key 불필요
- Rate limit: 알려진 한도 없음 (community 무료 서비스 — 남용 X 권장)
- 모델: `flux` (좋음, 30초) / `turbo` (빠름, 10초)

## Brand cluster style hint

| cluster | hint 추가 |
|---|---|
| warm-editorial | warm cream background, editorial illustration, soft coral accents |
| dark-minimal | dark minimalist background, neon accent, clean lines |
| corporate-blue | corporate blue palette, professional, geometric |
| neon-acid | vibrant neon colors on dark, electric energy |
| colorful | bright vibrant colors, playful, energetic |

## 참조

- 코드: `.claude/scripts/lib/pollinations_client.py`
- 캐시: `docs/screens/custom/`
- 메타: `.claude/state/image-cache/<keyword>.json`
- skill: `skills/skill-image-gen.md`
- Pollinations.ai 공식: https://pollinations.ai/
