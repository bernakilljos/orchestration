---
name: design-toolkit
description: |
  HTML/CSS 산출물(PPT·다이어그램·랜딩페이지·대시보드) 작성 시 디자인 도구·라이브러리 선택 가이드.
  사용자가 "디자인", "애니메이션", "예쁘게", "인터랙티브", "차트", "아이콘" 등 시각적 품질을 요청할 때 활성화.
---

## 목적

HTML→PNG 빌더 또는 인터랙티브 HTML 산출물 작성 시 **적합한 CDN 라이브러리 자동 선택**.

## 참조 파일

**`plugins/design_ppt/references/design-toolkit-cdn.md`** — 30개 카테고리, 100+ 라이브러리 CDN 카탈로그

## 라이브러리 선택 매트릭스

| 산출물 | 필수 | 권장 | 선택 |
|--------|------|------|------|
| **PPT 슬라이드** (정적 PNG) | Pretendard, Iconify | Animate.css, 글래스모피즘 | anime.js, Vanta.js |
| **교재 다이어그램** | Noto Sans KR, D3.js | Rough.js, Mermaid | Splitting.js |
| **인터랙티브 대시보드** | Chart.js/ApexCharts | GSAP, Tippy.js, Tailwind | ECharts, Tabulator |
| **랜딩페이지** | AOS, Swiper | anime.js, tsParticles | CountUp.js, Lottie |
| **데모/쇼케이스** | Three.js/Vanta.js | Lottie, Canvas Confetti | p5.js, PixiJS |
| **마인드맵/네트워크** | Markmap/Cytoscape.js | vis-network | GoJS |
| **타임라인/간트** | vis-timeline | Frappe Gantt | — |
| **폼/입력 UI** | Flatpickr, Choices.js | SortableJS, noUiSlider | Quill |

## Playwright 캡처 규칙

### 정적 캡처 (PPT/문서용 PNG)
```python
# 애니메이션 즉시 완료 → 최종 상태 캡처
await page.evaluate('''() => {
    document.querySelectorAll('*').forEach(el => {
        el.style.animation = 'none';
        el.style.transition = 'none';
    });
}''')
await page.screenshot(path=output, full_page=False)
```

### 애니메이션 중간 캡처 (동적 효과 보여줄 때)
```python
await page.goto(url)
await page.wait_for_timeout(1500)  # 1.5초 후 캡처
await page.screenshot(path=output, full_page=False)
```

### CDN 로드 대기
```python
await page.wait_for_load_state('networkidle')  # CDN 다운로드 완료 대기
```

## 폰트 선택 가이드

| 용도 | 1순위 | 2순위 | 3순위 |
|------|-------|-------|-------|
| **한글 본문** | Pretendard Variable | Noto Sans KR | Spoqa Han Sans |
| **한글 헤드라인** | GmarketSans | Black Han Sans | Do Hyeon |
| **한글 캐주얼** | Gamja Flower | Gaegu | Hi Melody |
| **한글 세리프** | Noto Serif KR | Song Myung | Sunflower |
| **영문 모던** | Inter | Poppins | DM Sans |
| **영문 클래식** | Playfair Display | Fraunces | Sora |
| **영문 테크** | Space Grotesk | Plus Jakarta Sans | Outfit |
| **코드** | JetBrains Mono | Fira Code | Source Code Pro |

## 아이콘 선택 가이드

| 세트 | 수량 | 스타일 | CDN 크기 |
|------|------|--------|----------|
| **Iconify** (현재) | 200,000+ | 모든 스타일 (Material, Bootstrap 등 통합) | 온디맨드 |
| **Lucide** | 1,400+ | 라인 (Feather 후속) | ~50KB |
| **Tabler** | 5,100+ | 라인 + Filled | ~100KB |
| **Phosphor** | 7,000+ | 6가지 두께 | ~200KB |
| **Font Awesome** | 2,000+ (Free) | 솔리드 + 라인 | ~80KB |
| **Bootstrap Icons** | 2,000+ | 라인 + Filled | ~60KB |

## 디자인 패턴 (CSS 복사용)

### 글래스모피즘
```css
backdrop-filter: blur(12px) saturate(180%);
background: rgba(255,255,255,0.08);
border: 1px solid rgba(255,255,255,0.15);
border-radius: 16px;
```

### 뉴모피즘
```css
background: #e0e5ec;
box-shadow: 9px 9px 16px #b8bec7, -9px -9px 16px #ffffff;
border-radius: 12px;
```

### 오로라 배경
```css
background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
background-size: 400% 400%;
animation: aurora 15s ease infinite;
```

### 메시 그라디언트
```css
background: radial-gradient(at 40% 20%, #1a1a2e 0, transparent 50%),
            radial-gradient(at 80% 0%, #16213e 0, transparent 50%),
            radial-gradient(at 0% 50%, #0f3460 0, transparent 50%);
```

### 노이즈 텍스처 오버레이
```css
background-image: url("data:image/svg+xml,..."); /* inline SVG noise */
```

### 텍스트 그라디언트
```css
background: linear-gradient(135deg, #667eea, #764ba2);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

## 주의사항

1. CDN 라이브러리는 **인터넷 연결 필요** — 오프라인 환경에서는 로컬 복사본 준비
2. 무거운 라이브러리 (Three.js, ECharts, D3.js) 는 **PNG 캡처 시간 증가** — timeout 넉넉히
3. Web Components (Shoelace, Fluent UI) 는 **Playwright에서 Shadow DOM** 주의
4. 한글 웹폰트는 **로드 시간 1~3초** — `wait_for_load_state('networkidle')` 필수
