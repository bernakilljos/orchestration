# Print & Publishing Toolkit

> **목적**: 인쇄·출판·전자책 관련 60+ 공통 도구 레퍼런스
> **적용**: 바코드·QR·전자책·타이포그래피·PDF 생성 등
> **최신**: 2026-05-20

---

## 1. 레이아웃 도구 (Layout Engines)

### LaTeX
- **용도**: 학술 논문, 기술 문서, 수식 렌더링
- **특징**: 높은 조판 품질, 수식 강점
- **설치**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install texlive-full texlive-xetex
  
  # macOS
  brew install --cask mactex
  
  # Windows
  choco install miktex
  ```

### InDesign (Scripting)
- **용도**: 프로페셔널 레이아웃, 페이지 마스터
- **특징**: IDML 내보내기, ExtendScript/UVS 스크립팅
- **참고**: 상용, 월 31,500원
- **라이브러리**: `indesign-extendscript` (GitHub), `idstools` (Python wrapper)

### Scribus
- **용도**: 무료 대체, 인쇄 PDF 생성
- **특징**: CMYK 지원, 색상 프로파일
- **설치**:
  ```bash
  sudo apt-get install scribus
  # macOS: brew install scribus
  # Windows: choco install scribus
  ```

### Affinity Publisher
- **용도**: InDesign 대체, 일회 구매 (약 80,000원)
- **특징**: 빠른 성능, 벡터+래스터 혼합
- **설치**: App Store, Microsoft Store

---

## 2. PDF 인쇄 (PDF Generation)

### ReportLab (Python)
- **용도**: 프로그래매틱 PDF 생성, 표, 이미지 임베드
- **특징**: 경량, 한글 지원 가능
- **설치**:
  ```bash
  pip install reportlab
  pip install reportlab[pil]  # 이미지 지원
  ```
- **예시**:
  ```python
  from reportlab.pdfgen import canvas
  from reportlab.lib.pagesizes import A4
  c = canvas.Canvas("output.pdf", pagesize=A4)
  c.drawString(100, 750, "안녕하세요")
  c.save()
  ```

### WeasyPrint (Python)
- **용도**: HTML → PDF 변환, 복잡한 레이아웃
- **특징**: CSS 완전 지원, 반응형
- **설치**:
  ```bash
  pip install weasyprint
  # 의존성: cairo, pango, GdkPixbuf
  # Ubuntu: sudo apt-get install libcairo2-dev libpango-1.0-0 libpango-cairo-1.0-0
  ```
- **예시**:
  ```python
  from weasyprint import HTML
  HTML('input.html').write_pdf('output.pdf')
  ```

### Prince XML
- **용도**: 고급 HTML → PDF (상용, 가격대 높음)
- **특징**: 최고 품질, 자동 페이지 넘김
- **설치**: macOS/Windows/Linux 바이너리

### PagedJS (JavaScript)
- **용도**: 브라우저 기반 인쇄 (오픈소스)
- **특징**: CSS Paged Media 완전 구현
- **설치**:
  ```bash
  npm install pagedjs
  ```
- **예시**:
  ```html
  <script src="https://unpkg.com/pagedjs/dist/paged.polyfill.js"></script>
  ```

### Vivliostyle (오픈소스)
- **용도**: 일본 발 HTML → PDF, 고급 조판
- **특징**: CSS Paged Media, 세로쓰기 지원
- **설치**:
  ```bash
  npm install -g @vivliostyle/cli
  vivliostyle build input.html --output output.pdf
  ```

---

## 3. 전자책 (eBook)

### Calibre
- **용도**: 전자책 변환, 관리, DRM 제거
- **특징**: 다중 포맷 (epub, mobi, azw3, pdf 등)
- **설치**:
  ```bash
  sudo apt-get install calibre
  # macOS: brew install --cask calibre
  # Windows: choco install calibre
  ```
- **명령어**:
  ```bash
  ebook-convert input.html output.epub
  ebook-convert input.epub output.mobi
  ```

### Sigil
- **용도**: EPUB 편집기 (GUI)
- **특징**: 시각 편집, 메타데이터 관리
- **설치**:
  ```bash
  sudo apt-get install sigil
  ```

### ebooklib (Python)
- **용도**: EPUB 프로그래매틱 생성
- **설치**:
  ```bash
  pip install ebooklib
  ```
- **예시**:
  ```python
  from ebooklib import epub
  book = epub.EpubBook()
  book.set_identifier('id123456')
  book.set_title('제목')
  book.set_language('ko')
  # ... 챕터 추가
  epub.write_epub('output.epub', book)
  ```

### Pandoc (epub 변환)
- **용도**: Markdown → EPUB, Docx → EPUB
- **설치**:
  ```bash
  sudo apt-get install pandoc
  ```
- **명령어**:
  ```bash
  pandoc -f markdown -t epub input.md -o output.epub
  ```

### Kindle Create
- **용도**: 아마존 킨들 직출판
- **특징**: MOBI/KPF 생성, 미리보기
- **설치**: Windows/macOS 앱 (무료)

---

## 4. 타이포그래피 (Typography)

### Google Fonts
- **용도**: 웹·출판용 무료 폰트 5,000+
- **사용**: https://fonts.google.com
- **다운로드**:
  ```bash
  # 한글: Noto Sans CJK, Roboto, Montserrat 등
  # 직접 링크: https://fonts.google.com/download?family=Noto+Sans+KR
  ```

### Adobe Fonts
- **용도**: 고급 폰트, Adobe CC 내 무제한
- **가격**: Creative Cloud 구독 포함
- **웹 사용**:
  ```html
  <link rel="stylesheet" href="https://fonts.adobe.com/fonts/...">
  ```

### Variable Fonts
- **용도**: 무게/너비 유동 가능한 단일 파일
- **예시**: Inter, Roboto Flex, IBM Plex
- **웹 로드**:
  ```css
  @font-face {
    font-family: 'Inter';
    src: url('Inter-Variable.woff2');
    font-variation-settings: 'wght' 100 900;
  }
  ```

### fonttools (Python)
- **용도**: 폰트 파일 조작, WOFF 변환
- **설치**:
  ```bash
  pip install fonttools
  ```
- **예시**:
  ```bash
  ttx -o output.ttx font.ttf  # TTF → XML
  woff2_compress font.ttf      # TTF → WOFF2
  ```

---

## 5. 이미지 최적화 (Image Optimization)

### Sharp (Node.js)
- **용도**: 빠른 이미지 리사이즈, 포맷 변환
- **특징**: libvips 기반, 멀티포맷 (jpeg, png, webp, avif)
- **설치**:
  ```bash
  npm install sharp
  ```
- **예시**:
  ```javascript
  const sharp = require('sharp');
  sharp('input.jpg')
    .resize(800, 600)
    .webp({ quality: 80 })
    .toFile('output.webp');
  ```

### ImageMagick
- **용도**: 명령줄 이미지 처리
- **특징**: 마스크, 워터마크, 배치
- **설치**:
  ```bash
  sudo apt-get install imagemagick
  convert input.jpg -resize 800x600 output.webp
  ```

### Squoosh (Google)
- **용도**: 웹 기반 이미지 압축
- **사용**: https://squoosh.app (CLI 도 있음)
- **설치** (CLI):
  ```bash
  npm install -g @squoosh/cli
  squoosh-cli --output-dir=out input.jpg
  ```

### TinyPNG API
- **용도**: 무손실 PNG/JPEG 압축 (API 기반)
- **가격**: 월 500회 무료
- **사용**:
  ```bash
  curl https://api.tinify.com/output \
    # --user "api:$TINIFY_KEY" \
    -d @input.png -o output.png
  ```

### SVGO (SVG Optimizer)
- **용도**: SVG 파일 최소화
- **설치**:
  ```bash
  npm install -g svgo
  svgo input.svg -o output.svg
  ```

---

## 6. 색상 관리 (Color Management)

### ICC 프로파일
- **용도**: CMYK, RGB, 인쇄소 색상 정확도
- **다운로드**: 인쇄소·제조사 제공
- **포함**:
  ```bash
  # ImageMagick으로 프로파일 임베드
  convert input.jpg -profile sRGB.icc -profile CMYK.icc output.pdf
  ```

### colorama (Python)
- **용도**: 터미널 색상 출력 (ANSI)
- **설치**:
  ```bash
  pip install colorama
  ```

### colour-science (Python)
- **용도**: 고급 색상 변환, CIE LAB, 색온도
- **설치**:
  ```bash
  pip install colour-science
  ```
- **예시**:
  ```python
  from colour import RGB_to_CMYK
  cmyk = RGB_to_CMYK([1, 0, 0])  # 빨강 → CMYK
  ```

### CMYK 변환 도구
- **온라인**: https://www.online-convert.com
- **로컬** (Python):
  ```bash
  pip install Pillow
  # PIL.Image.convert('CMYK') 사용
  ```

---

## 7. 바코드/QR (Barcode & QR)

### python-barcode
- **용도**: 바코드 생성 (CODE128, EAN, ISBN 등)
- **설치**:
  ```bash
  pip install python-barcode
  ```
- **예시**:
  ```python
  from barcode import EAN13
  ean = EAN13('5901234123457')
  ean.save('barcode.png')
  ```

### qrcode (Python)
- **용도**: QR 코드 생성
- **설치**:
  ```bash
  pip install qrcode[pil]
  ```
- **예시**:
  ```python
  import qrcode
  qr = qrcode.QRCode(version=1, box_size=10)
  qr.add_data('https://example.com')
  qr.make()
  img = qr.make_image(fill_color="black", back_color="white")
  img.save('qrcode.png')
  ```

### zxing (Java)
- **용도**: 바코드/QR 인식, 생성
- **설치**:
  ```bash
  # Windows/macOS
  brew install zxing-cpp  # C++ 버전
  ```

### jsbarcode (JavaScript)
- **용도**: 웹 기반 바코드
- **설치**:
  ```bash
  npm install jsbarcode
  ```
- **예시**:
  ```html
  <script src="https://cdn.jsdelivr.net/npm/jsbarcode"></script>
  <svg id="barcode"></svg>
  <script>
    JsBarcode("#barcode", "1234567890128", {format: "CODE128"});
  </script>
  ```

---

## 8. 라벨/스티커 (Label & Sticker)

### brother_ql (Python)
- **용도**: Brother QL 라벨 프린터 제어
- **설치**:
  ```bash
  pip install brother_ql
  ```
- **예시**:
  ```bash
  brother_ql -b usb -d QL-800 print -l 29x90 label.pdf
  ```

### DYMO SDK
- **용도**: DYMO 라벨 프린터 제어
- **설치**: Windows/macOS SDK (상용)
- **라이센스**: 무료 API

### ZPL (Zebra 프린터 언어)
- **용도**: Zebra 산업용 라벨 프린터
- **특징**: 직접 바이너리 명령어
- **예시**:
  ```text
  ^XA
  ^FO50,50
  ^A0N,28,28
  ^FDHello World^FS
  ^XZ
  ```

---

## 9. 3D 프린팅 (3D Printing)

### OctoPrint
- **용도**: 3D 프린터 웹 제어
- **설치**:
  ```bash
  pip install octoprint
  ```

### Cura (Ultimaker)
- **용도**: 3D 모델 슬라이싱
- **설치**:
  ```bash
  sudo apt-get install cura
  ```

### PrusaSlicer
- **용도**: Prusa 3D 프린터 슬라이싱
- **다운로드**: https://www.prusa3d.com/en/product/prusaslicer3/

### OpenSCAD
- **용도**: 파라메트릭 3D 모델링
- **설치**:
  ```bash
  sudo apt-get install openscad
  ```

### FreeCAD
- **용도**: 범용 3D CAD (무료)
- **설치**:
  ```bash
  sudo apt-get install freecad
  ```

---

## 10. 한국 출판 (Korean Publishing)

### ISBN 신청
- **기관**: 국립중앙도서관 (ISBN 관리기관)
- **과정**:
  1. 출판사 신청 (또는 개인 출판사 등록)
  2. ISBN 신청 (https://www.isbn.or.kr)
  3. CIP 신청 (필수)
  4. 납본 (2부, 국립중앙도서관 + 국회도서관)
- **비용**: 1개 ISBN 4,000원 (최소 10개 신청)

### CIP (Cataloging-in-Publication)
- **용도**: 책 본문 뒷표지 인쇄 정보
- **신청**: 국립중앙도서관 (ISBN 신청 후 자동 할당)
- **형식**:
  ```text
  CIP2024000123
  ```

### 교보/알라딘 API
- **용도**: 온라인 서점 연동
- **교보**: https://api.kyobobook.co.kr
- **알라딘**: https://api.aladin.co.kr
- **데이터**: ISBN, 가격, 재고, 순위

### 한글 폰트 라이센스
- **무료**: Noto Sans CJK, IBM Plex Sans KR, 함초롱 바탕
- **상용**: 모던한글, 윤디자인, 타이포그래피서울
- **확인**: 라이센스 명시 (특히 상용 출판 시)

---

## 통합 워크플로우 예시

```bash
# 1. HTML → PDF
weasyprint input.html output.pdf

# 2. PDF → 이미지 (미리보기)
convert -density 150 output.pdf page-%d.png

# 3. 이미지 최적화
sharp input.png -o optimized.webp

# 4. EPUB 생성
pandoc output.pdf -o book.epub

# 5. ISBN/CIP 신청 (수동)
# → 국립중앙도서관 웹사이트

# 6. QR 코드 생성 (프로모션용)
python -c "
import qrcode
qr = qrcode.QRCode()
qr.add_data('https://example.com/book')
qr.make()
qr.make_image().save('promo.png')
"
```

---

## 참조

- ReportLab 공식: https://www.reportlab.com/
- WeasyPrint: https://weasyprint.org/
- Calibre: https://calibre-ebook.com/
- 국립중앙도서관 ISBN: https://www.isbn.or.kr
- Google Fonts: https://fonts.google.com
