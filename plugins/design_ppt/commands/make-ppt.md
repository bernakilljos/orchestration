---
description: "PPT 자동 생성 — HTML/CSS → Playwright → PPTX (고품질) + python-pptx (간단용)"
allowed-tools: Bash(python:*), Bash(playwright:*)
---

## 두 가지 경로

### 경로 A: HTML/CSS 기반 (권장 — 고품질)

**사용 시기**: 프레젠테이션·발표·외부 공유용. 웹디자인 품질 필요.

#### 1. 슬라이드 설계 (Claude)

각 슬라이드 제목, 본문, 요점 정의:
- 슬라이드별 구조 수립
- 섹션 분류 (Part 1~4)
- 핵심 메시지 추출

#### 2. HTML 생성

`outputs/ppt/html-source/slides/slide-NN.html` 작성:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>슬라이드 제목</title>
  <!-- 필수 폰트 & 스크립트 -->
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  
  <!-- Mermaid (다이어그램 필요 시) -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  
  <!-- Iconify (아이콘 필요 시) -->
  <script src="https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js"></script>
  
  <!-- 디자인 시스템 -->
  <link href="../styles/design-system.css" rel="stylesheet">
</head>
<body>
  <div class="slide part-1">
    <!-- 컨텐츠 -->
  </div>
</body>
</html>
```

#### 3. 자산 활용 (인증 없이 즉시)

**Mermaid.js** — 다이어그램 자동 생성:
```html
<div class="mermaid-wrapper">
  <div class="mermaid">
    graph LR
      A[시작] --> B[처리] --> C[결과]
  </div>
</div>
```

**Iconify** — 200K+ 무료 SVG 아이콘:
```html
<iconify-icon icon="heroicons:check-circle" class="icon-success icon-md"></iconify-icon>
```

**Unsplash Source** — 무료 고해상도 사진:
```html
<div class="hero-bg" style="background-image: url('https://source.unsplash.com/1920x1080/?architecture,minimal');"></div>
```

**추가 폰트** — Fraunces(serif), Inter, Crimson Pro:
```html
<h1 class="display-serif">대형 제목</h1>
<p class="font-sans-alt">본문</p>
```

#### 4. 렌더링 및 조립

```bash
python .claude/scripts/generate-final-ppt.py
```

이 스크립트가:
- 각 HTML 파일을 Playwright 로 렌더 (PNG 변환)
- python-pptx 로 PNG 를 PPTX 슬라이드로 조립
- `outputs/ppt/orchestration-v1-FINAL.pptx` 생성

#### 5. 파일 확인

```bash
ls -lh outputs/ppt/orchestration-v1-FINAL.pptx
```

**소요 시간**:
- 초기 설계 + HTML: 1~2시간
- 재렌더링: 5분

---

### 경로 B: python-pptx 기반 (빠른 draft)

**사용 시기**: 사내 빠른 공유, 단순 레이아웃.

#### 1. 스크립트 작성

`.claude/scripts/generate-<topic>-ppt.py` 직접 작성:
```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
# 도형·표·텍스트 추가
prs.save('outputs/ppt/draft.pptx')
```

#### 2. 즉시 실행

```bash
python .claude/scripts/generate-<topic>-ppt.py
```

**소요 시간**: 30분~1시간

---

## 기본값: 경로 A (HTML/CSS)

특별 요청 없으면 A 선택.
사용자가 "빨리", "draft", "초안" 언급하면 B.

---

## 생성 후 검증

```bash
# 1. 파일 존재 확인
ls -lh outputs/ppt/orchestration-v1-FINAL.pptx

# 2. 크기 확인 (일반적으로 5~50MB, Unsplash 이미지 포함 시 더 클 수 있음)

# 3. 슬라이드 수 (메타데이터 확인, 선택사항)
unzip -l outputs/ppt/orchestration-v1-FINAL.pptx | grep -c "slide"

# 4. 브라우저/PowerPoint에서 수동 확인
```

---

## 설계 시스템 (design-system.css)

- **팔레트**: cream, gold, sage, terracotta, plum
- **타이포그래피**: display-xxl ~ caption, mono
- **컴포넌트**: slide, bullet-box, stat-display, plugin-grid
- **Phase 1 추가** (2026-04-24):
  - Mermaid 테마 + 스타일
  - Iconify 유틸 클래스
  - Unsplash 배경 스타일
  - 추가 폰트 클래스 (display-serif, font-serif, font-sans-alt)

자세히: `outputs/ppt/html-source/styles/design-system.css`

---

## 제한사항 & 주의

- **네트워크 필수**: Playwright 렌더 중 CDN(Google Fonts, Iconify, Unsplash) 접속 필요
- **Unsplash 차단**: 특정 네트워크에서 차단 시 → 단색 그라디언트로 fallback
- **Mermaid 폰트**: Pretendard 웹폰트 로드 필수 (프로젝트 팔레트 유지)
- **슬라이드 5장 이상 수정**: 초기 설계 일관성 확인 필수

---

## 예시: 새 슬라이드 추가

1. `outputs/ppt/html-source/slides/slide-NN.html` 작성 (기존 슬라이드 복사 후 수정)
2. Head에 필요 스크립트 추가 (Mermaid, Iconify 필요 시)
3. `python .claude/scripts/generate-final-ppt.py` 실행
4. `outputs/ppt/orchestration-v1-FINAL.pptx` 갱신 확인

---

## 커밋 후

```bash
git add outputs/ppt/ plugins/design_ppt/
git commit -m "feat/update: PPT 업그레이드 — <주제>"
git push
```
