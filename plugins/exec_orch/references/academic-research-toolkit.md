# Academic Research & Writing Toolkit Reference

> **목적**: 논문 검색·작성·분석·관리·출판 전체 생태계의 공통 도구 카탈로그 (domain-agnostic)
> **대상**: 모든 학술 연구 플러그인·스킬에서 참고
> **최종 갱신**: 2026-05-20

---

## 📚 카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|----|---------|--------|---------|
| 1 | 🔍 논문 검색 | 8 | 논문 데이터베이스, 메타데이터, 인덱싱 |
| 2 | 📚 참고문헌 관리 | 9 | 인용 포맷, BibTeX, 메타데이터 관리 |
| 3 | 📝 논문 작성 | 10 | LaTeX, Typst, Markdown 기반 문서 작성 |
| 4 | 🔐 표절 검사 | 6 | 원문성 검사, 표절율 측정, 신뢰성 검증 |
| 5 | 📊 통계 분석 | 10 | 고전 통계, 회귀, 베이지안 분석 |
| 6 | 📋 설문/데이터 수집 | 7 | 온라인 설문, 데이터 관리, RESTful API |
| 7 | 🗂️ 질적 연구 | 6 | 코딩, 메모 관리, 테마 분석, 시각화 |
| 8 | 📈 데이터 시각화 (학술) | 8 | ggplot2, 학술용 정적 그래프, 과학 차트 |
| 9 | 🔄 재현성 & 재생산 | 8 | 컨테이너, 워크플로우, 버전 관리 |
| 10 | 🌐 오픈 사이언스 & 저장소 | 7 | 데이터 공개, 저작권 관리, 미리보기 |
| 11 | 🤖 AI 연구 도구 | 9 | 의미 검색, 논문 분류, 지도 작성 |
| 12 | 🎯 프레젠테이션 | 6 | Beamer, 슬라이드 생성, 학술 포스터 |
| 13 | ✏️ 교정 & 번역 | 7 | 문법 검사, 스타일 가이드, 다국어 번역 |
| 14 | 🇰🇷 한국 학술 플랫폼 | 9 | KCI 저널, 국내 데이터베이스, 문헌 정보 |

**총 도구 수: 121개** (각 카테고리별 최소 6개 이상)

---

## 1️⃣ 논문 검색 (Literature Search)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 1.1 | Google Scholar | 학술 논문 검색 엔진 — 무료, 광범위한 메타데이터 | https://scholar.google.com |
| 1.2 | Semantic Scholar | AI 기반 논문 검색 및 인용 분석 — Allen AI 제공 | https://www.semanticscholar.org |
| 1.3 | PubMed | 의학·생명과학 논문 검색 (NIH 제공) | https://pubmed.ncbi.nlm.nih.gov |
| 1.4 | arXiv | 프리프린트 저장소 (물리·수학·컴퓨터과학) | https://arxiv.org |
| 1.5 | DBLP | 컴퓨터과학 논문 데이터베이스 | https://dblp.org |
| 1.6 | CrossRef | 학술 출판 메타데이터 및 DOI 등록 기관 | https://www.crossref.org |
| 1.7 | OpenAlex | 오픈 학술 메타데이터 (2M+ 저널) | https://openalex.org |
| 1.8 | BASE | Bielefeld Academic Search Engine (150M+ 문서) | https://www.base-search.net |

---

## 2️⃣ 참고문헌 관리 (Citation Management)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 2.1 | Zotero | 오픈소스 참고문헌 관리 — 브라우저 플러그인 지원 | https://www.zotero.org / `apt install zotero` |
| 2.2 | Mendeley | 클라우드 기반 참고문헌 관리 및 협업 | https://www.mendeley.com |
| 2.3 | EndNote | 상용 참고문헌 관리 (Thomson Reuters) | https://endnote.com |
| 2.4 | Paperpile | 웹 기반 참고문헌 관리 — Google Drive 통합 | https://paperpile.com |
| 2.5 | JabRef | 오픈소스 BibTeX 관리 도구 | https://www.jabref.org |
| 2.6 | BibTeX | LaTeX 인용 포맷 표준 | 기본 포함 (TeXLive/MiKTeX) |
| 2.7 | Citation.js | JavaScript 인용 라이브러리 — 50+ 포맷 지원 | `npm install citation-js` |
| 2.8 | Citavi | 학술 정보 관리 및 인용 생성 | https://www.citavi.com |
| 2.9 | ReadCube | 논문 관리 및 추천 플랫폼 | https://www.readcube.com |

---

## 3️⃣ 논문 작성 (Manuscript Preparation)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 3.1 | Overleaf | 온라인 LaTeX 에디터 — 실시간 협업 | https://www.overleaf.com |
| 3.2 | TeXLive | LaTeX 통합 배포판 (Windows/Linux/macOS) | https://tug.org/texlive / `apt install texlive-full` |
| 3.3 | MiKTeX | Windows 중심 LaTeX 배포 | https://miktex.org |
| 3.4 | Typst | 현대 활자 시스템 — LaTeX 대안 | https://typst.app |
| 3.5 | Pandoc | 문서 변환 도구 (Markdown ↔ LaTeX ↔ DOCX) | https://pandoc.org / `apt install pandoc` |
| 3.6 | Quarto | 과학 논문 작성 (R/Python 통합) | https://quarto.org / `pip install quarto-cli` |
| 3.7 | R Markdown | R 코드 + 문서 통합 작성 | `install.packages("rmarkdown")` |
| 3.8 | Jupyter Book | Jupyter 노트북 책 출판 | `pip install jupyter-book` |
| 3.9 | BookDown | R 기반 책 작성 프레임워크 | `install.packages("bookdown")` |
| 3.10 | VSCode + LaTeX Workshop | VS Code 에서 LaTeX 실시간 편집 | `code --install-extension James-Yu.latex-workshop` |

---

## 4️⃣ 표절 검사 (Plagiarism Detection)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 4.1 | Turnitin | 대학 표준 표절 검사 도구 | https://www.turnitin.com |
| 4.2 | Grammarly | 문법·표절·스타일 검사 (AI 기반) | https://www.grammarly.com |
| 4.3 | iThenticate | 학술 출판사 대상 고급 표절 검사 | https://www.ithenticate.com |
| 4.4 | Copyscape | 웹 기반 표절 검사 도구 | https://www.copyscape.com |
| 4.5 | Quetext | AI 기반 표절율 및 유사도 검사 | https://www.quetext.com |
| 4.6 | PlagScan | 유럽 표준 표절 검사 (12M+ 데이터베이스) | https://www.plagscan.com |

---

## 5️⃣ 통계 분석 (Statistical Analysis)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 5.1 | R | 통계 분석 기본 언어 | https://www.r-project.org / `apt install r-base` |
| 5.2 | SPSS | 상용 통계 소프트웨어 (IBM) | https://www.ibm.com/spss |
| 5.3 | Stata | 경제학·사회과학 통계 소프트웨어 | https://www.stata.com |
| 5.4 | SAS | 빅데이터 통계 분석 | https://www.sas.com |
| 5.5 | JASP | 점 & 클릭 통계 분석 (베이지안 강화) | https://jasp-stats.org |
| 5.6 | jamovi | 사용자 친화적 통계 소프트웨어 | https://www.jamovi.org |
| 5.7 | statsmodels | Python 통계 모델링 라이브러리 | `pip install statsmodels` |
| 5.8 | pingouin | Python 생물통계학 라이브러리 | `pip install pingouin` |
| 5.9 | scipy.stats | Python SciPy 통계 모듈 | `pip install scipy` |
| 5.10 | ggplot2 | R 시각 + 통계 패키지 | `install.packages("ggplot2")` |

---

## 6️⃣ 설문 & 데이터 수집 (Survey & Data Collection)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 6.1 | Qualtrics | 엔터프라이즈 온라인 설문 플랫폼 | https://www.qualtrics.com |
| 6.2 | Google Forms | 무료 온라인 설문 도구 | https://forms.google.com |
| 6.3 | SurveyMonkey | 온라인 설문 및 분석 (500+템플릿) | https://www.surveymonkey.com |
| 6.4 | REDCap | 임상 데이터 수집 (NIH 후원) | https://www.project-redcap.org |
| 6.5 | LimeSurvey | 오픈소스 온라인 설문 도구 | https://www.limesurvey.org |
| 6.6 | KoBoToolbox | 인도주의 데이터 수집 (오픈소스) | https://www.kobotoolbox.org |
| 6.7 | Jotform | 드래그앤드롭 폼 빌더 | https://www.jotform.com |

---

## 7️⃣ 질적 연구 (Qualitative Research & NVivo)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 7.1 | NVivo | 질적 데이터 분석 (QSR International) | https://www.qsrinternational.com/nvivo |
| 7.2 | ATLAS.ti | 시맨틱 분석 및 질적 데이터 코딩 | https://atlasti.com |
| 7.3 | MAXQDA | 질적·혼합 연구 분석 소프트웨어 | https://www.maxqda.com |
| 7.4 | Dedoose | 클라우드 기반 혼합 방법 분석 | https://www.dedoose.com |
| 7.5 | Taguette | 오픈소스 텍스트 태깅 및 주석 | https://www.taguette.org |
| 7.6 | QDA Miner | 질적 데이터 마이닝 및 분석 | https://provalisresearch.com/products/qdaminer |

---

## 8️⃣ 데이터 시각화 - 학술 (Academic Visualization)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 8.1 | ggplot2 | R 문법 기반 과학 그래프 | `install.packages("ggplot2")` |
| 8.2 | matplotlib | Python 정적 과학 차트 | `pip install matplotlib` |
| 8.3 | seaborn | Python 통계 시각화 (matplotlib 기반) | `pip install seaborn` |
| 8.4 | plotnine | R ggplot2의 Python 포트 | `pip install plotnine` |
| 8.5 | tikz/pgfplots | LaTeX 기반 출판 품질 그래프 | 기본 포함 (TeXLive) |
| 8.6 | Graphviz | 네트워크·다이어그램 시각화 | https://graphviz.org / `apt install graphviz` |
| 8.7 | Inkscape | 벡터 그래픽 에디터 (학술 포스터용) | https://inkscape.org |
| 8.8 | R ggvis | 인터랙티브 ggplot2 시각화 | `install.packages("ggvis")` |

---

## 9️⃣ 재현성 & 재생산성 (Reproducibility & Containers)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 9.1 | Jupyter | 대화형 노트북 (Python/R/Julia) | `pip install jupyter` |
| 9.2 | Binder | Jupyter 노트북 클라우드 실행 환경 | https://mybinder.org |
| 9.3 | Docker | 컨테이너 기반 재현 가능한 환경 | https://www.docker.com / `apt install docker.io` |
| 9.4 | Singularity | HPC 친화적 컨테이너 | https://sylabs.io |
| 9.5 | Snakemake | Python 기반 워크플로우 관리 | `pip install snakemake` |
| 9.6 | Nextflow | 분산 과학 워크플로우 | https://www.nextflow.io |
| 9.7 | CWL (Common Workflow Language) | 표준 워크플로우 정의 | https://www.commonwl.org |
| 9.8 | DVC (Data Version Control) | 데이터+모델 버전 관리 | `pip install dvc` |

---

## 🔟 오픈 사이언스 & 저장소 (Open Science & Repositories)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 10.1 | OSF (Open Science Framework) | 연구 프로젝트 공개·관리 | https://osf.io |
| 10.2 | Zenodo | CERN 제공 오픈 데이터 저장소 | https://zenodo.org |
| 10.3 | Figshare | 학술 자료 공유 (논문, 데이터, 포스터) | https://figshare.com |
| 10.4 | Dryad | 데이터 저작권 관리 (출판 연계) | https://datadryad.org |
| 10.5 | GitHub | 코드 + 데이터 버전 관리 | https://github.com |
| 10.6 | protocols.io | 프로토콜 공개·버전 관리 | https://www.protocols.io |
| 10.7 | Open Knowledge Foundation | 오픈 데이터 정책·커뮤니티 | https://okfn.org |

---

## 1️⃣1️⃣ AI 연구 도구 (AI-Powered Research Tools)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 11.1 | Elicit | AI 기반 논문 검색 및 데이터 추출 | https://elicit.org |
| 11.2 | Consensus | AI가 논문 내용을 요약·검색 | https://consensus.app |
| 11.3 | ResearchRabbit | 관심 주제 기반 논문 추천 | https://researchrabbitapp.com |
| 11.4 | Connected Papers | 논문 연관성 시각화 그래프 | https://www.connectedpapers.com |
| 11.5 | Inciteful | 인용 네트워크 분석 및 경로 찾기 | https://inciteful.xyz |
| 11.6 | Scite | 인용 맥락 분석 (논문 평가) | https://scite.ai |
| 11.7 | Litmaps | 시간별 논문 트렌드 시각화 | https://www.litmaps.co |
| 11.8 | SciSpace | AI 기반 논문 분석 및 요약 | https://scispace.com |
| 11.9 | ChatPDF | PDF 논문 AI 질문 응답 | https://www.chatpdf.com |

---

## 1️⃣2️⃣ 프레젠테이션 (Academic Presentations)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 12.1 | Beamer | LaTeX 기반 학술 슬라이드 | 기본 포함 (TeXLive) |
| 12.2 | Marp | Markdown to PowerPoint 슬라이드 | https://marp.app / `npm install -g @marp-team/marp-cli` |
| 12.3 | reveal.js | HTML 기반 프레젠테이션 프레임워크 | https://revealjs.com |
| 12.4 | SlideDeck | 구글 슬라이드 기반 과학 프레젠테이션 | https://slidedeck.io |
| 12.5 | Figma + Presentations | Figma 내 프레젠테이션 기능 (협업) | https://www.figma.com |
| 12.6 | Canva Academic | 학술 포스터·슬라이드 템플릿 | https://www.canva.com |

---

## 1️⃣3️⃣ 교정 & 번역 (Proofreading & Translation)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 13.1 | Grammarly | 문법·스타일·표절 일괄 검사 (AI) | https://www.grammarly.com |
| 13.2 | DeepL | AI 기반 고품질 번역 (50+ 언어) | https://www.deepl.com |
| 13.3 | LanguageTool | 오픈소스 문법 검사 (25+ 언어) | https://languagetool.org / `pip install language-tool-python` |
| 13.4 | ProWritingAid | 상세 쓰기 분석 및 교정 | https://prowritingaid.com |
| 13.5 | Hemingway Editor | 명확성·간결성 검사 | https://www.hemingwayapp.com |
| 13.6 | Google Translate API | 프로그래머 친화적 번역 API | https://cloud.google.com/translate |
| 13.7 | Papago (네이버) | 한영 번역 (학술문 최적화) | https://papago.naver.com / `pip install naver-papago` |

---

## 1️⃣4️⃣ 한국 학술 플랫폼 (Korean Academic Platforms)

| # | 도구명 | 한글 설명 | URL / 설치 |
|----|--------|---------|---------|
| 14.1 | RISS (한국교육학술정보원) | 국내 최대 학술 검색 플랫폼 | https://www.riss.kr |
| 14.2 | KISS (한국학술정보) | 한국학술지인용색인 (KCI 저널) | https://kiss.kstudy.com |
| 14.3 | DBpia | 학술지·논문 통합 검색 | https://www.dbpia.co.kr |
| 14.4 | KCI (한국학술지인용색인) | 국내 학술지 등재·평가 | https://kci.go.kr |
| 14.5 | KERIS (교육학술정보원) | 고등교육 학술 정보 통합 검색 | https://www.keris.or.kr |
| 14.6 | 학술연구정보서비스 (NARS) | 국회도서관 학술 정보 | https://nars.nanet.go.kr |
| 14.7 | 국회도서관 논문 검색 | 국가 수탁 학술 자료 | https://www.nanet.go.kr |
| 14.8 | 국립중앙도서관 서지정보 | 국내 출판물·학위논문 | https://www.nl.go.kr |
| 14.9 | 학술진흥재단 과제 검색 | NRF 연구 과제 및 결과물 | https://www.nrf.re.kr |

---

## 📌 도구 선택 가이드

### 논문 검색 의사결정
- **일반 학술**: Google Scholar, Semantic Scholar
- **생의학**: PubMed
- **프리프린트**: arXiv, SSRN
- **컴퓨터과학**: DBLP
- **한국 학술**: RISS, KISS, KCI

### 참고문헌 관리 의사결정
- **협업**: Zotero (오픈) vs Paperpile (웹 기반)
- **LaTeX**: JabRef, BibTeX
- **클라우드**: Mendeley, Paperpile
- **한국 대학**: Zotero (무료) 권장

### 논문 작성 의사결정
- **LaTeX 협업**: Overleaf
- **Python/R 통합**: Quarto, Jupyter Book
- **빠른 변환**: Pandoc
- **현대식**: Typst

### 표절 검사 의사결정
- **대학 표준**: Turnitin
- **포괄적 검사**: Grammarly
- **출판사 대상**: iThenticate

### 통계 분석 의사결정
- **기본**: R + RStudio
- **사용자 친화**: JASP, jamovi
- **회귀 분석**: statsmodels (Python) or R
- **베이지안**: R (rstan, bayesplot)

### AI 논문 분석
- **검색 + 요약**: Elicit
- **신뢰도 평가**: Scite
- **트렌드**: Litmaps, Connected Papers
- **추천**: ResearchRabbit

---

## ✨ 통합 워크플로우 예시

### 1단계: 논문 검색 및 관리
```text
Google Scholar / Semantic Scholar 
  ↓
Zotero (참고문헌 관리)
  ↓
Connected Papers (인용 네트워크)
```

### 2단계: 논문 작성
```text
Overleaf (LaTeX) 또는 Quarto (R/Python)
  ↓
Grammarly (문법 검사)
  ↓
Turnitin (표절 검사)
```

### 3단계: 통계 분석
```text
R / Python (statsmodels)
  ↓
ggplot2 / matplotlib (시각화)
  ↓
Quarto (논문 삽입)
```

### 4단계: 재현성 확보
```text
Jupyter Notebook
  ↓
Docker (환경 관리)
  ↓
OSF / Zenodo (공개)
```

### 5단계: 발표
```text
Beamer (LaTeX) 또는 Marp (Markdown)
  ↓
Figma (협업 포스터)
```

---

## 🔗 참고 링크

- **학술 커뮤니티**: Reddit r/AcademicResearch, Slack 학술 채널
- **HOW-TO 튜토리얼**: Overleaf Docs, R for Data Science (Wickham), Quarto Guide
- **최신 동향**: Nature News, Science Daily, The Scholarly Kitchen
- **한국 가이드**: RISS 사용 설명서, 대학원생 논문 작성 가이드

---

## 📌 주의사항

1. **표절 검사**: 대학별 라이선스 정책 확인
2. **통계 도구**: 분야별 표준 (의학=SPSS, 심리=R, 경제=Stata) 확인
3. **LaTeX**: 학위논문 양식 템플릿 미리 확보
4. **데이터 공개**: IRB 승인 범위 내 공개
5. **한국 저널**: KCI 등재 기준·심사 기간 확인

---

**최종 갱신**: 2026-05-20  
**관리자**: orchestration_v1 Toolkit
