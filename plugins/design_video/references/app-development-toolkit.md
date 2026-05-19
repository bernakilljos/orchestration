# App Development Toolkit — 모바일·데스크톱·웹앱·접근성·국제화·SEO·성능

> **목적**: 앱 개발 전 영역 (모바일·데스크톱·접근성·i18n·SEO·성능) 통합 레퍼런스

---

## 1. 모바일 앱 개발

### 크로스플랫폼
| 프레임워크 | 언어 | 특장 | 설치 |
|-----------|------|------|------|
| **React Native** | JS/TS | 가장 큰 생태계, Expo로 간편 | `npx create-expo-app` |
| **Flutter** | Dart | 네이티브 성능, 아름다운 UI | flutter.dev |
| **Kotlin Multiplatform** | Kotlin | 로직 공유, UI 네이티브 | JetBrains |
| **Capacitor** | Web→네이티브 | 웹앱→모바일 래핑 | `npm install @capacitor/core` |
| **.NET MAUI** | C# | Microsoft 크로스플랫폼 | Visual Studio |

### 네이티브
| 플랫폼 | 언어 | UI 프레임워크 |
|--------|------|-------------|
| **iOS** | Swift | SwiftUI / UIKit |
| **Android** | Kotlin | Jetpack Compose / XML |

### React Native + Expo (가장 빠른 시작)
```bash
npx create-expo-app my-app
cd my-app && npx expo start
# QR 스캔으로 즉시 폰에서 실행
```

### Flutter
```bash
flutter create my_app
cd my_app && flutter run
```

### 모바일 필수 라이브러리
```bash
# React Native
npm install react-navigation @react-native-async-storage/async-storage
npm install react-native-reanimated react-native-gesture-handler
npm install @tanstack/react-query axios

# Flutter
flutter pub add dio provider go_router flutter_riverpod
```

---

## 2. 데스크톱 앱 개발

| 프레임워크 | 언어 | 번들 크기 | 특장 |
|-----------|------|----------|------|
| **Tauri** | Rust + Web | ~3MB | 가장 가볍고 빠름 (2026 추천) |
| **Electron** | JS | ~80MB | 가장 큰 생태계 (VSCode, Slack) |
| **Wails** | Go + Web | ~8MB | Go 백엔드 + 웹 프론트 |
| **Neutralinojs** | JS | ~2MB | 초경량 |
| **Flutter Desktop** | Dart | ~20MB | 크로스플랫폼 (모바일+데스크톱) |
| **PyQt / PySide** | Python | ~30MB | Python GUI 표준 |
| **Tkinter** | Python | 내장 | Python 기본 GUI |
| **Flet** | Python | ~20MB | Flutter 기반 Python UI |
| **Dear PyGui** | Python | ~10MB | GPU 가속 Python GUI |

### Tauri (2026 추천)
```bash
npm create tauri-app@latest
cd my-app && npm run tauri dev
```

### Electron
```bash
npm init electron-app@latest my-app
cd my-app && npm start
```

### Python GUI (Flet — 가장 모던)
```bash
pip install flet
```
```python
import flet as ft

def main(page: ft.Page):
    page.title = "My App"
    page.add(ft.Text("Hello!"), ft.ElevatedButton("Click me"))

ft.app(main)
```

---

## 3. 접근성 (a11y)

### 표준
| 표준 | 설명 |
|------|------|
| **WCAG 2.2** | 웹 접근성 가이드라인 (A/AA/AAA) |
| **WAI-ARIA** | 스크린리더용 역할·속성 |
| **Section 508** | 미국 연방 접근성 법 |

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **axe-core** | 접근성 자동 테스트 엔진 | `npm install axe-core` |
| **Lighthouse** | Chrome 접근성 점수 | Chrome 내장 |
| **pa11y** | CLI 접근성 테스트 | `npm install -g pa11y` |
| **Storybook a11y** | 컴포넌트 접근성 체크 | `npm install @storybook/addon-a11y` |
| **eslint-plugin-jsx-a11y** | React 접근성 린트 | `npm install eslint-plugin-jsx-a11y` |
| **Colour Contrast Checker** | 색상 대비 검사 | webaim.org/resources/contrastchecker |
| **NVAccess NVDA** | 무료 스크린리더 (Windows) | nvaccess.org |
| **VoiceOver** | macOS/iOS 스크린리더 | 내장 |

### HTML 접근성 필수 패턴
```html
<!-- 이미지 대체 텍스트 -->
<img src="chart.png" alt="2026년 매출 추이 그래프 — 1분기 30억, 2분기 45억">

<!-- 폼 라벨 -->
<label for="email">이메일</label>
<input id="email" type="email" aria-required="true">

<!-- 스킵 내비게이션 -->
<a href="#main-content" class="skip-link">본문으로 건너뛰기</a>

<!-- ARIA 라이브 영역 (동적 알림) -->
<div role="alert" aria-live="polite">저장되었습니다</div>

<!-- 키보드 접근성 -->
<button onclick="submit()" onkeypress="submit()">제출</button>
```

---

## 4. 국제화 (i18n) / 다국어

### JavaScript
| 라이브러리 | 특장 | 설치 |
|-----------|------|------|
| **i18next** | JS i18n 표준 (React/Vue/Node) | `npm install i18next react-i18next` |
| **FormatJS (react-intl)** | ICU 메시지 포맷 | `npm install react-intl` |
| **Lingui** | 컴파일 타임 i18n (가벼움) | `npm install @lingui/react` |
| **next-intl** | Next.js i18n | `npm install next-intl` |
| **vue-i18n** | Vue i18n | `npm install vue-i18n` |

### Python
```bash
pip install babel             # 날짜·숫자·통화 로케일
pip install python-i18n       # 간단한 i18n
pip install gettext           # GNU gettext (표준)
```

### 번역 서비스
| 서비스 | 특장 | 무료 |
|--------|------|------|
| **Crowdin** | 번역 관리 플랫폼 | ✅ (오픈소스) |
| **Lokalise** | 번역 + CI 통합 | ✅ (무료 티어) |
| **Phrase** | 번역 관리 | ✅ (무료 티어) |
| **DeepL API** | AI 번역 | ✅ (500k 문자/월) |
| **Papago API** | 한국어 번역 최강 | ✅ (10k/일) |

---

## 5. SEO (검색엔진 최적화)

### 메타태그 필수
```html
<head>
  <title>페이지 제목 — 사이트명</title>
  <meta name="description" content="페이지 설명 (150자 이내)">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://example.com/page">

  <!-- Open Graph (소셜 공유) -->
  <meta property="og:title" content="제목">
  <meta property="og:description" content="설명">
  <meta property="og:image" content="https://example.com/og-image.jpg">
  <meta property="og:url" content="https://example.com/page">
  <meta property="og:type" content="website">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">

  <!-- JSON-LD 구조화 데이터 -->
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"WebPage","name":"제목","description":"설명"}
  </script>
</head>
```

### SEO 도구
| 도구 | 특장 | 무료 |
|------|------|------|
| **Google Search Console** | 검색 성능 분석 | ✅ |
| **Google Analytics 4** | 웹 분석 | ✅ |
| **Ahrefs** | 백링크·키워드 분석 | 유료 ($99/월~) |
| **Semrush** | SEO 올인원 | 유료 ($130/월~) |
| **Screaming Frog** | 사이트 크롤러 | ✅ (500 URL) |
| **Lighthouse** | Core Web Vitals | ✅ (Chrome 내장) |
| **PageSpeed Insights** | 페이지 속도 분석 | ✅ |
| **Sitemap Generator** | XML 사이트맵 | ✅ |

### 프레임워크별 SEO
```bash
# Next.js — SSR + 메타태그
npm install next-seo

# Nuxt — 자동 SEO
npm install @nuxtjs/seo

# Astro — 정적 사이트 (SEO 최적)
npm create astro@latest
```

---

## 6. 성능 최적화

### Core Web Vitals
| 지표 | 목표 | 측정 |
|------|------|------|
| **LCP** (Largest Contentful Paint) | < 2.5초 | 메인 콘텐츠 로드 |
| **INP** (Interaction to Next Paint) | < 200ms | 인터랙션 응답 |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 레이아웃 안정성 |

### 프론트엔드 성능
```bash
# 번들 분석
npm install webpack-bundle-analyzer
npm install @next/bundle-analyzer

# 이미지 최적화
npm install sharp                    # 서버사이드 이미지 최적화
npm install @squoosh/lib             # Squoosh (Google)
pip install pillow                   # Python 이미지 최적화
```

```html
<!-- 이미지 지연 로딩 -->
<img src="photo.jpg" loading="lazy" decoding="async" alt="설명">

<!-- 폰트 프리로드 -->
<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>

<!-- 리소스 힌트 -->
<link rel="dns-prefetch" href="//api.example.com">
<link rel="preconnect" href="https://cdn.example.com">
```

### 백엔드 성능
```bash
pip install cachetools          # Python 캐시
pip install aiocache            # async 캐시
pip install orjson              # 빠른 JSON (10x)
pip install msgpack             # 바이너리 직렬화
pip install uvloop              # 빠른 이벤트 루프
```

---

## 7. 데이터 엔지니어링

| 도구 | 특장 | 설치 |
|------|------|------|
| **Apache Airflow** | 워크플로우 오케스트레이션 | `pip install apache-airflow` |
| **dbt** | SQL 변환 (ELT) | `pip install dbt-core` |
| **Apache Spark** | 대규모 데이터 처리 | `pip install pyspark` |
| **Polars** | Rust 기반 고속 데이터프레임 | `pip install polars` |
| **DuckDB** | 인메모리 분석 DB | `pip install duckdb` |
| **Dagster** | 데이터 오케스트레이션 (Airflow 대안) | `pip install dagster` |
| **Prefect** | 워크플로우 (Airflow 대안) | `pip install prefect` |
| **Great Expectations** | 데이터 품질 검증 | `pip install great-expectations` |
| **Apache Kafka** | 이벤트 스트리밍 | Docker |
| **Debezium** | CDC (Change Data Capture) | Docker |
| **Fivetran** | ETL SaaS | 유료 |
| **Airbyte** | 오픈소스 ETL | ✅ |

---

## 8. 사이버보안

| 도구 | 특장 | 설치 |
|------|------|------|
| **Burp Suite** | 웹 보안 테스트 표준 | Community 무료 |
| **OWASP ZAP** | 오픈소스 웹 스캐너 | ✅ |
| **Metasploit** | 침투 테스트 프레임워크 | ✅ (Community) |
| **Nmap** | 네트워크 스캐너 | ✅ |
| **Wireshark** | 패킷 분석 | ✅ |
| **Ghidra** | 리버스 엔지니어링 (NSA) | ✅ |
| **Kali Linux** | 보안 테스트 OS | ✅ |
| **Snyk** | 의존성 취약점 스캔 | ✅ (무료 티어) |
| **Trivy** | 컨테이너 보안 스캔 | ✅ |
| **Gitleaks** | Git 시크릿 스캔 | ✅ (이미 설치) |
| **Semgrep** | 코드 패턴 보안 스캔 | ✅ (이미 설치) |

```bash
pip install bandit            # Python 보안 (이미 설치)
pip install safety            # 의존성 취약점
pip install pwntools          # CTF/익스플로잇 개발
```

---

## 9. 교육 / 학습 리소스

### 무료 학습 플랫폼
| 플랫폼 | 특장 | 무료 |
|--------|------|------|
| **freeCodeCamp** | 풀스택 웹 (인증서) | ✅ |
| **The Odin Project** | 웹 개발 로드맵 | ✅ |
| **CS50** | Harvard CS 입문 | ✅ |
| **Codecademy** | 인터랙티브 코딩 | ✅ (기본) |
| **Scrimba** | 인터랙티브 강의 | ✅ (일부) |
| **인프런** | 한국 개발 강의 | ✅ (일부) |
| **노마드 코더** | 한국 실전 코딩 | ✅ (일부) |
| **생활코딩** | 한국 무료 코딩 | ✅ |

### 개발 로드맵
| 리소스 | URL |
|--------|-----|
| **roadmap.sh** | 프론트/백/DevOps/AI 로드맵 |
| **Developer Roadmap** | github.com/kamranahmedse/developer-roadmap |
| **Awesome** | github.com/sindresorhus/awesome |
| **Build Your Own X** | github.com/codecrafters-io/build-your-own-x |
| **System Design Primer** | github.com/donnemartin/system-design-primer |

### 코딩 챌린지
| 플랫폼 | 특장 |
|--------|------|
| **LeetCode** | 알고리즘 (면접 준비) |
| **HackerRank** | 코딩 챌린지 + 인증서 |
| **Codewars** | 카타 (난이도별) |
| **Advent of Code** | 매년 12월 퍼즐 |
| **Project Euler** | 수학 + 프로그래밍 |
| **프로그래머스** | 한국 코딩 테스트 |
| **백준** | 한국 알고리즘 |

---

## 10. 하드웨어 / 임베디드

| 플랫폼 | 특장 | 가격 |
|--------|------|------|
| **Raspberry Pi 5** | 리눅스 보드 (교육, IoT) | $60 |
| **Arduino** | 마이크로컨트롤러 (입문) | $25 |
| **ESP32** | Wi-Fi + BLE (IoT) | $5 |
| **Jetson Nano** | NVIDIA GPU (AI) | $149 |
| **Micro:bit** | 교육용 마이크로컨트롤러 | $15 |
| **STM32** | ARM Cortex-M (프로덕션) | $5~ |

### Python 하드웨어
```bash
pip install RPi.GPIO          # 라즈베리파이 GPIO
pip install gpiozero          # GPIO 간편 API
pip install pyserial          # 시리얼 (Arduino)
pip install micropython       # MicroPython (ESP32)
pip install circuitpython     # CircuitPython (Adafruit)
pip install pyfirmata         # Firmata (Arduino 제어)
```

### FPGA
| 도구 | 특장 |
|------|------|
| **Vivado** | Xilinx FPGA IDE |
| **Quartus** | Intel FPGA IDE |
| **Yosys** | 오픈소스 합성 |
| **nMigen/Amaranth** | Python HDL |
| **SpinalHDL** | Scala HDL |
