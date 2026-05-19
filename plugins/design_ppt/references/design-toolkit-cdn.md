# Design Toolkit — CDN 라이브러리 카탈로그

> **목적**: HTML→PNG 빌더에서 `<script src="CDN">` / `<link href="CDN">` 로 즉시 사용
> **Playwright 주의**: 애니메이션 있는 HTML 캡처 시 `page.wait_for_timeout(ms)` 필요

---

## 1. Animation (애니메이션)

### anime.js — 경량 타임라인 애니메이션
```html
<script src="https://cdn.jsdelivr.net/npm/animejs@3.2.2/lib/anime.min.js"></script>
```
- 타임라인, 스태거, SVG path morphing, 스프링 물리
- **Playwright**: `wait_for_timeout(2000)` (애니메이션 완료 대기)
```js
anime({ targets: '.box', translateX: 250, rotate: '1turn', duration: 800 });
```

### GSAP — 프로급 애니메이션 엔진
```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/DrawSVGPlugin.min.js"></script>
```
- 타임라인 체이닝, 스크롤 트리거, 텍스트 타이핑, SVG 드로우
```js
gsap.from('.card', { y: 50, opacity: 0, stagger: 0.1, duration: 0.6 });
```

### Motion One — 최소 번들 (3.8KB)
```html
<script src="https://cdn.jsdelivr.net/npm/motion@10.18.0/dist/motion.min.js"></script>
```
- Web Animations API 기반, WAAPI 네이티브 성능

### Lottie — After Effects JSON 애니메이션
```html
<script src="https://cdn.jsdelivr.net/npm/lottie-web@5.12.2/build/player/lottie.min.js"></script>
```
- AE → Bodymovin → JSON → 웹 재생
```js
lottie.loadAnimation({ container: el, path: 'anim.json', renderer: 'svg' });
```

### Auto Animate — 레이아웃 전환 자동 애니메이션
```html
<script src="https://cdn.jsdelivr.net/npm/@formkit/auto-animate@0.8.2/index.min.js"></script>
```

---

## 2. CSS Animation (선언형)

### Animate.css — 80+ 프리셋 애니메이션
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/animate.css@4.1.1/animate.min.css">
```
```html
<h1 class="animate__animated animate__fadeInUp">제목</h1>
```

### Hover.css — 호버 효과 모음
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/hover.css@2.3.1/css/hover-min.css">
```

### Transition.css — 47개 전환 효과
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/transition-style@1.0.1/transition.min.css">
```

---

## 3. SVG / Drawing

### Vivus — SVG 선 그리기 애니메이션
```html
<script src="https://cdn.jsdelivr.net/npm/vivus@0.4.6/dist/vivus.min.js"></script>
```
```js
new Vivus('my-svg', { duration: 200, type: 'oneByOne' });
```

### Rough.js — 손그림 느낌 도형
```html
<script src="https://cdn.jsdelivr.net/npm/roughjs@4.6.6/bundled/rough.min.js"></script>
```
```js
const rc = rough.canvas(document.getElementById('canvas'));
rc.rectangle(10, 10, 200, 200, { roughness: 2.0, fill: 'coral' });
```

### Two.js — 2D 드로잉 (SVG/Canvas/WebGL)
```html
<script src="https://cdn.jsdelivr.net/npm/two.js@0.8.12/build/two.min.js"></script>
```

---

## 4. Data Visualization (데이터 시각화)

### D3.js — 데이터 기반 문서 조작
```html
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
```
- 트리맵, 네트워크, 산점도, 히트맵 모두 가능

### Chart.js — 심플 차트
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
```
- Bar, Line, Pie, Doughnut, Radar, Polar, Bubble, Scatter

### ApexCharts — 인터랙티브 차트
```html
<script src="https://cdn.jsdelivr.net/npm/apexcharts@3.49.0/dist/apexcharts.min.js"></script>
```

### ECharts — 대규모 데이터 시각화 (Baidu)
```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
```
- 3D, 지도, 트리, 산키 다이어그램

### Mermaid — 다이어그램 (flowchart, sequence, gantt, ER)
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.0/dist/mermaid.min.js"></script>
```
```js
mermaid.initialize({ startOnLoad: true, theme: 'dark' });
```

---

## 5. 3D / WebGL

### Three.js — 3D 렌더링
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>
```

### Zdog — 의사-3D (플랫 디자인 3D)
```html
<script src="https://cdn.jsdelivr.net/npm/zdog@1.1.3/dist/zdog.dist.min.js"></script>
```
- 둥근 느낌, 일러스트 스타일 3D

### Vanta.js — 배경 3D 효과 (Three.js 기반)
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/vanta@0.5.24/dist/vanta.net.min.js"></script>
```
```js
VANTA.NET({ el: '#bg', color: 0x3f7fff, backgroundColor: 0x0a0a0a });
```
- NET, WAVES, BIRDS, FOG, CLOUDS, GLOBE, DOTS, RINGS, HALO, TOPOLOGY, TRUNK, CELLS

---

## 6. Particle / Effect

### tsParticles — 파티클 효과 (particles.js 후속)
```html
<script src="https://cdn.jsdelivr.net/npm/tsparticles@3.3.0/tsparticles.bundle.min.js"></script>
```
```js
tsParticles.load('particles', { particles: { number: { value: 80 }, move: { enable: true } } });
```

### Canvas Confetti — 축하 효과
```html
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
```
```js
confetti({ particleCount: 100, spread: 70 });
```

---

## 7. Typography (타이포그래피)

### Splitting.js — 텍스트 분리 → 글자별 애니메이션
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.css">
<script src="https://cdn.jsdelivr.net/npm/splitting@1.0.6/dist/splitting.min.js"></script>
```
```js
Splitting({ target: '.hero-text', by: 'chars' });
```

### Typed.js — 타이핑 효과
```html
<script src="https://cdn.jsdelivr.net/npm/typed.js@2.1.0/dist/typed.umd.js"></script>
```
```js
new Typed('.typing', { strings: ['Claude', 'Codex', 'Gemini'], typeSpeed: 50 });
```

### CountUp.js — 숫자 카운트업 애니메이션
```html
<script src="https://cdn.jsdelivr.net/npm/countup.js@2.8.0/dist/countUp.umd.js"></script>
```

---

## 8. Scroll / Reveal

### AOS — Animate On Scroll
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css">
<script src="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js"></script>
```
```html
<div data-aos="fade-up" data-aos-duration="800">내용</div>
```
```js
AOS.init();
```

### ScrollReveal
```html
<script src="https://cdn.jsdelivr.net/npm/scrollreveal@4.0.9/dist/scrollreveal.min.js"></script>
```

---

## 9. Carousel / Slider

### Swiper — 터치 슬라이더
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11.1.0/swiper-bundle.min.css">
<script src="https://cdn.jsdelivr.net/npm/swiper@11.1.0/swiper-bundle.min.js"></script>
```

### Splide — 경량 슬라이더 (29KB)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">
<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>
```

---

## 10. Icon Libraries (아이콘)

### Iconify — 200,000+ 아이콘 (현재 사용 중)
```html
<script src="https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js"></script>
```
```html
<iconify-icon icon="mdi:rocket-launch" width="48"></iconify-icon>
```

### Lucide — Feather Icons 후속 (1400+ 아이콘, SVG)
```html
<script src="https://cdn.jsdelivr.net/npm/lucide@0.379.0/dist/umd/lucide.min.js"></script>
```
```js
lucide.createIcons();
```
```html
<i data-lucide="shield-check"></i>
```

### Phosphor Icons — 7000+ 아이콘
```html
<script src="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css"></script>
```

### Heroicons — Tailwind 공식 아이콘 (300+)
```html
<!-- SVG 직접 사용 권장 (CDN 없음, copy-paste) -->
<!-- https://heroicons.com -->
```

### Tabler Icons — 5100+ SVG 아이콘
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.2.0/dist/tabler-icons.min.css">
```

### Font Awesome 6 Free
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css">
```

### Bootstrap Icons
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
```

---

## 11. Fonts (한글 + 디자인 폰트)

### 본문용
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200..900&display=swap" rel="stylesheet">
```

### 디자인 / 헤드라인용
```html
<link href="https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSansMedium.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Do+Hyeon&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Jua&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=East+Sea+Dokdo&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Hi+Melody&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Sunflower:wght@300;500;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Song+Myung&display=swap" rel="stylesheet">
```

### 코드용
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300..700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;700&display=swap" rel="stylesheet">
```

### 영문 디자인
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@100..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@100..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@100..900&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200..800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@100..800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap" rel="stylesheet">
```

---

## 12. Gradient / Color

### CSS Gradient 패턴 (복사용)
```css
/* 메시 그라디언트 */
background: radial-gradient(at 40% 20%, #1a1a2e 0, transparent 50%),
            radial-gradient(at 80% 0%, #16213e 0, transparent 50%),
            radial-gradient(at 0% 50%, #0f3460 0, transparent 50%),
            radial-gradient(at 80% 50%, #533483 0, transparent 50%),
            radial-gradient(at 0% 100%, #e94560 0, transparent 50%);

/* 글래스모피즘 */
backdrop-filter: blur(12px) saturate(180%);
background: rgba(255,255,255,0.08);
border: 1px solid rgba(255,255,255,0.15);
border-radius: 16px;

/* 뉴모피즘 */
background: #e0e5ec;
box-shadow: 9px 9px 16px #b8bec7, -9px -9px 16px #ffffff;

/* 오로라 배경 */
background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
background-size: 400% 400%;
animation: aurora 15s ease infinite;
@keyframes aurora { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }

/* 노이즈 텍스처 */
background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
```

---

## 13. Layout / CSS Framework

### Tailwind CSS (CDN Play)
```html
<script src="https://cdn.tailwindcss.com"></script>
```

### DaisyUI (Tailwind 컴포넌트)
```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.2/dist/full.min.css" rel="stylesheet">
```

### UnoCSS (atomic, Tailwind 호환)
```html
<!-- CDN 없음, 빌드 도구 필요 -->
```

---

## 14. Image / Media

### Lightbox2
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lightbox2@2.11.4/dist/css/lightbox.min.css">
<script src="https://cdn.jsdelivr.net/npm/lightbox2@2.11.4/dist/js/lightbox.min.js"></script>
```

### Medium Zoom — 이미지 줌 (Medium 스타일)
```html
<script src="https://cdn.jsdelivr.net/npm/medium-zoom@1.1.0/dist/medium-zoom.min.js"></script>
```

### Masonry — Pinterest 레이아웃
```html
<script src="https://cdn.jsdelivr.net/npm/masonry-layout@4.2.2/dist/masonry.pkgd.min.js"></script>
```

---

## 15. Code Highlight

### Prism.js
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css">
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
```

### Highlight.js
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css">
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/highlight.min.js"></script>
```

### Shiki — VS Code 수준 하이라이팅
```html
<script src="https://cdn.jsdelivr.net/npm/shiki@1.6.0/dist/index.unpkg.iife.js"></script>
```

---

## 16. Utility

### Day.js — 경량 날짜 (2KB)
```html
<script src="https://cdn.jsdelivr.net/npm/dayjs@1.11.11/dayjs.min.js"></script>
```

### Lodash
```html
<script src="https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js"></script>
```

### Mark.js — 텍스트 하이라이트
```html
<script src="https://cdn.jsdelivr.net/npm/mark.js@8.11.1/dist/mark.min.js"></script>
```

### Tippy.js — 툴팁
```html
<script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.8/dist/umd/popper.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/tippy.js@6.3.7/dist/tippy-bundle.umd.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tippy.js@6.3.7/dist/tippy.css">
```

---

## Playwright 캡처 팁

```python
# 애니메이션 있는 HTML 캡처 패턴
async def capture_with_animation(page, html_path, output_png, wait_ms=2000):
    await page.goto(f'file:///{html_path}')
    await page.wait_for_timeout(wait_ms)  # 애니메이션 완료 대기
    await page.screenshot(path=output_png, full_page=False)

# CSS animation 즉시 완료 (정적 캡처용)
async def capture_static(page, html_path, output_png):
    await page.goto(f'file:///{html_path}')
    await page.evaluate('''() => {
        document.querySelectorAll('*').forEach(el => {
            el.style.animation = 'none';
            el.style.transition = 'none';
        });
    }''')
    await page.screenshot(path=output_png, full_page=False)

# anime.js 완료 대기
async def capture_animejs(page, html_path, output_png):
    await page.goto(f'file:///{html_path}')
    await page.wait_for_function('typeof anime !== "undefined"')
    await page.wait_for_timeout(3000)
    await page.screenshot(path=output_png, full_page=False)
```

---

## 17. UI Component Libraries (컴포넌트 라이브러리)

### Bootstrap 5 — 가장 널리 쓰이는 UI 프레임워크
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
```
- Grid, Card, Modal, Navbar, Accordion, Toast, Offcanvas, Carousel

### Bulma — Flexbox CSS (JS 없음)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0.0/css/bulma.min.css">
```
- 순수 CSS, JS 의존 없음, 모바일 퍼스트

### Pico CSS — 클래스리스 CSS (시맨틱 HTML만으로 스타일)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.0.6/css/pico.min.css">
```
- `<article>`, `<section>`, `<nav>` 만으로 자동 스타일링

### Water.css — 클래스 없는 미니멀 CSS
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2.1.1/out/water.min.css">
```

### MVP.css — 최소 MVP 스타일
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/mvp.css@1.14.0/mvp.css">
```

### Sakura — 클래스리스 CSS (일본풍)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sakura.css@1.4.1/css/sakura.css">
```

### Simple.css — 시맨틱 HTML CSS
```html
<link rel="stylesheet" href="https://cdn.simplecss.org/simple.min.css">
```

### Pure CSS — Yahoo (3.7KB)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@3.0.0/build/pure-min.css">
```

---

## 18. Design System CSS (기업 디자인 시스템)

### IBM Carbon Design
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@carbon/styles@1.57.0/css/styles.min.css">
```
- IBM 공식 디자인 시스템, 접근성 최적화, 데이터 중심 UI

### Shoelace — 웹 컴포넌트 기반
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/themes/light.css">
<script type="module" src="https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2.15.1/cdn/shoelace-autoloader.js"></script>
```
```html
<sl-button variant="primary">버튼</sl-button>
<sl-dialog label="다이얼로그"><p>내용</p></sl-dialog>
<sl-progress-bar value="60"></sl-progress-bar>
```

### Open Props — CSS Custom Properties 디자인 토큰
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/open-props@1.7.4/open-props.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/open-props@1.7.4/normalize.min.css">
```
- 색상·그림자·크기·이징·그라디언트 변수 400+개

### Primer CSS — GitHub 공식
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@primer/css@21.3.3/dist/primer.css">
```
- GitHub UI 그대로 재현 가능

### Spectrum CSS — Adobe 공식
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@spectrum-css/vars@9.0.0/dist/spectrum-global.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@spectrum-css/tokens@14.0.0/dist/css/index.css">
```

### Fluent UI Web Components — Microsoft 공식
```html
<script type="module" src="https://cdn.jsdelivr.net/npm/@fluentui/web-components@2.6.1/dist/web-components.min.js"></script>
```
```html
<fluent-button appearance="accent">버튼</fluent-button>
<fluent-progress></fluent-progress>
```

---

## 19. Table / Grid (테이블·데이터그리드)

### Tabulator — 인터랙티브 테이블
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tabulator-tables@6.2.1/dist/css/tabulator.min.css">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6.2.1/dist/js/tabulator.min.js"></script>
```
- 정렬, 필터, 페이지네이션, 편집, 엑셀 export

### DataTables — jQuery 테이블
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/datatables.net-dt@2.0.8/css/dataTables.dataTables.min.css">
<script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/datatables.net@2.0.8/js/dataTables.min.js"></script>
```

### Grid.js — 프레임워크 독립 테이블
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/gridjs@6.2.0/dist/theme/mermaid.min.css">
<script src="https://cdn.jsdelivr.net/npm/gridjs@6.2.0/dist/gridjs.umd.js"></script>
```

---

## 20. Map / Geo (지도)

### Leaflet — 오픈소스 지도
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.min.js"></script>
```

### MapLibre GL — 벡터 지도 (Mapbox 오픈소스 포크)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.4.1/dist/maplibre-gl.css">
<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@4.4.1/dist/maplibre-gl.js"></script>
```

---

## 21. Timeline / Gantt

### vis-timeline — 타임라인 시각화
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.3/dist/vis-timeline-graph2d.min.css">
<script src="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.3/dist/vis-timeline-graph2d.min.js"></script>
```

### vis-network — 네트워크 그래프
```html
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.6/dist/vis-network.min.js"></script>
```

### Frappe Gantt — 간트 차트
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.css">
<script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js"></script>
```

---

## 22. Form / Input

### Choices.js — 셀렉트 박스 강화
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/styles/choices.min.css">
<script src="https://cdn.jsdelivr.net/npm/choices.js@10.2.0/public/assets/scripts/choices.min.js"></script>
```

### Flatpickr — 날짜 선택
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.js"></script>
```

### noUiSlider — 레인지 슬라이더
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/nouislider@15.7.1/dist/nouislider.min.css">
<script src="https://cdn.jsdelivr.net/npm/nouislider@15.7.1/dist/nouislider.min.js"></script>
```

### SortableJS — 드래그앤드롭 정렬
```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
```

### Quill — 리치 텍스트 에디터
```html
<link href="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.js"></script>
```

---

## 23. Notification / Alert

### SweetAlert2
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11.11.0/dist/sweetalert2.min.css">
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.11.0/dist/sweetalert2.all.min.js"></script>
```
```js
Swal.fire({ title: '완료!', text: '저장됨', icon: 'success' });
```

### Toastify
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/toastify-js@1.12.0/src/toastify.min.css">
<script src="https://cdn.jsdelivr.net/npm/toastify-js@1.12.0/src/toastify.min.js"></script>
```

### Notiflix
```html
<script src="https://cdn.jsdelivr.net/npm/notiflix@3.2.7/dist/notiflix-aio-3.2.7.min.js"></script>
```
- Notify, Report, Confirm, Loading, Block 5종 세트

---

## 24. Diagram / Flowchart

### Mermaid (위 §4 참조)

### GoJS — 엔터프라이즈 다이어그램 (평가판)
```html
<script src="https://cdn.jsdelivr.net/npm/gojs@3.0.6/release/go.js"></script>
```

### JointJS (Rappid) — 다이어그램 프레임워크
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jointjs@4.0.1/dist/joint.css">
<script src="https://cdn.jsdelivr.net/npm/jointjs@4.0.1/dist/joint.js"></script>
```

### Cytoscape.js — 그래프/네트워크 시각화
```html
<script src="https://cdn.jsdelivr.net/npm/cytoscape@3.29.2/dist/cytoscape.min.js"></script>
```

### Markmap — 마인드맵 (마크다운 기반)
```html
<script src="https://cdn.jsdelivr.net/npm/markmap-view@0.17.0/dist/browser/index.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.17.0/dist/browser/index.js"></script>
```

---

## 25. Loading / Progress

### NProgress — 상단 진행바 (YouTube 스타일)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/nprogress@0.2.0/nprogress.css">
<script src="https://cdn.jsdelivr.net/npm/nprogress@0.2.0/nprogress.js"></script>
```

### Pace.js — 자동 페이지 로딩
```html
<script src="https://cdn.jsdelivr.net/npm/pace-js@1.2.4/pace.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pace-js@1.2.4/themes/blue/pace-theme-minimal.css">
```

### LDRS — 53개 로딩 스피너 (웹 컴포넌트)
```html
<script type="module" src="https://cdn.jsdelivr.net/npm/ldrs@1.0.2/dist/auto/ring.js"></script>
```
```html
<l-ring size="40" color="coral"></l-ring>
<l-bouncy size="45" color="deepskyblue"></l-bouncy>
```

---

## 26. Motion / Physics

### Matter.js — 2D 물리 엔진
```html
<script src="https://cdn.jsdelivr.net/npm/matter-js@0.20.0/build/matter.min.js"></script>
```

### p5.js — Creative Coding
```html
<script src="https://cdn.jsdelivr.net/npm/p5@1.9.4/lib/p5.min.js"></script>
```
- Processing → JavaScript, 아트·시뮬레이션·인터랙티브

### PixiJS — 2D WebGL 렌더러
```html
<script src="https://cdn.jsdelivr.net/npm/pixi.js@8.1.6/dist/pixi.min.js"></script>
```

---

## 27. Audio / Video

### Howler.js — 오디오 재생
```html
<script src="https://cdn.jsdelivr.net/npm/howler@2.2.4/dist/howler.min.js"></script>
```

### Plyr — 비디오 플레이어 (YouTube/Vimeo/HTML5)
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/plyr@3.7.8/dist/plyr.css">
<script src="https://cdn.jsdelivr.net/npm/plyr@3.7.8/dist/plyr.min.js"></script>
```

### WaveSurfer.js — 오디오 파형 시각화
```html
<script src="https://cdn.jsdelivr.net/npm/wavesurfer.js@7.7.15/dist/wavesurfer.min.js"></script>
```

---

## 28. PDF / Document

### PDF.js — PDF 렌더링 (Mozilla)
```html
<script src="https://cdn.jsdelivr.net/npm/pdfjs-dist@4.3.136/build/pdf.min.mjs" type="module"></script>
```

### html2canvas — HTML→Canvas→PNG
```html
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
```

### jsPDF — PDF 생성
```html
<script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js"></script>
```

---

## 29. QR / Barcode

### QRCode.js
```html
<script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
```

### JsBarcode
```html
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js"></script>
```

---

## 30. Clipboard / Share

### clipboard.js
```html
<script src="https://cdn.jsdelivr.net/npm/clipboard@2.0.11/dist/clipboard.min.js"></script>
```

---

## 31. Design Inspiration (디자인 영감 사이트)

### Behance — Adobe 창작자 포트폴리오
https://www.behance.net

### Dribbble — 디자이너 커뮤니티
https://dribbble.com

### Awwwards — 웹 디자인 어워드
https://www.awwwards.com

### SiteInspire — 웹사이트 설계 영감
https://www.siteinspire.com

### Land-book — 랜딩페이지 카탈로그
https://land-book.com

### Mobbin — 앱 UI 스크린샷 모음
https://mobbin.com

### UI Movement — 인터랙션 영감
https://uimovement.com

### Godly — 디자인 패턴 영감
https://godly.website

### Collect UI — UI/UX 스크린샷
https://www.collectui.com

### Lapa Ninja — 랜딩페이지 영감
https://www.lapa.ninja

---

## 32. Color Palette (컬러 팔레트 도구)

### Coolors — AI 컬러 팔레트 생성
https://coolors.co

### Color Hunt — 큐레이션 팔레트
https://colorhunt.co

### Khroma — AI 컬러 학습기
https://www.khroma.co

### Happy Hues — 색상 조합 보기
https://www.happyhues.co

### Muzli Colors — 색상 검색
https://colors.muz.li

### Colormind — 딥러닝 컬러 팔레트
http://colormind.io

### BrandColors — 브랜드 컬러 모음
https://brandcolors.net

### Eva Colors — 접근성 컬러 시스템
https://colors.eva.design

### UI Colors — UI 컬러 팔레트
https://uicolors.app

### ColorSpace — 색상 그라디언트 생성
https://www.colorspace.com

---

## 33. Free Illustrations (무료 일러스트)

### Storyset — 편집 가능 일러스트
https://storyset.com

### unDraw — 오픈소스 일러스트
https://undraw.co

### DrawKit — SVG 일러스트 라이브러리
https://www.drawkit.io

### ManyPixels — 추상 일러스트
https://www.manypixels.co/gallery

### Icons8 Ouch — 일러스트 팩
https://icons8.com/illustrations

### IRA Design — 그래디언트 일러스트
https://iradesign.io

### Humaaans — 캐릭터 조합기
https://www.humaaans.com

### Open Doodles — 손그림 스타일
https://www.opendoodles.com

### Blush — 맞춤형 일러스트
https://blush.design

### Lukasz Adam — 3D 일러스트
https://lukaszadam.com/illustrations

---

## 34. Mockups & Devices (목업)

### Mockup World — 무료 목업 모음
https://www.mockupworld.co

### LS Graphics — PSD 목업 템플릿
https://www.ls.graphics

### Angle.sh — 기기 목업 생성
https://www.angle.sh

### Artboard Studio — 온라인 목업 도구
https://artboard.studio

### Previewed — 자동 목업 생성
https://previewed.app

### Shots.so — 웹사이트 스크린샷
https://shots.so

### Smartmockups — 클라우드 목업 제작
https://smartmockups.com

### Rotato — 3D 기기 뷰
https://www.rotato.app

### Mockuuups Studio — 온라인 목업 생성
https://www.mockuuups.studio

### Screely — 웹사이트 프리젠테이션
https://www.screely.com

---

## 35. Stock Images & Videos (스톡 이미지/영상)

### Pexels — 무료 사진
https://www.pexels.com

### Unsplash — 고품질 무료 사진
https://unsplash.com

### Pixabay — 무료 이미지/영상
https://pixabay.com

### Mixkit — 무료 영상 & 오디오
https://mixkit.co

### Coverr — 무료 비디오 클립
https://coverr.co

### Freepik — 벡터 & 사진
https://www.freepik.com

### Videvo — 무료 비디오 소스
https://www.videvo.net

### Life of Vids — 라이프스타일 영상
https://www.lifeofvids.com

### Burst — 고품질 스톡 사진
https://burst.shopify.com

### Mazwai — 영상 클립 모음
https://www.mazwai.com

---

## 36. Fonts & Typography (폰트 사이트)

### Fontshare — 무료 폰트 라이브러리
https://www.fontshare.com

### DaFont — 창의적 폰트 다운로드
https://www.dafont.com

### Typewolf — 폰트 추천
https://www.typewolf.com

### Fontpair — Google Fonts 조합
https://www.fontpair.co

### Pangram Pangram — 고급 폰트
https://pangrampangram.com

### Velvetyne — 독립 폰트 파운드리
https://www.velvetyne.fr

### WhatFont — 웹 폰트 검사 도구 (Chrome Extension)
https://www.whatfontis.com

### Fontjoy — AI 폰트 쌍 생성
https://fontjoy.com

---

## 37. Animation Tools (서비스형)

### Rive — 인터랙티브 애니메이션 플랫폼
https://rive.app

### Jitter — 애니메이션 설계 도구
https://jitter.video

### Haiku Animator — 모션 디자인
https://www.haikuapp.com

### Principle — 인터랙션 설계
https://principle.app

### Motionity — 웹 애니메이션 빌더
https://www.motionity.app

### Animista — CSS 애니메이션 라이브러리
https://animista.net

### Loading.io — 로딩 애니메이션 생성
https://loading.io

### Keyshape — SVG 애니메이션 도구
https://www.keyshapeapp.com

---

## 38. 3D Design Resources (3D 디자인)

### Spline — 온라인 3D 편집기 (export to web)
https://spline.design

### Blender — 오픈소스 3D 모델링
https://www.blender.org

### Sketchfab — 3D 모델 마켓플레이스
https://sketchfab.com

### Vectary — 온라인 3D 디자인 (Spline 전신)
https://www.vectary.com

### Poly Pizza — 로우폴리 3D 생성기
https://poly.pizza

### CGTrader — 3D 모델 판매
https://www.cgtrader.com

### Clara.io — 온라인 3D 편집
https://clara.io

### Adobe Substance 3D — 3D 텍스처링 & 렌더링
https://www.adobe.com/products/substance3d.html

### Thangs — 3D 모델 공유
https://www.thangs.com

### Dimensions — 3D 모델 검색
https://www.dimensions.com

---

## 39. Icons 추가 (아이콘 라이브러리)

### Remix Icon — 2000+ SVG 아이콘
https://remixicon.com

### Iconoir — 오픈소스 SVG 아이콘
https://iconoir.com

### SVG Repo — SVG 아이콘 저장소
https://www.svgrepo.com

---

## 40. UI/UX Design Tools (서비스형)

### Penpot — 오픈소스 Figma 대안
https://penpot.app

### ProtoPie — 프로토타입 도구
https://www.protopie.io

### UXPin — 디자인 시스템 도구
https://www.uxpin.com

### MockFlow — 와이어프레임 & UI 디자인
https://www.mockflow.com

### Balsamiq — 빠른 와이어프레임
https://balsamiq.com

### Lunacy — 무료 벡터 설계 (Sketch 호환)
https://www.lunacy.dev

### Framer — 프로토타입 & 배포
https://www.framer.com

### Adobe Express — 온라인 디자인 (Adobe 단순 도구)
https://www.adobe.com/express

---

## 카테고리별 추천 조합

### PPT 슬라이드 (정적 캡처)
```text
Animate.css + Iconify + Pretendard + 글래스모피즘 CSS
```

### 인터랙티브 대시보드
```text
Chart.js + GSAP + Tippy.js + Tailwind + Lucide Icons
```

### 랜딩페이지
```text
AOS + anime.js + Swiper + tsParticles + Poppins
```

### 교재 다이어그램
```text
D3.js + Rough.js + Splitting.js + Noto Sans KR
```

### 데모 / 쇼케이스
```text
Three.js/Vanta.js + Lottie + CountUp.js + Canvas Confetti
```
