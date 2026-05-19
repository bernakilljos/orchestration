# Game Asset Toolkit — 게임 이미지·아이콘·스프라이트·사운드·3D

> **목적**: 게임 개발 시 필요한 에셋 생성·획득·편집 도구 총정리
> **범위**: 2D 스프라이트, 아이콘, 타일맵, UI, 사운드, 음악, 3D 모델, AI 생성

---

## 1. 무료 게임 에셋 사이트 (즉시 사용)

### 종합
| 사이트 | 내용 | 라이선스 |
|--------|------|----------|
| **kenney.nl** | 70,000+ 에셋 (2D/3D/UI/사운드) | CC0 (완전 무료) |
| **opengameart.org** | 커뮤니티 게임 아트 | CC/GPL 다양 |
| **itch.io/game-assets** | 인디 게임 에셋 마켓 | 무료+유료 |
| **craftpix.net** | 스프라이트, 배경, UI, 타일셋 | 무료+유료 |
| **gamedevmarket.net** | 프리미엄 게임 에셋 | 유료 |
| **quaternius.com** | 3D 로우폴리 모델 | CC0 |
| **kaylousberg.itch.io** | 3D 카약 에셋 팩 | CC0 |

### 아이콘 전용
| 사이트 | 내용 | 형식 |
|--------|------|------|
| **game-icons.net** | 4,000+ 게임 아이콘 (검/방패/물약/스킬) | SVG (흑백, 색상 커스텀) |
| **iconify.design** | 200,000+ 아이콘 (게임 세트 포함) | SVG/웹컴포넌트 |
| **flaticon.com** | 게임 카테고리 아이콘 | PNG/SVG |
| **icons8.com** | 게임 UI 아이콘 세트 | PNG/SVG |
| **noun project** | 미니멀 아이콘 | SVG |

### 텍스처·배경
| 사이트 | 내용 | 라이선스 |
|--------|------|----------|
| **ambientCG** | PBR 텍스처 (금속, 나무, 돌, 흙) | CC0 |
| **polyhaven.com** | HDR 환경맵 + 텍스처 + 3D | CC0 |
| **textures.com** | 사진 기반 텍스처 | 무료 크레딧제 |
| **lospec.com/palette-list** | 픽셀아트 팔레트 700+ | 무료 |

### 사운드
| 사이트 | 내용 | 라이선스 |
|--------|------|----------|
| **freesound.org** | 500,000+ 효과음 | CC 다양 |
| **mixkit.co** | 효과음 + BGM | 무료 |
| **sonniss.com/gameaudiogdc** | GDC 무료 효과음 팩 (매년) | 무료 |
| **incompetech.com** | Kevin MacLeod BGM | CC-BY |
| **musopen.org** | 클래식 음악 (저작권 프리) | CC0/PD |

---

## 2. 스프라이트 / 픽셀아트 도구

### 에디터
| 도구 | 특장 | 비용 |
|------|------|------|
| **Aseprite** | 픽셀아트 표준 (애니메이션, 타일맵) | $20 (소스 무료 빌드 가능) |
| **Piskel** | 웹 기반 픽셀아트 (무료) | 무료 (piskelapp.com) |
| **LibreSprite** | Aseprite 포크 (무료) | 무료 |
| **Pixelorama** | Godot 기반 픽셀 에디터 | 무료 |
| **GraphicsGale** | 클래식 픽셀 에디터 | 무료 |
| **Krita** | 디지털 페인팅 + 애니메이션 | 무료 |
| **GIMP** | Photoshop 대안 | 무료 |

### 자동 생성 (프로시저럴)
```bash
pip install pyxel             # 레트로 게임 엔진 (8bit 스프라이트 내장)
pip install arcade            # 2D 게임 엔진 (스프라이트 시스템)
pip install pixel-font        # 픽셀 폰트 생성
```

### CDN (웹 게임용)
```html
<!-- 스프라이트 시트 로더 -->
<script src="https://cdn.jsdelivr.net/npm/pixi.js@8.1.6/dist/pixi.min.js"></script>

<!-- 픽셀아트 렌더링 (CSS) -->
<style>
  .pixel-art {
    image-rendering: pixelated;      /* Chrome/Edge */
    image-rendering: crisp-edges;    /* Firefox */
    -ms-interpolation-mode: nearest-neighbor;  /* IE */
  }
</style>
```

---

## 3. 아이콘 생성

### game-icons.net 사용법
```html
<!-- SVG 직접 사용 (4000+ 게임 아이콘) -->
<img src="https://game-icons.net/icons/ffffff/000000/1x1/lorc/sword-brandish.svg" width="64">
<img src="https://game-icons.net/icons/ffffff/000000/1x1/delapouite/potion-ball.svg" width="64">
<img src="https://game-icons.net/icons/ffffff/000000/1x1/lorc/shield.svg" width="64">

<!-- 색상 커스텀 (foreground/background) -->
<img src="https://game-icons.net/icons/FFD700/8B0000/1x1/lorc/crown.svg" width="64">
```

### 아이콘 카테고리 (game-icons.net)
- **무기**: sword, axe, bow, staff, dagger, hammer, spear, gun
- **방어구**: shield, helmet, armor, gauntlet, boots
- **아이템**: potion, scroll, gem, key, chest, coin, ring
- **스킬**: fire, ice, lightning, heal, buff, debuff
- **생물**: dragon, wolf, spider, skeleton, ghost, demon
- **UI**: heart, star, arrow, lock, gear, menu

### AI 아이콘 생성
```python
# Stable Diffusion 으로 게임 아이콘 생성
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0")

# 아이콘 스타일 프롬프트
prompt = "game icon, fire sword, fantasy RPG style, flat design, transparent background, 64x64 pixel art"
negative = "blurry, low quality, text, watermark, realistic"
image = pipe(prompt, negative_prompt=negative, width=512, height=512).images[0]
```

### 아이콘 팩 생성기 (Python)
```python
# SVG 아이콘 → 게임용 PNG 스프라이트 시트
from PIL import Image
import cairosvg

icons = ['sword', 'shield', 'potion', 'scroll', 'gem']
size = 64
sheet = Image.new('RGBA', (size * len(icons), size))

for i, icon in enumerate(icons):
    # game-icons.net SVG → PNG
    cairosvg.svg2png(
        url=f"https://game-icons.net/icons/ffffff/000000/1x1/lorc/{icon}.svg",
        write_to=f"tmp_{icon}.png", output_width=size, output_height=size
    )
    img = Image.open(f"tmp_{icon}.png")
    sheet.paste(img, (i * size, 0))

sheet.save("icon_spritesheet.png")
```

---

## 4. 타일맵 / 맵 에디터

| 도구 | 특장 | 비용 |
|------|------|------|
| **Tiled** | 타일맵 표준 에디터 (.tmx) | 무료 |
| **LDtk** | 모던 2D 레벨 에디터 (Celeste 개발자) | 무료 |
| **Tilesetter** | 자동 타일 규칙 생성 | $15 |
| **RPG Maker** | RPG 특화 맵+이벤트 | $80 |

### 프로시저럴 맵 생성
```python
pip install noise             # Perlin/Simplex 노이즈 (지형 생성)
pip install tcod              # 로그라이크 맵 생성 (BSP, 던전)
pip install wave-function-collapse  # WFC 타일 자동 배치
```

```python
# Perlin 노이즈 → 지형 맵
import noise
import numpy as np
from PIL import Image

width, height = 256, 256
world = np.zeros((height, width))
for y in range(height):
    for x in range(width):
        world[y][x] = noise.pnoise2(x/50, y/50, octaves=6)

# 높이 → 색상 (물=파랑, 풀=초록, 산=갈색, 눈=흰색)
```

---

## 5. UI 키트 (게임용)

### 무료 UI 키트
| 이름 | 스타일 | 소스 |
|------|--------|------|
| **Kenney UI Pack** | 범용 게임 UI (버튼, 슬라이더, 패널) | kenney.nl |
| **Fantasy UI** | RPG 스타일 (인벤토리, 체력바) | craftpix.net |
| **Sci-Fi UI** | SF 스타일 (HUD, 미니맵) | craftpix.net |
| **Mobile Game UI** | 모바일 게임 (캐주얼) | itch.io |

### CSS 게임 UI 패턴
```css
/* RPG 스타일 HP 바 */
.hp-bar {
  width: 200px; height: 20px;
  background: #333; border: 2px solid #666;
  border-radius: 10px; overflow: hidden;
}
.hp-bar-fill {
  height: 100%;
  background: linear-gradient(180deg, #ff4444, #cc0000);
  transition: width 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(255,255,255,0.3);
}

/* 픽셀 스타일 버튼 */
.pixel-btn {
  font-family: 'Press Start 2P', monospace;
  background: #4a86c8;
  color: white;
  border: 4px solid;
  border-color: #6ba8e8 #2a5698 #2a5698 #6ba8e8;
  padding: 8px 16px;
  image-rendering: pixelated;
  cursor: pointer;
}
.pixel-btn:active {
  border-color: #2a5698 #6ba8e8 #6ba8e8 #2a5698;
}

/* 인벤토리 그리드 */
.inventory {
  display: grid;
  grid-template-columns: repeat(6, 48px);
  gap: 4px;
  background: rgba(0,0,0,0.8);
  padding: 8px;
  border: 2px solid #555;
}
.inv-slot {
  width: 48px; height: 48px;
  background: rgba(255,255,255,0.1);
  border: 1px solid #444;
  display: flex; align-items: center; justify-content: center;
}
```

### 게임 UI 폰트 (CDN)
```html
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=VT323&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=DotGothic16&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&display=swap" rel="stylesheet">
```

---

## 6. AI 게임 에셋 생성

### 이미지 생성 (Stable Diffusion)
```python
# 스타일별 프롬프트 템플릿
PROMPTS = {
    "pixel_item": "pixel art game item, {item}, 32x32, transparent background, retro style, clean edges",
    "pixel_char": "pixel art game character, {desc}, 16x32 sprite, side view, idle pose, retro RPG",
    "fantasy_icon": "game icon, {item}, fantasy RPG style, detailed, gold border, dark background",
    "isometric": "isometric game tile, {desc}, low poly, soft shadows, clean edges",
    "portrait": "character portrait, {desc}, anime style, bust shot, game avatar",
    "landscape": "game background, {desc}, parallax layers, 16bit style, wide format",
    "monster": "creature design, {desc}, game enemy, concept art, dynamic pose",
}
```

### 캐릭터 스프라이트 시트 생성
```python
# AI로 캐릭터 생성 → 스프라이트 시트로 정리
from diffusers import StableDiffusionPipeline

# 방향별 생성 (front, back, left, right)
directions = ['front view', 'back view', 'left side view', 'right side view']
base_prompt = "pixel art RPG warrior character, 32x32, {dir}, walk cycle frame 1"

for d in directions:
    img = pipe(base_prompt.format(dir=d)).images[0]
    img.save(f"warrior_{d.replace(' ', '_')}.png")
```

### 텍스처 생성
```python
# Stable Diffusion 으로 타일러블 텍스처
prompt = "seamless tileable texture, {material}, game asset, top-down view, 256x256"
materials = ["grass", "stone floor", "wooden planks", "sand", "water", "lava", "snow", "dirt path"]
```

### 사운드 생성
```html
<!-- jsfxr — 레트로 게임 효과음 생성기 (웹) -->
<script src="https://cdn.jsdelivr.net/npm/jsfxr@0.2.0/dist/jsfxr.min.js"></script>
```
```python
# Python 효과음 생성
pip install pyfxr              # 레트로 게임 효과음 (sfxr 포트)
```

```python
import pyfxr
# 프리셋으로 효과음 생성
jump = pyfxr.preset("jump")
explosion = pyfxr.preset("explosion")
powerup = pyfxr.preset("powerup")
hit = pyfxr.preset("hit")
coin = pyfxr.preset("coin")
laser = pyfxr.preset("laser")
```

---

## 7. 게임 엔진 (웹/Python/범용)

### 웹 게임 엔진 (CDN)
```html
<!-- Phaser 3 — 2D 웹게임 표준 -->
<script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js"></script>

<!-- Kaboom.js — 초간단 2D (교육용) -->
<script src="https://cdn.jsdelivr.net/npm/kaboom@3000.1.17/dist/kaboom.js"></script>

<!-- Excalibur — TypeScript 2D 엔진 -->
<script src="https://cdn.jsdelivr.net/npm/excalibur@0.29.3/build/dist/excalibur.min.js"></script>

<!-- PixiJS — 2D WebGL 렌더러 (고성능) -->
<script src="https://cdn.jsdelivr.net/npm/pixi.js@8.1.6/dist/pixi.min.js"></script>

<!-- Three.js — 3D WebGL -->
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>

<!-- Babylon.js — 3D 게임 엔진 -->
<script src="https://cdn.jsdelivr.net/npm/babylonjs@7.10.1/babylon.js"></script>

<!-- PlayCanvas — 3D 게임 엔진 (웹) -->
<script src="https://cdn.jsdelivr.net/npm/playcanvas@1.72.0/build/playcanvas.min.js"></script>

<!-- Matter.js — 2D 물리 -->
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.20.0/build/matter.min.js"></script>

<!-- Planck.js — Box2D 포트 (2D 물리) -->
<script src="https://cdn.jsdelivr.net/npm/planck@1.0.4/dist/planck.min.js"></script>
```

### Python 게임
```bash
pip install pygame            # 2D 게임 표준
pip install arcade            # 모던 2D (교육 친화)
pip install pyglet            # OpenGL 기반
pip install ursina            # 3D 초간단 (Panda3D 기반)
pip install pyxel             # 레트로 8bit 엔진
pip install ppb               # 교육용 게임 프레임워크
pip install raylib            # C raylib 바인딩 (고성능)
```

### 범용 (데스크톱/모바일/콘솔)
| 엔진 | 언어 | 2D/3D | 비용 |
|------|------|-------|------|
| **Godot** | GDScript/C# | 2D+3D | 무료 오픈소스 |
| **Unity** | C# | 2D+3D | 무료 (매출 제한) |
| **Unreal** | C++/Blueprint | 3D | 무료 (로열티) |
| **Defold** | Lua | 2D+3D | 무료 |
| **Bevy** | Rust | 2D+3D | 무료 오픈소스 |
| **LÖVE** | Lua | 2D | 무료 |
| **MonoGame** | C# | 2D+3D | 무료 |

---

## 8. 스프라이트 시트 도구

### 패킹 (여러 이미지 → 1장 시트)
```bash
pip install Pillow            # PIL 로 수동 패킹
pip install rectpack          # 최적 사각형 패킹 알고리즘
```

```python
# 스프라이트 시트 자동 패킹
from PIL import Image
import rectpack

packer = rectpack.newPacker()
sprites = ['walk1.png', 'walk2.png', 'walk3.png', 'walk4.png']
images = [Image.open(s) for s in sprites]

for i, img in enumerate(images):
    packer.add_rect(img.width, img.height, i)
packer.add_bin(512, 512)
packer.pack()

sheet = Image.new('RGBA', (512, 512))
for rect in packer.rect_list():
    b, x, y, w, h, rid = rect
    sheet.paste(images[rid], (x, y))
sheet.save('spritesheet.png')
```

### 온라인 도구
| 도구 | URL | 특장 |
|------|-----|------|
| **TexturePacker** | texturepacker.com | 업계 표준 스프라이트 패커 |
| **ShoeBox** | renderhjs.net/shoebox | 무료 스프라이트 도구 |
| **Leshy SpriteSheet Tool** | leshylabs.com | 웹 기반 무료 |

---

## 9. 파티클 / VFX

### 웹
```html
<!-- tsParticles (이미 CDN 카탈로그에 있음) -->
<script src="https://cdn.jsdelivr.net/npm/tsparticles@3.3.0/tsparticles.bundle.min.js"></script>

<!-- Proton.js — 2D 파티클 엔진 -->
<script src="https://cdn.jsdelivr.net/npm/proton-engine@4.3.2/build/proton.min.js"></script>
```

### 파티클 프리셋 (게임용)
```javascript
// 폭발
{ particles: { number: { value: 50 }, move: { speed: 20, outModes: 'destroy' }, life: { duration: { value: 0.5 } } } }

// 마법 반짝임
{ particles: { number: { value: 100 }, color: { value: ['#ff0', '#0ff', '#f0f'] }, size: { value: 3, animation: { enable: true } } } }

// 비/눈
{ particles: { number: { value: 200 }, move: { direction: 'bottom', speed: 5 }, shape: { type: 'circle' }, size: { value: 2 } } }
```

---

## 10. 게임 수학 / 유틸

```bash
pip install pymunk            # Chipmunk 2D 물리 (pygame 연동)
pip install pytmx             # Tiled .tmx 맵 로더
pip install noise             # Perlin/Simplex 노이즈
pip install numpy             # 벡터/행렬 연산
pip install shapely           # 충돌 감지 (다각형)
```

```javascript
// A* 길찾기 (CDN)
// https://cdn.jsdelivr.net/npm/pathfinding@0.4.18/pathfinding-browser.min.js

// EasyStar.js — 간단한 A*
// https://cdn.jsdelivr.net/npm/easystarjs@0.4.4/src/easystar.js
```

---

## 추천 조합

### 2D 픽셀 RPG
```text
Phaser 3 + Tiled + game-icons.net + Press Start 2P 폰트 + pyfxr 효과음
```

### 웹 캐주얼 게임
```text
Kaboom.js + Kenney 에셋 + tsParticles + Matter.js + Howler.js
```

### 3D 웹 게임
```text
Three.js/Babylon.js + polyhaven 텍스처 + quaternius 3D 모델
```

### 인디 게임 프로토타입
```text
Godot + Aseprite + LMMS (음악) + Stable Diffusion (컨셉아트)
```

### AI 게임 에셋 파이프라인
```text
Stable Diffusion (이미지) → rembg (배경제거) → rectpack (스프라이트시트) → Phaser (게임)
```
