# Python Toolkit — pip 패키지 카탈로그

> **목적**: `pip install <package>` 로 즉시 사용 가능한 도구 모음
> **용도**: 빌더 스크립트, 자동화, 데이터 처리, 이미지/영상 보정, AI, 테스트

---

## 1. Image Processing (이미지 보정·처리)

### 기본
```bash
pip install pillow            # PIL 후속 — 리사이즈, 크롭, 필터, 포맷 변환
pip install opencv-python     # OpenCV — 얼굴 검출, 에지, 컬러 보정, HDR
pip install scikit-image      # 과학 이미지 처리 — 노이즈 제거, 세그멘테이션, 형태학
```

### 보정·향상
```bash
pip install rawpy             # RAW 파일 (.NEF/.CR2/.ARW) 읽기 + 현상
pip install imageio           # 다양한 포맷 I/O (TIFF, GIF, WebP, DICOM)
pip install wand              # ImageMagick 바인딩 — 200+ 필터, 벡터↔래스터
pip install colour-science    # 색 공간 변환 (sRGB↔Lab↔XYZ↔CMYK)
pip install colorcorrect      # 화이트밸런스 자동 보정
pip install autocrop          # 얼굴 기반 자동 크롭 (프로필 사진)
pip install rembg             # AI 배경 제거 (U2-Net)
pip install transparent-background  # 배경 투명화 (InSPyReNet)
```

### AI 초해상도 (Super Resolution)
```bash
pip install realesrgan        # Real-ESRGAN — x2/x4 업스케일 (이미 설치)
pip install basicsr           # 기반 프레임워크 (이미 설치)
pip install swinir            # SwinIR — 트랜스포머 기반 복원
pip install hat               # HAT — 최신 초해상도 (2024 SOTA)
```

### AI 이미지 생성·편집
```bash
pip install diffusers         # Stable Diffusion, SDXL, ControlNet
pip install transformers      # Hugging Face — CLIP, BLIP, SAM
pip install compel            # 프롬프트 가중치 (Stable Diffusion)
pip install controlnet-aux    # ControlNet 전처리 (canny, depth, pose)
pip install segment-anything  # SAM — 클릭 한 번 세그멘테이션
```

### OCR (문자 인식)
```bash
pip install easyocr           # 80+ 언어 OCR (한글 우수)
pip install pytesseract       # Tesseract 바인딩 (설치 별도)
pip install paddleocr         # PaddlePaddle OCR (중국어·한국어 강력)
pip install manga-ocr         # 일본어 만화 OCR
pip install surya-ocr         # 다국어 OCR + 레이아웃 분석
```

### 얼굴·인체
```bash
pip install face-recognition  # 얼굴 인식·비교 (dlib 기반)
pip install deepface          # 얼굴 분석 (나이, 성별, 감정, 인종)
pip install mediapipe         # 포즈, 손, 얼굴 메쉬 (Google)
pip install insightface       # 얼굴 검출·인식 (ArcFace)
pip install codeformer-pip    # CodeFormer — 얼굴 복원 (이미 설치)
```

---

## 2. Video Processing (영상 보정·편집)

### 기본
```bash
pip install moviepy           # 영상 편집 (자르기, 합치기, 자막, 효과)
pip install ffmpeg-python     # FFmpeg Python 바인딩
pip install av                # PyAV — FFmpeg 저수준 바인딩 (빠름)
pip install vidgear           # 멀티 소스 비디오 I/O (YouTube, IP카메라)
pip install decord            # GPU 가속 비디오 디코딩
```

### 보정·향상
```bash
pip install opencv-python     # 비디오 안정화, 컬러 보정, 노이즈 제거
pip install basicvsr          # BasicVSR — 비디오 초해상도
pip install real-esrgan       # 비디오 프레임별 업스케일
```

### AI 영상
```bash
pip install torch torchvision # PyTorch 비전 (객체 검출, 세그멘테이션)
pip install ultralytics       # YOLOv8 — 실시간 객체 검출·추적
pip install supervision       # 비디오 분석 시각화 (바운딩박스, 카운터)
pip install norfair           # 다중 객체 추적 (경량)
```

### 자막·STT
```bash
pip install openai-whisper    # Whisper — 음성→텍스트 (이미 설치)
pip install faster-whisper    # CTranslate2 기반 Whisper (4x 빠름)
pip install pysrt             # SRT 자막 파일 조작
pip install webvtt-py         # WebVTT 자막 조작
pip install subs2cia          # 자막 기반 오디오 추출
```

### 썸네일·GIF
```bash
pip install pygifsicle        # GIF 최적화·압축
pip install imgcat            # 터미널에 이미지 출력
```

---

## 3. Audio Processing (오디오 보정·처리)

```bash
pip install librosa           # 오디오 분석 (스펙트로그램, BPM, 피치)
pip install soundfile         # WAV/FLAC/OGG I/O
pip install pydub             # 오디오 편집 (자르기, 합치기, 볼륨) (이미 설치)
pip install noisereduce       # 노이즈 제거 (이미 설치)
pip install pedalboard        # 오디오 이펙트 (EQ, 리버브, 컴프레서)
pip install demucs            # 스템 분리 (보컬/드럼/베이스/기타) (이미 설치)
pip install spleeter          # 스템 분리 (Deezer)
pip install pyworld           # 보컬 피치 변환
pip install edge-tts          # Microsoft TTS (무료, 한국어)
pip install TTS               # Coqui TTS (로컬, 다국어)
pip install bark              # AI 음성 생성 (효과음 포함)
```

---

## 4. Data / Analytics (데이터 처리·분석)

```bash
pip install pandas            # 데이터프레임 (표 데이터)
pip install polars            # Rust 기반 고속 데이터프레임
pip install numpy             # 수치 연산
pip install scipy             # 과학 계산
pip install openpyxl          # Excel 읽기/쓰기 (이미 설치)
pip install xlsxwriter        # Excel 쓰기 (차트 강력)
pip install python-docx       # Word 읽기/쓰기 (이미 설치)
pip install python-pptx       # PowerPoint 읽기/쓰기 (이미 설치)
pip install tabulate          # 콘솔 표 포매팅
pip install rich              # 터미널 Rich text (표, 진행바, 트리)
```

### 시각화
```bash
pip install matplotlib        # 기본 차트 (이미 설치 예정)
pip install seaborn           # 통계 시각화 (matplotlib 기반)
pip install plotly            # 인터랙티브 차트 (HTML 출력)
pip install altair            # 선언적 시각화
pip install bokeh             # 대시보드용 인터랙티브 차트
pip install pygwalker         # 판다스 → Tableau 스타일 탐색
```

### 금융 / 주식 / 시뮬레이션
```bash
pip install yfinance          # 주식·ETF 시세 (Yahoo Finance)
pip install backtrader        # 주식 백테스팅 프레임워크
pip install zipline-reloaded  # 알고리즘 트레이딩 백테스트 (Quantopian)
pip install ta                # 기술 지표 (RSI, MACD, 볼린저밴드)
pip install ta-lib            # 기술 지표 (C 기반, 빠름)
pip install quantlib          # 금융 공학 (옵션·채권·금리)
pip install empyrical         # 포트폴리오 성과 분석
pip install pyfolio           # 포트폴리오 시각화
pip install simpy             # 이산 이벤트 시뮬레이션
pip install mesa              # 에이전트 기반 시뮬레이션 (ABM)
pip install gym               # 강화학습 환경 (시뮬레이션)
```

### 과학 / 공학 / 물리 시뮬레이션
```bash
pip install scipy             # 과학 계산 (미분·적분·최적화)
pip install sympy             # 기호 수학 (수식 계산)
pip install pybullet          # 3D 물리 시뮬레이션
pip install pymunk            # 2D 물리 (Chipmunk)
pip install fenics            # 유한요소법 (FEM)
pip install openmdao          # 다학제 최적화
pip install astropy           # 천문학 계산
```

### 의료 / 바이오
```bash
pip install biopython         # 생물정보학 (DNA·단백질)
pip install nibabel           # 의료 영상 (NIfTI, DICOM)
pip install pydicom           # DICOM 의료 이미지
pip install monai             # 의료 AI (PyTorch 기반)
pip install lifelines         # 생존 분석
pip install mne               # 뇌파(EEG) 분석
```

### 법률 / 문서 분석
```bash
pip install spacy             # NLP (개체명 인식, 구문 분석)
pip install konlpy            # 한국어 NLP (형태소 분석)
pip install kiwipiepy         # Kiwi 한국어 형태소 (빠름)
pip install sentence-transformers  # 문장 임베딩 (유사도 검색)
pip install docx2txt          # Word 텍스트 추출
pip install pdfplumber        # PDF 텍스트·표 추출
pip install camelot-py        # PDF 표 추출 (정밀)
```

### 회계 / ERP
```bash
pip install openpyxl          # Excel 읽기/쓰기 (이미 설치)
pip install xlsxwriter        # Excel 쓰기 (차트·서식 강력)
pip install python-barcode    # 바코드 생성
pip install qrcode            # QR 코드 생성
pip install num2words         # 숫자→한글 (금삼천만원)
pip install babel             # 통화·날짜 로케일 포맷
```

### 글쓰기 / 출판
```bash
pip install markdown          # Markdown → HTML
pip install python-docx       # Word 생성 (이미 설치)
pip install ebooklib          # EPUB 전자책 생성
pip install weasyprint        # HTML → PDF (CSS 지원)
pip install reportlab         # PDF 프로그래밍 생성
pip install fpdf2             # 경량 PDF 생성
pip install python-pptx       # PPT 생성 (이미 설치)
```

### 영화 / 영상 제작
```bash
pip install moviepy           # 영상 편집 (자르기·합치기·효과) (이미 설치)
pip install colour-science    # 컬러 그레이딩 (DCI-P3, ACES)
pip install nuke              # 합성 (Foundry — 상용)
pip install opencv-python     # VFX 기본 (크로마키·트래킹)
pip install subtitle-parser   # SRT/ASS 자막 파싱
pip install ass               # ASS 자막 (스타일링)
pip install ffmpeg-python     # FFmpeg 바인딩 (인코딩·변환)
```

### 크롤링·스크래핑
```bash
pip install requests          # HTTP 클라이언트
pip install httpx             # async HTTP (requests 후속)
pip install beautifulsoup4    # HTML 파싱
pip install selectolax        # 초고속 HTML 파싱 (Modest 기반)
pip install selenium          # 브라우저 자동화
pip install playwright        # 브라우저 자동화 (Playwright) (이미 설치 예정)
pip install scrapy            # 크롤링 프레임워크
pip install newspaper3k       # 뉴스 기사 추출
pip install trafilatura       # 웹페이지 본문 추출
```

---

## 5. Web Framework (웹 프레임워크)

```bash
pip install fastapi           # 비동기 REST API (타입 힌트 기반)
pip install uvicorn           # ASGI 서버 (FastAPI 실행)
pip install flask             # 경량 웹 프레임워크
pip install django            # 풀스택 웹 프레임워크
pip install streamlit         # 데이터 앱 빌더 (ML 대시보드)
pip install gradio            # AI 데모 UI (Hugging Face)
pip install nicegui           # Python-only 웹 UI (Vue.js 기반)
pip install reflex            # 풀스택 Python 웹앱 (React 기반)
```

---

## 6. AI / ML (인공지능·머신러닝)

```bash
pip install anthropic         # Claude API
pip install openai            # OpenAI API
pip install google-generativeai  # Gemini API
pip install langchain         # LLM 오케스트레이션
pip install langchain-anthropic   # LangChain + Claude
pip install langchain-openai     # LangChain + OpenAI
pip install langgraph         # 그래프 기반 에이전트 워크플로우
pip install langserve         # LangChain 모델 서빙 (API 배포)
pip install langsmith         # LLM 트레이싱+평가+디버깅
pip install llama-index       # RAG 프레임워크
pip install chromadb          # 벡터 DB (이미 설치 가능)
pip install sentence-transformers  # 임베딩 모델
pip install tiktoken          # OpenAI 토크나이저
pip install tokenizers        # Hugging Face 토크나이저
pip install litellm           # 100+ LLM 통합 프록시 (비용 추적)
pip install instructor        # 구조화 LLM 출력 (Pydantic 강제)
pip install outlines          # LLM 출력 제약 (JSON/정규식 강제)
pip install mirascope         # LLM 추상화 (다중 모델)
pip install magentic          # 데코레이터 기반 LLM 호출
pip install dspy-ai           # 프로그래밍 방식 프롬프트 최적화
pip install haystack-ai       # RAG+에이전트 (deepset)
pip install smolagents        # 코드 에이전트 (Hugging Face)
pip install crewai            # 멀티에이전트 팀 (역할 기반)
pip install autogen           # 대화형 멀티에이전트 (MS)
```

### AI 서빙 / 배포
```bash
pip install vllm              # 고속 LLM 서빙 (PagedAttention)
pip install bentoml           # ML 모델 패키징+배포
pip install ray[serve]        # 분산 서빙 (Ray Serve)
pip install modal             # 서버리스 GPU (클라우드)
pip install replicate         # AI 모델 원클릭 배포 (API)
pip install runpod            # GPU 클라우드 (저렴)
pip install together          # 오픈소스 모델 호스팅
pip install groq              # 초고속 추론 API
```

### ML 학습
```bash
pip install scikit-learn      # 전통 ML (분류, 회귀, 클러스터링)
pip install xgboost           # 그래디언트 부스팅
pip install lightgbm          # 경량 그래디언트 부스팅
pip install catboost          # 범주형 변수 강점 부스팅
```

### 딥러닝
```bash
pip install torch torchvision torchaudio  # PyTorch (이미 설치)
pip install timm              # PyTorch Image Models (800+ 사전학습)
pip install accelerate        # 분산 학습 (Hugging Face)
pip install peft              # LoRA/QLoRA 파인튜닝
pip install bitsandbytes      # 양자화 (4bit/8bit)
```

### XAI (설명 가능한 AI)
```bash
pip install shap              # Shapley 값 기반 특성 중요도 (표준)
pip install lime              # 로컬 해석 (개별 예측 설명)
pip install captum            # PyTorch 모델 해석 (Meta)
pip install interpret         # InterpretML (Microsoft XAI 통합)
pip install alibi             # 반사실적 설명 (Counterfactual)
pip install omnixai           # 표/이미지/텍스트 통합 XAI
```

### AI 거버넌스 / 공정성 / 모니터링
```bash
pip install aif360            # AI 공정성 검사 (IBM)
pip install raiwidgets        # Responsible AI Toolbox (Microsoft)
pip install giskard           # ML 모델 검증 + 취약점 탐지
pip install evidently         # ML 모니터링 (데이터 드리프트 감지)
pip install whylogs           # 데이터+모델 관측
pip install guardrails-ai     # LLM 출력 검증
pip install nemoguardrails    # 대화 안전 (NVIDIA)
```

### 합성데이터 (Synthetic Data)
```bash
pip install sdv               # 테이블·시계열·관계형 합성 (MIT)
pip install ctgan             # GAN 기반 테이블 합성
pip install gretel-client     # Gretel 합성데이터 (SaaS)
pip install mimesis           # 고속 가짜 데이터 (100x Faker)
pip install DataSynthesizer   # 차등 프라이버시 합성
pip install ydata-synthetic   # 시계열 합성
```

### 자연어→SQL / 대화형 BI
```bash
pip install vanna             # 자연어→SQL (DB 연동)
pip install chainlit          # LLM 챗 UI
pip install faststream        # Python 이벤트 프레임워크 (Kafka/Redis)
```

### 프라이버시 보호 (PETs)
```bash
pip install opacus            # 차등 프라이버시 (PyTorch)
pip install flwr              # 연합학습 (Flower)
pip install tenseal           # 동형암호 ML
pip install mpyc              # 안전한 다자간 연산 (MPC)
pip install pysyft            # PySyft 프라이버시 보존 ML
```

### 탄소 배출 / Green AI
```bash
pip install codecarbon        # ML 학습 탄소 배출 측정
pip install carbontracker     # GPU 에너지 추적
pip install eco2ai            # 에코 AI 추적
```

---

## 7. Testing (테스트)

```bash
pip install pytest            # Python 표준 테스트
pip install pytest-cov        # 커버리지 리포트
pip install pytest-asyncio    # async 테스트
pip install pytest-mock       # 모킹
pip install hypothesis        # 속성 기반 테스트 (자동 입력 생성)
pip install faker             # 가짜 데이터 생성 (이름, 주소, 전화번호)
pip install factory-boy       # 테스트 팩토리 패턴
pip install responses         # requests 모킹
pip install respx             # httpx 모킹
pip install freezegun         # 시간 고정 (datetime 모킹)
```

---

## 8. Security (보안)

```bash
pip install bandit            # Python 보안 스캔 (이미 설치)
pip install safety            # 의존성 취약점 검사
pip install cryptography      # 암호화 (AES, RSA, X.509)
pip install pyjwt             # JWT 토큰
pip install passlib            # 비밀번호 해싱 (bcrypt, argon2)
pip install python-dotenv     # .env 파일 로드
pip install keyring           # OS 시크릿 저장소
```

---

## 9. CLI / DevTools (개발 도구)

```bash
pip install click             # CLI 프레임워크
pip install typer             # click 위에 타입 힌트 CLI
pip install tqdm              # 진행바
pip install loguru            # 구조화 로깅
pip install pydantic          # 데이터 검증 (FastAPI 기반)
pip install pydantic-settings # 환경변수 → 설정 객체
pip install watchdog          # 파일 변경 감시
pip install schedule          # 간단한 작업 스케줄링
pip install psutil            # 시스템 모니터링 (CPU, 메모리, 프로세스)
pip install py-cpuinfo        # CPU 정보
```

---

## 10. Document / PDF

```bash
pip install PyMuPDF           # PDF 읽기/쓰기/변환 (이미 설치)
pip install reportlab         # PDF 생성 (프로그래밍)
pip install weasyprint        # HTML→PDF (CSS 완벽 지원)
pip install camelot-py        # PDF 표 추출
pip install tabula-py         # PDF 표 추출 (Java 기반)
pip install pdfplumber        # PDF 텍스트·표 추출
pip install pikepdf           # PDF 편집 (워터마크, 암호화)
pip install img2pdf           # 이미지→PDF
pip install ocrmypdf          # PDF OCR 레이어 추가
pip install python-docx       # Word 읽기/쓰기 (이미 설치)
pip install docx2pdf          # Word→PDF
pip install mammoth           # Word→HTML
```

---

## 11. Diagram / Visualization

```bash
pip install diagrams          # 인프라 아키텍처 다이어그램 (코드→PNG)
pip install graphviz          # DOT 언어 다이어그램
pip install networkx          # 그래프/네트워크 분석
pip install pydot             # Graphviz Python 바인딩
pip install drawsvg           # SVG 프로그래밍 생성
pip install cairosvg          # SVG→PNG/PDF 변환
pip install pygal             # SVG 차트 생성
```

---

## 12. Notification / Communication

```bash
pip install slack-sdk         # Slack API
pip install discord.py        # Discord 봇
pip install python-telegram-bot  # Telegram 봇
pip install twilio            # SMS/전화 (Twilio)
pip install resend            # 이메일 전송 (모던 API)
pip install apprise           # 70+ 알림 서비스 통합
```

---

## 13. Cloud / Infrastructure

```bash
pip install boto3             # AWS SDK
pip install google-cloud-storage  # GCP Storage
pip install azure-storage-blob   # Azure Blob
pip install paramiko          # SSH 클라이언트
pip install fabric            # SSH 자동화 (원격 배포)
pip install docker            # Docker API
pip install kubernetes        # K8s API
pip install pulumi            # IaC (Infrastructure as Code)
```

---

## 14. Database

```bash
pip install sqlalchemy        # ORM + SQL 빌더
pip install alembic           # DB 마이그레이션
pip install sqlmodel          # SQLAlchemy + Pydantic (FastAPI)
pip install asyncpg           # PostgreSQL async
pip install aiomysql          # MySQL async
pip install pymongo           # MongoDB
pip install redis             # Redis
pip install aiosqlite         # SQLite async
pip install tortoise-orm      # async ORM
pip install peewee            # 경량 ORM
```

---

## 15. Geospatial (지리정보)

```bash
pip install folium            # Leaflet 지도 (Python → HTML)
pip install geopandas         # 지리 데이터프레임
pip install shapely           # 도형 연산
pip install geopy             # 지오코딩 (주소→좌표)
```

---

## 카테고리별 추천 조합

### 이미지 보정 워크플로우
```text
pillow + opencv-python + rembg + realesrgan + easyocr
```

### 영상 보정 워크플로우
```text
moviepy + ffmpeg-python + opencv-python + faster-whisper + ultralytics
```

### AI 데모 앱
```text
streamlit + anthropic + chromadb + sentence-transformers + plotly
```

### 데이터 분석
```text
pandas + openpyxl + matplotlib + seaborn + rich
```

### 웹 API 서버
```text
fastapi + uvicorn + sqlmodel + pydantic-settings + python-dotenv
```

### 문서 자동화
```text
python-docx + python-pptx + PyMuPDF + camelot-py + weasyprint
```

### 테스트 스위트
```text
pytest + pytest-cov + pytest-mock + hypothesis + faker + freezegun
```
