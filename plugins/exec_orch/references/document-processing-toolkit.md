# Document Processing Toolkit Reference

> **목적**: 4개 플러그인 (design_pdf, design_word, doc_auto, mcp_docs) 이 사용하는 **공통 도구 카탈로그**
> **적용**: PDF · Word · Excel · 마크다운 · OCR · API 문서 · 포맷 변환 · 템플릿
> **사용**: 각 플러그인의 README, SPEC.md, commands/, skills/ 에서 참조
> **갱신**: 월 1회, 새 도구 검증 후 추가 (실제 npm/pip 존재 확인 후만)

---

## 1. PDF 생성 (PDF Generation)

PDF 파일을 처음부터 만드는 도구.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 1.1 | ReportLab | Python PDF 라이브러리 — 프로그래매틱 PDF 생성 | `pip install reportlab` | 레이아웃 제어 강, 저수준 |
| 1.2 | FPDF2 | 간단한 Python PDF 생성 — fpdf 모듈 개선판 | `pip install fpdf2` | 텍스트·이미지·표 기본 |
| 1.3 | WeasyPrint | HTML/CSS → PDF 변환 | `pip install weasyprint` | 웹 레이아웃 그대로 PDF |
| 1.4 | Puppeteer (Node.js) | Chrome 원격 제어 — PDF 내보내기 | `npm install puppeteer` | 고품질, 수초 소요 |
| 1.5 | Playwright (Python) | 웹 자동화 — PDF/PNG 캡처 | `pip install playwright` | headless 지원, cross-browser |
| 1.6 | Prince XML | HTML/CSS → PDF (상용) | `brew install prince` 또는 DL | 고급 CSS 지원, 비용 |
| 1.7 | wkhtmltopdf | 오픈소스 HTML → PDF | `brew install wkhtmltopdf` | 레이아웃 정확, QtWebKit 기반 |
| 1.8 | Sphinx | Python 문서 → PDF | `pip install sphinx` | 도큐먼테이션 전문 |
| 1.9 | pandoc | 범용 문서 변환기 | `brew install pandoc` | 마크다운 → PDF 등 |
| 1.10 | go-echarts | Go 차트 라이브러리 — HTML → PNG → PDF | `go get -u github.com/go-echarts/go-echarts/v2` | 인터랙티브 차트 변환 |

---

## 2. PDF 파싱 (PDF Parsing)

기존 PDF 에서 텍스트·표·메타데이터 추출.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 2.1 | PyPDF2 | PDF 병합·분할·텍스트 추출 | `pip install PyPDF2` | 기본 기능, 안정 |
| 2.2 | pdfplumber | PDF 테이블·텍스트 고정밀 추출 | `pip install pdfplumber` | 테이블 infer 강력 |
| 2.3 | pdfminer.six | PDF 레이아웃 분석 및 텍스트 추출 | `pip install pdfminer.six` | 저수준 제어 |
| 2.4 | camelot-py | PDF 테이블 추출 전문 | `pip install camelot-py[cv]` | cv 옵션 필요 |
| 2.5 | tabula-py | PDF 테이블 추출 (Java 기반) | `pip install tabula-py` | pandas DataFrame 변환 |
| 2.6 | PyMuPDF (fitz) | PDF/XPS 파싱 및 렌더링 | `pip install pymupdf` | 빠른 속도, 메타데이터 |
| 2.7 | pypdfium2 | PDFium 기반 PDF 파싱 | `pip install pypdfium2` | 고속, 정확한 렌더링 |
| 2.8 | pikepdf | PDF 저수준 조작 (C++ 라이브러리) | `pip install pikepdf` | 복잡한 구조 접근 |
| 2.9 | pdf-parse | Node.js PDF 텍스트 추출 | `npm install pdf-parse` | JavaScript 환경 |
| 2.10 | pdfjs-dist | PDF.js 배포판 — 브라우저 PDF 렌더링 | `npm install pdfjs-dist` | 웹 프론트엔드 용 |

---

## 3. PDF 양식 (PDF Forms)

PDF 폼 필드 채우기 및 AcroForms 조작.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 3.1 | pdfrw | PDF 읽고 쓰기 — 양식 필드 조작 | `pip install pdfrw` | AcroForms 지원 |
| 3.2 | PyPDF2 (AcroForms) | PyPDF2 의 양식 필드 기능 | `pip install PyPDF2>=2.0` | merge/update 메서드 |
| 3.3 | pdf-lib | JavaScript PDF 라이브러리 — 양식 채우기 | `npm install pdf-lib` | 브라우저·Node.js 호환 |
| 3.4 | qpdf | C++ PDF 유틸리티 — 폼 지원 | `brew install qpdf` | 저수준 조작 |
| 3.5 | Apache PDFBox | Java PDF 도구 | `mvn dependency:get -Dartifact=org.apache.pdfbox:pdfbox:2.0.x` | JVM 기반 |
| 3.6 | iText | Java PDF 라이브러리 (상용/AGPL) | `mvn add org.itextpdf:itextpdf` | 강력한 양식 지원 |
| 3.7 | PySimpleGUI (PDF 폼) | GUI 폼 → PDF 작성 | `pip install PySimpleGUI` | 원본 PDF X, 새로 생성 |
| 3.8 | pydantic + reportlab | 데이터 검증 + PDF 생성 | `pip install pydantic reportlab` | 스키마 기반 폼 |

---

## 4. PDF 보안 (PDF Security)

PDF 암호화·권한·디지털 서명.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 4.1 | PyPDF2 (encryption) | PDF 암호화/복호화 | `pip install PyPDF2>=2.0` | 사용자·소유자 암호 |
| 4.2 | pikepdf (encryption) | pikepdf 암호화 기능 | `pip install pikepdf` | AES 256-bit |
| 4.3 | qpdf | PDF 보안/암호화 | `brew install qpdf` | C++ 구현, 고속 |
| 4.4 | pdftk-java | PDF 유틸리티 (Java 재구현) | `brew install pdftk-java` | 보안 추가/제거 |
| 4.5 | GhostScript | PostScript/PDF 처리 | `brew install ghostscript` | 암호화 변환 등 |
| 4.6 | pyHanko (암호화) | pyHanko 의 암호화 기능 | `pip install pyhanko` | 디지털 서명 + 암호화 |
| 4.7 | cryptography | Python 암호화 라이브러리 | `pip install cryptography` | PDF 내부 암호화 구현용 |

---

## 5. 전자서명 (Digital Signature)

PDF 에 디지털 서명 추가 및 검증.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 5.1 | pyHanko | PDF 디지털 서명 라이브러리 | `pip install pyhanko[pades]` | PADES/PAdES 준수 |
| 5.2 | endesive | PDF 서명 (Python) | `pip install endesive` | 타임스탬프 지원 |
| 5.3 | Adobe Sign SDK | Adobe Sign API (공식) | `npm install adobe-sign-sdk` | 클라우드 서명 |
| 5.4 | DocuSign SDK | DocuSign API (공식) | `pip install docusign-esign-python-client` | 엔터프라이즈 전자서명 |
| 5.5 | PandaDoc API | PandaDoc 문서 자동화 | REST API / `pip install pandas-doc-python` | 클라우드 기반 |
| 5.6 | OneSpan SDK | OneSpan 전자서명 | 공식 SDK (언어별) | 규제 준수 (eIDAS·ESIGN) |
| 5.7 | M-Trust (한국) | 한국 인증서 기반 서명 | REST API / `pip install m-trust-client` (비공식) | 공공인증서/금융인증서 |
| 5.8 | NPKI (한국) | 전자정부 공인인증서 | 별도 라이브러리 | 한국 정부 규격 |
| 5.9 | cryptography (PKCS#7) | 디지털 인증서 생성 | `pip install cryptography` | 저수준 구현용 |
| 5.10 | openssl (cmd) | OpenSSL 전자서명 | `brew install openssl` | 커맨드라인 유틸리티 |

---

## 6. Word/DOCX (Microsoft Word)

.docx 파일 생성 및 조작.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 6.1 | python-docx | Python DOCX 읽고 쓰기 | `pip install python-docx` | 표·이미지·스타일 |
| 6.2 | docx-template | Jinja2 기반 DOCX 템플릿 엔진 | `pip install docxtpl` | 변수 치환 강력 |
| 6.3 | mammoth | DOCX → HTML 변환 | `npm install mammoth` / `pip install mammoth` | 깨끗한 HTML |
| 6.4 | pandoc | DOCX 양방향 변환 | `brew install pandoc` | 마크다운 ↔ DOCX |
| 6.5 | python-pptx (docx 호환) | python-pptx 와 유사 API | `pip install python-docx` | PPTX 는 별도 |
| 6.6 | libreoffice (headless) | LibreOffice 자동화 (UNO) | `brew install libreoffice` | 모든 MS Office 포맷 |
| 6.7 | unoconv | LibreOffice 파일 변환 | `pip install unoconv` 또는 `brew` | DOCX → PDF/HTML/ODF |
| 6.8 | Office Open XML 스키마 | 저수준 ZIP 조작 | `pip install zipfile` (내장) | .docx = ZIP 이므로 가능 |
| 6.9 | docx2python | DOCX 텍스트·메타데이터 추출 | `pip install docx2python` | 고급 구조 분석 |
| 6.10 | win32com (Windows) | Microsoft Word COM | `pip install pywin32` | 윈도우 Word.Application 직접 제어 |

---

## 7. PowerPoint/PPTX

.pptx 파일 생성 및 편집.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 7.1 | python-pptx | Python PPTX 읽고 쓰기 | `pip install python-pptx` | 슬라이드·도형·텍스트 |
| 7.2 | pptx-template | Jinja2 기반 PPTX 템플릿 | `pip install pptx-template` (커뮤니티) | 변수 치환 |
| 7.3 | LibreOffice (Impress) | LibreOffice PPTX 처리 | `brew install libreoffice` | UNO 자동화 |
| 7.4 | pandoc (PPTX) | PPTX 변환 | `brew install pandoc` | PPTX → markdown/PDF |
| 7.5 | Gamma API | Gamma.app 프로그래매틱 생성 | REST API (`gamma.app/api`) | SaaS 기반 AI 슬라이드 |
| 7.6 | Beautiful Soup + ZIP | PPTX 구조 직접 파싱 | `pip install beautifulsoup4` | XML 기반 조작 |
| 7.7 | odfpy | ODF (LibreOffice) 포맷 | `pip install odfpy` | ODP (OpenDocument Presentation) |
| 7.8 | pillow | 슬라이드 이미지 조작 | `pip install pillow` | 이미지 삽입 전 변환 |
| 7.9 | win32com (PowerPoint) | Windows PowerPoint COM | `pip install pywin32` | 윈도우 PowerPoint.Application |
| 7.10 | aspose-slides | Aspose.Slides (상용 대안) | `pip install aspose-slides` | 엔터프라이즈 |

---

## 8. Excel/XLSX

.xlsx/.xls 파일 생성 및 조작.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 8.1 | openpyxl | Python XLSX 읽고 쓰기 | `pip install openpyxl` | 스타일·차트·포뮬러 |
| 8.2 | xlsxwriter | 최적화된 XLSX 쓰기 | `pip install xlsxwriter` | 쓰기 전용, 빠름 |
| 8.3 | xlrd / xlwt | 오래된 XLS 포맷 | `pip install xlrd xlwt` | .xls 레거시 지원 |
| 8.4 | pandas (to_excel) | pandas DataFrame → Excel | `pip install openpyxl xlsxwriter` + `pandas` | 데이터 과학 표준 |
| 8.5 | pycel | Excel 포뮬러 평가 | `pip install pycel` | Excel 계산 엔진 |
| 8.6 | formulas | Excel 포뮬러 파싱 | `pip install formulas` | 복잡한 수식 분석 |
| 8.7 | ezodf | ODF 스프레드시트 (LibreOffice) | `pip install ezodf` | .ods 파일 |
| 8.8 | LibreOffice (Calc) | LibreOffice Calc 자동화 | `brew install libreoffice` | UNO 기반 |
| 8.9 | unoconv (XLSX) | XLSX 변환 | `pip install unoconv` | XLSX → CSV/PDF |
| 8.10 | win32com (Excel) | Windows Excel COM | `pip install pywin32` | 윈도우 Excel.Application |

---

## 9. OCR (광학 문자 인식)

이미지에서 텍스트 추출.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 9.1 | Tesseract OCR | 오픈소스 OCR 엔진 | `brew install tesseract` | 광범위 언어 지원 |
| 9.2 | pytesseract | Python Tesseract 래퍼 | `pip install pytesseract` | Tesseract 호출 |
| 9.3 | EasyOCR | 심층 학습 기반 OCR | `pip install easyocr` | 고정밀, 여러 언어 |
| 9.4 | PaddleOCR | Baidu Paddle 기반 OCR | `pip install paddleocr` | 한글·중국어 우수 |
| 9.5 | Surya OCR | AI Foundation 최신 OCR | `pip install surya-ocr` | 개선된 정확도 |
| 9.6 | docTR | Mindee 문서 OCR | `pip install python-doctr` | 문서 구조 분석 |
| 9.7 | AWS Textract | Amazon Textract API | AWS SDK / `pip install boto3` | 클라우드 기반, 비용 |
| 9.8 | Google Vision API | Google Cloud Vision | `pip install google-cloud-vision` | 클라우드 기반 |
| 9.9 | Azure Computer Vision | Microsoft Azure OCR | `pip install azure-cognitiveservices-vision-computervision` | 엔터프라이즈 |
| 9.10 | Claude Vision API | Anthropic Claude multimodal | Python/Node SDK | 이미지 해석 (전문) |

---

## 10. 마크다운 변환 (Markdown)

마크다운 ↔ HTML/PDF/DOCX 변환.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 10.1 | pandoc | 범용 문서 변환기 | `brew install pandoc` | 마크다운 ↔ 거의 모든 포맷 |
| 10.2 | markdown-it | JavaScript 마크다운 파서 | `npm install markdown-it` | 빠르고 안전 |
| 10.3 | remark | 통합 마크다운 생태계 | `npm install remark` | 플러그인 기반 |
| 10.4 | marked | JavaScript 마크다운 파서 | `npm install marked` | 간단하고 빠름 |
| 10.5 | python-markdown | Python 마크다운 | `pip install markdown` | 표준 라이브러리 |
| 10.6 | markdown2 | python-markdown 확장판 | `pip install markdown2` | 테이블·각주 등 |
| 10.7 | mistune | Python 마크다운 파서 | `pip install mistune` | 고속, 커스텀 가능 |
| 10.8 | myst-parser | Jupyter MyST 마크다운 | `pip install myst-parser` | 코드·수식 강화 |
| 10.9 | markdown-pdf | 마크다운 → PDF | `npm install markdown-pdf` | Electron 기반 |
| 10.10 | grip | GitHub 마크다운 프리뷰 | `pip install grip` | 로컬 서버 렌더링 |

---

## 11. API 문서 생성 (API Documentation)

자동으로 API 레퍼런스 생성.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 11.1 | Swagger/OpenAPI | API 스펙 표준 | `npm install swagger-ui-express` | YAML/JSON 포맷 |
| 11.2 | Redoc | OpenAPI → 아름다운 HTML 문서 | `npm install redoc-cli` | 원라인 뷰 |
| 11.3 | Stoplight Studio | API 디자인 플랫폼 (GUI) | 다운로드 또는 웹 버전 (`stoplight.io`) | 비주얼 에디터 |
| 11.4 | AsyncAPI | 비동기 API 문서 | `npm install @asyncapi/cli` | Kafka·MQTT 등 |
| 11.5 | Swagger Codegen | 코드 생성 | `npm install @openapitools/openapi-generator-cli` | 클라이언트/서버 생성 |
| 11.6 | Sphinx (REST) | Python API 문서 | `pip install sphinx` | autodoc 플러그인 |
| 11.7 | TypeDoc | TypeScript API 문서 | `npm install typedoc` | TS 주석 → HTML |
| 11.8 | JSDoc | JavaScript API 문서 | `npm install jsdoc` | JS 주석 → HTML |
| 11.9 | Doxygen | C/C++/Java 문서 생성 | `brew install doxygen` | 구조화된 코드 분석 |
| 11.10 | pdoc | Python API 문서 | `pip install pdoc` | 간단한 Python 문서 |

---

## 12. 템플릿 엔진 (Template Engines)

동적 콘텐츠 렌더링.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 12.1 | Jinja2 | Python 템플릿 엔진 | `pip install jinja2` | 표준 Python |
| 12.2 | Handlebars | JavaScript 템플릿 | `npm install handlebars` | {{}} 문법 |
| 12.3 | Mustache | 로직 없는 템플릿 | `npm install mustache` / `pip install pystache` | 단순, 모든 언어 |
| 12.4 | EJS | Embedded JavaScript | `npm install ejs` | Node.js/브라우저 |
| 12.5 | Liquid | Ruby 템플릿 (Shopify) | `npm install liquidjs` / `pip install Liquid` | 확장 가능 |
| 12.6 | Nunjucks | JavaScript Jinja2 대체 | `npm install nunjucks` | Jinja2 와 유사 |
| 12.7 | Pug | 간결한 템플릿 문법 | `npm install pug` | Indentation 기반 |
| 12.8 | Mako | Python 템플릿 (고급) | `pip install mako` | 제어문·상속 강력 |
| 12.9 | Velocity | Java 템플릿 | Maven artifact `org.apache.velocity:velocity` | 엔터프라이즈 |
| 12.10 | Freemarker | Java 템플릿 | Maven artifact `org.freemarker:freemarker` | 복잡한 로직 가능 |

---

## 13. 텍스트/문서 추출 (Text Extraction)

PDF/문서에서 텍스트 및 구조 추출.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 13.1 | textract | 문서 텍스트 추출 (다양한 포맷) | `pip install textract` | PDF·DOCX·XLSX 등 |
| 13.2 | Apache Tika | 문서 메타·콘텐츠 추출 | `brew install tika` / Java | 엔터프라이즈급 |
| 13.3 | unstructured.io | 구조화되지 않은 문서 파싱 | `pip install unstructured` | AI 기반 문서 분해 |
| 13.4 | LangChain loaders | LLM 통합 문서 로더 | `pip install langchain` | RAG용 표준 |
| 13.5 | pypdf + pdfplumber | PDF 고급 추출 | `pip install pypdf pdfplumber` | 텍스트+표 합성 |
| 13.6 | pandoc (텍스트) | 문서 → 평문 | `brew install pandoc` | 모든 포맷 지원 |
| 13.7 | python-docx (텍스트) | DOCX 텍스트 추출 | `pip install python-docx` | 단락·표 구조 유지 |
| 13.8 | Beautiful Soup | HTML 파싱 | `pip install beautifulsoup4` | 구조화된 텍스트 추출 |
| 13.9 | Selenium (웹스크래이핑) | 동적 웹 텍스트 수집 | `pip install selenium` | JavaScript 렌더링 |
| 13.10 | playwright (텍스트) | Playwright 문서 텍스트 | `pip install playwright` | 스크린 텍스트 추출 |

---

## 14. 포맷 변환 (Format Conversion)

문서 포맷 간 변환.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 14.1 | pandoc | 마스터 변환 도구 | `brew install pandoc` | DOCX↔PDF↔MD↔HTML |
| 14.2 | LibreOffice (headless) | Office 파일 변환 | `brew install libreoffice` | 모든 MS/ODF 포맷 |
| 14.3 | unoconv | LibreOffice 변환 래퍼 | `pip install unoconv` | CLI 기반 |
| 14.4 | calibre | 전자책 변환 | `brew install calibre` | EPUB·MOBI·PDF·HTML |
| 14.5 | GhostScript | PostScript/PDF 변환 | `brew install ghostscript` | 저수준 렌더링 |
| 14.6 | ImageMagick | 이미지 포맷 변환 | `brew install imagemagick` | PNG↔JPG↔WEBP 등 |
| 14.7 | ffmpeg | 비디오/오디오 변환 | `brew install ffmpeg` | MP4·MP3·WebM 등 |
| 14.8 | Imagemin | 이미지 최적화 | `npm install imagemin` | PNG/JPG 압축 |
| 14.9 | Sharp | Node.js 이미지 처리 | `npm install sharp` | 고속 리사이즈·변환 |
| 14.10 | Pillow (PIL) | Python 이미지 처리 | `pip install pillow` | 기본 변환 및 필터 |

---

## 15. README/문서 자동화 (Documentation Generators)

프로젝트 문서 자동 생성.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 15.1 | Sphinx | Python 문서 빌더 | `pip install sphinx` | .rst/.md → HTML/PDF |
| 15.2 | MkDocs | Markdown 문서 사이트 | `pip install mkdocs` | 간단한 정적 사이트 |
| 15.3 | Docusaurus | React 기반 문서 프레임워크 | `npm install docusaurus` | 모던한 UI |
| 15.4 | Vitepress | Vue 기반 정적 생성기 | `npm install vitepress` | 빠른 빌드 |
| 15.5 | TypeDoc | TypeScript 자동 문서 | `npm install typedoc` | TS 주석 스캔 |
| 15.6 | pydoc | Python 내장 문서 | Python 내장 | 기본 기능 |
| 15.7 | pdoc3 | Python 간결한 문서 | `pip install pdoc3` | 최소화 설정 |
| 15.8 | Gitbook | 인터랙티브 책 플랫폼 | `npm install gitbook-cli` | 온라인/오프라인 |
| 15.9 | Hugo | 정적 사이트 생성기 | `brew install hugo` | 빠른 빌드 |
| 15.10 | Jekyll | Ruby 정적 생성기 | `gem install jekyll` | GitHub Pages 표준 |

---

## 16. 이미지 처리 (Image Processing)

PDF 및 문서 내 이미지 최적화 및 조작.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 16.1 | Pillow (PIL) | Python 이미지 라이브러리 | `pip install pillow` | 리사이즈·자르기·필터 |
| 16.2 | opencv-python | OpenCV Python 바인딩 | `pip install opencv-python` | 고급 이미지 처리 |
| 16.3 | scikit-image | 이미지 처리 도구 모음 | `pip install scikit-image` | 필터·변환·복원 |
| 16.4 | ImageMagick | 범용 이미지 변환 | `brew install imagemagick` | CLI + C/C++ API |
| 16.5 | Sharp (Node.js) | 고속 이미지 리사이즈 | `npm install sharp` | JPEG·PNG·WebP |
| 16.6 | Imagemin | 이미지 최적화 | `npm install imagemin imagemin-mozjpeg` | 손실/무손실 압축 |
| 16.7 | FFmpeg (이미지) | 비디오·이미지 프레임 추출 | `brew install ffmpeg` | GIF·프레임 변환 |
| 16.8 | Wand | ImageMagick Python 래퍼 | `pip install wand` | ImageMagick 이용 |
| 16.9 | svglib | SVG → PDF/이미지 | `pip install svglib` | 벡터 변환 |
| 16.10 | tinypng / imagemin-tinypng | 이미지 압축 API | `npm install imagemin-tinypng` | 클라우드 압축 |

---

## 17. 메타데이터 (Metadata)

문서 메타데이터 읽기 및 쓰기.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 17.1 | PyPDF2 (메타데이터) | PDF 메타데이터 | `pip install PyPDF2` | 제목·작성자·주제 등 |
| 17.2 | python-docx (props) | DOCX 메타데이터 | `pip install python-docx` | 코어 프로퍼티 |
| 17.3 | piexif | EXIF 메타데이터 (이미지) | `pip install piexif` | JPEG·TIFF |
| 17.4 | Pillow.Image.info | Pillow 이미지 메타 | `pip install pillow` | PNG·GIF 정보 |
| 17.5 | exifread | EXIF 읽기 | `pip install exifread` | 사진 메타데이터 |
| 17.6 | mutagen | 오디오 메타데이터 | `pip install mutagen` | MP3·FLAC·M4A |
| 17.7 | python-magic | 파일 타입 감지 | `pip install python-magic` | MIME 타입 |
| 17.8 | file (CLI) | 파일 타입 명령어 | `brew install file` | 시스템 유틸리티 |
| 17.9 | openpyxl (메타) | XLSX 메타데이터 | `pip install openpyxl` | 시트·통합 문서 정보 |
| 17.10 | lxml | XML 메타데이터 | `pip install lxml` | 저수준 구조 접근 |

---

## 18. 검증 및 품질 (Validation & Quality)

문서 검증, 품질 체크, 접근성.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 18.1 | PyPDF2 (검증) | PDF 구조 검증 | `pip install PyPDF2` | 손상 감지 |
| 18.2 | pikepdf (검증) | pikepdf 유효성 검사 | `pip install pikepdf` | PDF 규격 준수 |
| 18.3 | aXe | 접근성 검사 | `npm install @axe-core/cli` | WCAG 규격 |
| 18.4 | axe-core (Python) | 접근성 테스트 | `pip install axe-core-selenium` | Selenium 통합 |
| 18.5 | pa11y | 접근성 CLI | `npm install pa11y` | 자동화 접근성 감사 |
| 18.6 | verifyElementPresence | 요소 검증 | Selenium/Playwright 내장 | 테스트 자동화 |
| 18.7 | htmllint | HTML 검증 | `npm install htmllint` | HTML 규격 |
| 18.8 | w3c-html-validator | W3C HTML 검증 | `npm install html-validate` | 표준 준수 |
| 18.9 | cssnano | CSS 최적화 | `npm install cssnano` | 스타일시트 성능 |
| 18.10 | eslint | JavaScript 린팅 | `npm install eslint` | 코드 품질 |

---

## 19. 멀티언어 (Multilingual)

다국어 문서 처리 및 번역.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 19.1 | EasyOCR (다국어) | 다국어 OCR | `pip install easyocr` | 한글·중국어·일본어 |
| 19.2 | PaddleOCR (다국어) | Paddle 다국어 OCR | `pip install paddleocr` | 중국어·한글 우수 |
| 19.3 | Google Translate API | Google 번역 | `pip install google-cloud-translate` | 클라우드 기반 |
| 19.4 | Azure Translator | Microsoft 번역 | `pip install azure-cognitiveservices-language-translator` | 엔터프라이즈 |
| 19.5 | translate (Python) | 다중 백엔드 번역 | `pip install translate` | 여러 서비스 지원 |
| 19.6 | Tesseract (다국어) | Tesseract 다국어 모델 | `brew install tesseract` + 언어 팩 | 한글 포함 |
| 19.7 | unicode 처리 | Unicode 정규화 | `pip install unidecode` | 문자 정규화 |
| 19.8 | hangul-utils | 한글 처리 | `pip install hangul-utils` | 초성·중성·종성 |
| 19.9 | jieba | 중국어 분사 | `pip install jieba` | 중문 토크나이저 |
| 19.10 | MeCab | 일본어/한국어 형태소 분석 | `brew install mecab` + 사전 | 고정밀 |

---

## 20. 고급 기능 (Advanced)

특수 목적 처리.

| # | 도구 | 한글 설명 | 설치 | 비고 |
|---|------|---------|------|------|
| 20.1 | plotly | 인터랙티브 차트 | `pip install plotly` | HTML 임베드 가능 |
| 20.2 | matplotlib | 정적 그래프 | `pip install matplotlib` | PNG로 저장 |
| 20.3 | seaborn | 통계 시각화 | `pip install seaborn` | matplotlib 기반 |
| 20.4 | bokeh | 대용량 데이터 시각화 | `pip install bokeh` | 인터랙티브 |
| 20.5 | altair | 선언형 시각화 | `pip install altair` | Vega 기반 |
| 20.6 | mplfinance | 금융 차트 | `pip install mplfinance` | 주식·초 데이터 |
| 20.7 | reportlab (차트) | ReportLab 차트 | `pip install reportlab` | PDF 내 차트 |
| 20.8 | latex (수학) | LaTeX 수식 렌더링 | `pip install latex2mathml` | 수식 변환 |
| 20.9 | sympy | 수학 기호 | `pip install sympy` | 수식 조작 |
| 20.10 | jupyter (notebook) | Jupyter 노트북 변환 | `pip install jupyter nbconvert` | .ipynb → HTML/PDF |

---

## 사용 패턴 (Usage Patterns)

각 플러그인에서 권장하는 도구 조합.

### design_pdf
- **PDF 생성**: ReportLab (저수준 제어) + WeasyPrint (HTML/CSS)
- **파싱**: pdfplumber (표) + PyMuPDF (고속)
- **보안**: PyPDF2 encryption + qpdf
- **서명**: pyHanko

### design_word
- **DOCX 생성**: python-docx + docxtpl (템플릿)
- **변환**: pandoc (마크다운 ↔ DOCX) + unoconv (다중 포맷)
- **추출**: python-docx + docx2python

### doc_auto
- **템플릿 엔진**: Jinja2 (Python) + Handlebars (JavaScript)
- **자동화**: Sphinx (Python) + MkDocs (Markdown)
- **OCR**: EasyOCR + PaddleOCR (한글)
- **포맷 변환**: pandoc (마스터) + LibreOffice headless

### mcp_docs
- **API 문서**: Swagger/OpenAPI + Redoc (렌더링)
- **코드 문서**: TypeDoc (TS) + pdoc (Python)
- **마크다운**: pandoc + remark + markdown-it
- **배포**: MkDocs + Docusaurus (사이트)

---

## 검증 정책 (Verification Policy)

도구 추가 시 다음 확인 필수:

1. **npm/pip 존재**: `npm view <package>` / `pip search <package>` (또는 PyPI 직접)
2. **활성 개발**: 최근 3개월 내 업데이트
3. **라이선스**: MIT/Apache/GPL 확인
4. **호환성**: Python 3.8+, Node.js 14+ 지원
5. **문서**: 공식 README/Wiki 있음
6. **테스트**: 간단한 설치 테스트 완료

---

## 참조

- **plugin.json**: 각 플러그인 마다 dependencies 명시 (이 문서 참조)
- **README.md**: design_pdf, design_word, doc_auto, mcp_docs 각각
- **SPEC.md**: 미래 계획 (Phase 2~3 도구 추가)
- **script examples**: `.claude/scripts/verify-docx-structure.py` 등

---

## 갱신 기록

| 날짜 | 변경 | 버전 |
|------|------|------|
| 2026-05-20 | 최초 작성 — 4개 플러그인 공통 카탈로그 | 1.0 |
| | 20개 카테고리 × 100+ 도구 | |
| | install 검증 정책 추가 | |

**다음 갱신**: 2026-06-20 (월 1회)
