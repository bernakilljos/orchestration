# Spreadsheet & Data Visualization COMMON Toolkit

> **Scope**: Spreadsheet/Data-viz plugin (`design_excel`) 공통 도구 카탈로그  
> **용도**: 엑셀/구글시트, 차트, 대시보드, 리포트 생성 도구 일괄 참조  
> **업데이트**: 2026-05-20  
> **관리**: plugins/exec_orch/references/ (동기화 불필요, 참조 전용)

---

## 1. 스프레드시트 작성 & 편집 라이브러리 (Python)

| 라이브러리 | 용도 | 설명 | 설치 |
|---|---|---|---|
| **openpyxl** | xlsx 읽기/쓰기 | 엑셀 2007+ 형식 (가장 많이 사용) | `pip install openpyxl` |
| **xlsxwriter** | xlsx 생성 (쓰기만) | 고속 생성, 스타일·차트 지원 | `pip install xlsxwriter` |
| **xlrd** | xls 읽기 (레거시) | 엑셀 2003 이전 형식 | `pip install xlrd` |
| **xlwt** | xls 쓰기 (레거시) | 엑셀 2003 형식 생성 | `pip install xlwt` |
| **pandas ExcelWriter** | xlsx 읽기/쓰기 | pandas DataFrame → Excel | `pip install pandas` |
| **xlwings** | Excel VBA 자동화 (Windows/Mac) | Python ↔ Excel 양방향 | `pip install xlwings` |
| **pyexcel** | 다중 포맷 (xlsx, csv, json) | 일반화된 인터페이스 | `pip install pyexcel pyexcel-xlsx` |
| **unidecode + openpyxl** | 한글 처리 | 깨진 한글 자동 변환 | `pip install unidecode openpyxl` |
| **Pillow + openpyxl** | 이미지 임베드 | 엑셀에 PNG/JPG 삽입 | `pip install Pillow openpyxl` |
| **python-docx** | docx 생성 | Word 문서 (엑셀 아님, 참고) | `pip install python-docx` |

---

## 2. Google Sheets API & 클라우드 스프레드시트

| 도구/라이브러리 | 설명 | 설치 |
|---|---|---|
| **gspread** | Google Sheets Python API (간편) | `pip install gspread` |
| **google-api-python-client** | Google API 공식 클라이언트 | `pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client` |
| **df2gspread** | pandas DataFrame → Google Sheets | `pip install df2gspread` |
| **Sheety** | 웹훅 기반 Sheets API | [sheety.co](https://sheety.co) |
| **SheetDB** | Google Sheets JSON API | [sheetdb.io](https://sheetdb.io) |
| **Integromat (Make)** | 노코드 자동화 (Sheets 포함) | [integromat.com](https://www.integromat.com) |
| **Zapier** | Sheets 자동화 연동 | [zapier.com](https://zapier.com) |

---

## 3. 차트 & 그래프 생성 라이브러리

| 라이브러리/도구 | 유형 | 설명 | 설치 |
|---|---|---|---|
| **matplotlib** | Python 라이브러리 | 기본 차트 (선, 막대, 산점도, 히스토그램) | `pip install matplotlib` |
| **plotly** | Python/JavaScript | 인터랙티브 차트 (특히 웹) | `pip install plotly` |
| **plotly Express** | Python (high-level) | plotly 간편 API | `pip install plotly` |
| **bokeh** | Python | 웹 기반 인터랙티브 차트 | `pip install bokeh` |
| **altair** | Python | Vega-Lite 기반 선언형 차트 | `pip install altair` |
| **seaborn** | Python | matplotlib 기반 통계 차트 | `pip install seaborn` |
| **ggplot2** | R | ggplot 기반 R 차트 (Python은 plotnine) | `install.packages("ggplot2")` |
| **plotnine** | Python | R ggplot2 포트 | `pip install plotnine` |
| **folium** | Python | Leaflet 지도 시각화 | `pip install folium` |
| **geopandas** | Python | 지리 데이터 시각화 | `pip install geopandas` |
| **pydeck** | Python | Deck.gl 3D 맵 | `pip install pydeck` |
| **graphviz** | C/Python | 네트워크/트리 그래프 | `pip install graphviz` 및 Graphviz 설치 |
| **plotly.graph_objects** | Python | 저수준 plotly API | `pip install plotly` |
| **echarts** | JavaScript | Baidu 기반 인터랙티브 차트 | `npm install echarts` |
| **Chart.js** | JavaScript | 경량 웹 차트 | `npm install chart.js` |
| **D3.js** | JavaScript | 강력한 데이터 시각화 라이브러리 | `npm install d3` |
| **Recharts** | JavaScript/React | React 차트 컴포넌트 | `npm install recharts` |
| **Nivo** | JavaScript/React | React 기반 고급 차트 | `npm install @nivo/core @nivo/bar` 등 |
| **Apache ECharts** | JavaScript | 대용량 데이터 차트 (특히 중국) | `npm install echarts` |
| **vis.js** | JavaScript | 네트워크 + 타임라인 | `npm install vis` |
| **Mermaid** | JavaScript | 다이어그램 (Markdown 호환) | `npm install mermaid` |

---

## 4. 대시보드 & BI 도구

| 도구 | 유형 | 설명 | 가격/설치 |
|---|---|---|---|
| **Streamlit** | Python 프레임워크 | 파이썬 스크립트 → 웹 앱 (데이터 앱) | `pip install streamlit` (무료) |
| **Dash** (Plotly) | Python 프레임워크 | Flask 기반 인터랙티브 대시보드 | `pip install dash` (무료) |
| **Panel** (HoloViz) | Python 프레임워크 | Jupyter 통합 앱 | `pip install panel` (무료) |
| **Gradio** | Python 라이브러리 | ML 모델 UI 생성 | `pip install gradio` (무료) |
| **Jupyter Notebook** | IDE | 데이터 분석 + 시각화 환경 | `pip install jupyter` (무료) |
| **Retool** | 노코드 플랫폼 | 드래그앤드롭 대시보드 빌더 | [retool.com](https://retool.com) ($10~/month) |
| **Metabase** | BI 플랫폼 (오픈소스) | SQL → 대시보드 자동 | `docker run metabase/metabase` (무료) |
| **Apache Superset** | BI 플랫폼 (오픈소스) | 대규모 데이터 시각화 | [superset.apache.org](https://superset.apache.org) (무료) |
| **PowerBI** (Microsoft) | BI 플랫폼 | Excel 통합, 엔터프라이즈 | $10~$20/user/month |
| **Tableau** | BI 플랫폼 | 고급 데이터 시각화 | $70~$2,190/month |
| **Looker** (Google) | BI 플랫폼 | 구글 클라우드 통합 | $5,000+/month |
| **QlikView** | BI 플랫폼 | 연결형 분석 | 라이센스 기반 |
| **Sisense** | BI 플랫폼 | 임베딩형 분석 | 라이센스 기반 |
| **Kibana** (Elastic) | 시각화 도구 | Elasticsearch 기반 | `docker run docker.elastic.co/kibana` (무료) |
| **Grafana** | 모니터링 대시보드 | 시계열 데이터 시각화 | [grafana.com](https://grafana.com) (무료/Pro) |

---

## 5. 리포트 & 문서 생성

| 도구 | 설명 | 설치 |
|---|---|---|
| **Jinja2 + openpyxl** | 템플릿 렌더링 → Excel 생성 | `pip install jinja2 openpyxl` |
| **python-pptx** | PowerPoint 생성 | `pip install python-pptx` |
| **reportlab** | PDF 생성 | `pip install reportlab` |
| **weasyprint** | HTML → PDF 변환 | `pip install weasyprint` |
| **pandoc** | 문서 포맷 변환 (md→docx→pdf) | `apt install pandoc` |
| **pandas-profiling** | 데이터 프로필 리포트 | `pip install pandas-profiling` |
| **sweetviz** | EDA 자동 리포트 (pandas) | `pip install sweetviz` |
| **ydata-profiling** | 고급 EDA 리포트 (pandas-profiling 진화) | `pip install ydata-profiling` |
| **dataprep** | 데이터 정제 + 리포트 | `pip install dataprep` |
| **Great Expectations** | 데이터 검증 리포트 | `pip install great-expectations` |
| **Sphinx** | 문서 생성 (기술 문서) | `pip install sphinx` |
| **MkDocs** | Markdown → 사이트 생성 | `pip install mkdocs` |

---

## 6. 피벗 테이블 & 데이터 변환

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **pandas pivot_table()** | 피벗 테이블 생성 | `pip install pandas` |
| **pandas groupby()** | 그룹화 및 집계 | `pip install pandas` |
| **pandas melt()** | Unpivot (행으로 변환) | `pip install pandas` |
| **polars** | 고속 데이터프레임 (pandas 대체) | `pip install polars` |
| **DuckDB** | SQL 쿼리 → DataFrame | `pip install duckdb` |
| **dbt** (data build tool) | SQL 변환 + 테스트 | `pip install dbt-core dbt-postgres` |
| **SQL Alchemy** | Python SQL 추상화 | `pip install sqlalchemy` |
| **Pandas Merge/Join** | 테이블 조인 | `pip install pandas` |

---

## 7. 인포그래픽 & 이미지 생성

| 도구 | 설명 | 가격/설치 |
|---|---|---|
| **Canva API** | 디자인 자동화 + 템플릿 | [canva.com/api](https://www.canva.com/api) (요청 기반) |
| **Piktochart** | 노코드 인포그래픽 | [piktochart.com](https://piktochart.com) ($99+/year) |
| **Infogram** | 인터랙티브 인포그래픽 | [infogram.com](https://infogram.com) (Free/$240+/year) |
| **Venngage** | 비주얼 콘텐츠 (인포그래픽, 차트) | [venngage.com](https://venngage.com) (Free/$10+/month) |
| **Adobe Express** | 빠른 그래픽 생성 (Canva 경쟁) | [express.adobe.com](https://www.adobe.com/express) (Free/Premium) |
| **Figma** | 디자인 플랫폼 (API 지원) | [figma.com](https://figma.com) (Free/$12+/month) |
| **Graphviz** | 시스템 다이어그램 + 오토레이아웃 | `apt install graphviz` (무료) |
| **Mermaid Diagram** | 마크다운 다이어그램 | `npm install mermaid` (무료) |
| **Python PIL/Pillow** | 이미지 조작 | `pip install Pillow` (무료) |

---

## 8. 테이블 UI & 웹 표시

| 라이브러리/도구 | 프레임워크 | 설명 | 설치 |
|---|---|---|---|
| **AG Grid** | JavaScript/React/Vue | 기업 수준 데이터 테이블 | `npm install ag-grid-community` (Free/$1,195+/year) |
| **TanStack Table** (React Table) | React | 헤드리스 테이블 라이브러리 | `npm install @tanstack/react-table` (무료) |
| **Handsontable** | JavaScript | 스프레드시트 UI (Excel 스타일) | `npm install handsontable` (Free/$990+/year) |
| **DataTables.js** | JavaScript | 서버사이드 테이블 | `npm install datatables.net` (무료) |
| **Material-Table** | React | Material Design 테이블 | `npm install @material-table/core` (무료) |
| **React Data Grid** | React | 경량 데이터 그리드 | `npm install @react-data-grid/all` (무료) |
| **Tabulator** | JavaScript | 고급 테이블 라이브러리 | `npm install tabulator-tables` (Free/$40~$190) |
| **PivotTable.js** | JavaScript | 피벗 테이블 웹 UI | `npm install pivottable` (무료) |
| **Semantic UI Table** | CSS | 테이블 스타일 (프레임워크) | `npm install semantic-ui` (무료) |

---

## 9. 데이터 라벨링 & 준비

| 도구 | 설명 | 가격/설치 |
|---|---|---|
| **Label Studio** | ML 라벨링 플랫폼 (오픈소스) | `pip install label-studio` (무료) |
| **Prodigy** (Explosion AI) | 능동 학습 라벨링 | [prodigy.ai](https://prodi.gy) ($500+) |
| **Snorkel** | 약한 감시 (weak supervision) | `pip install snorkel` (무료) |
| **OpenLabeling** | 이미지 라벨링 (오픈소스) | GitHub [Cartucho/OpenLabeling](https://github.com/Cartucho/OpenLabeling) |
| **CVAT** | 컴퓨터 비전 라벨링 | [cvat.ai](https://cvat.ai) (무료 / 클라우드 $) |
| **Roboflow** | 데이터셋 관리 + 변환 | [roboflow.com](https://roboflow.com) (Free/$50+/month) |
| **Scale AI** | AI 라벨링 서비스 (대행) | [scale.com](https://scale.com) (종량제) |

---

## 10. 테스트 & 검증

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **Great Expectations** | 데이터 검증 (데이터 품질) | `pip install great-expectations` |
| **pytest** | Python 유닛 테스트 | `pip install pytest` |
| **pandas.testing** | DataFrame 비교 | `pip install pandas` |
| **hypothesis** | 속성 기반 테스트 | `pip install hypothesis` |
| **Selenium** | 웹 자동화 테스트 | `pip install selenium` |
| **Playwright** | 브라우저 자동화 | `pip install playwright` |
| **jasmine** | JavaScript 테스트 | `npm install jasmine` |
| **jest** | JavaScript 테스트 (React) | `npm install jest` |

---

## 11. 데이터 저장소 & DB 연동

| 도구/라이브러리 | 설명 | 설치 |
|---|---|---|
| **SQLite** | 경량 파일 기반 DB | `apt install sqlite3` 또는 `pip install sqlite3` |
| **PostgreSQL** | 오픈소스 관계형 DB | `apt install postgresql` |
| **MySQL** | MySQL 관계형 DB | `apt install mysql-server` |
| **MongoDB** | NoSQL 문서 DB | `docker run mongo` |
| **Redis** | 인메모리 캐시 DB | `apt install redis-server` |
| **Firebase/Firestore** | Google 클라우드 DB | [firebase.google.com](https://firebase.google.com) |
| **AWS DynamoDB** | Amazon NoSQL DB | [aws.amazon.com/dynamodb](https://aws.amazon.com/dynamodb/) |
| **Azure SQL** | Microsoft SQL DB | [azure.microsoft.com](https://azure.microsoft.com) |
| **BigQuery** | Google 대규모 데이터 웨어하우스 | [cloud.google.com/bigquery](https://cloud.google.com/bigquery) |
| **Snowflake** | 클라우드 데이터 웨어하우스 | [snowflake.com](https://www.snowflake.com) |
| **Redshift** | AWS 데이터 웨어하우스 | [aws.amazon.com/redshift](https://aws.amazon.com/redshift/) |

---

## 12. 통계 & 머신러닝

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **scipy.stats** | 통계 분석 | `pip install scipy` |
| **statsmodels** | 통계 모델 + 회귀 | `pip install statsmodels` |
| **scikit-learn** | 머신러닝 (분류, 클러스터링) | `pip install scikit-learn` |
| **TensorFlow** | 딥러닝 (신경망) | `pip install tensorflow` |
| **PyTorch** | 딥러닝 (동적 그래프) | `pip install torch` |
| **XGBoost** | 부스팅 회귀 | `pip install xgboost` |
| **LightGBM** | 경량 부스팅 | `pip install lightgbm` |
| **CatBoost** | 범주형 데이터 부스팅 | `pip install catboost` |
| **SHAP** | 모델 해석 (피처 중요도) | `pip install shap` |
| **Lime** | 로컬 모델 해석 | `pip install lime` |

---

## 13. 시계열 데이터 & 예측

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **statsmodels.tsa** | ARIMA, SARIMA, VAR | `pip install statsmodels` |
| **Prophet** (Facebook) | 시계열 예측 (휴일 지원) | `pip install pystan prophet` |
| **LSTM** (TensorFlow) | 시계열 신경망 | `pip install tensorflow` |
| **Temporal Fusion Transformer** | 최신 시계열 모델 | `pip install pytorch-lightning` |
| **PyFlux** | 시계열 모델링 | `pip install pyflux` |

---

## 14. 한국어 지원 도구

| 도구 | 설명 | 설치 |
|---|---|---|
| **openpyxl + unidecode** | 한글 인코딩 처리 | `pip install unidecode openpyxl` |
| **KoNLPy** | 한국어 자연언어처리 | `pip install konlpy` |
| **Pandas + Korean locale** | 한글 정렬/포맷 | Locale 설정 필요 |
| **Google Sheets (한글 지원)** | 기본 한글 지원 | [sheets.google.com](https://sheets.google.com) |
| **Excel (한글 지원)** | 기본 한글 지원 | Microsoft Office |
| **Metabase (한글)** | 한글 UI 지원 | [metabase.com](https://www.metabase.com) |

---

## 15. 실시간 협업 도구

| 도구 | 설명 | 가격 |
|---|---|---|
| **Google Sheets** | 실시간 협업 스프레드시트 | Free / $10~$30/month |
| **Microsoft Excel Online** | 클라우드 엑셀 | 포함 (Microsoft 365) |
| **Airtable** | 노코드 데이터베이스 + 협업 | Free / $10~$50/month |
| **Notion** | 페이지 + 테이블 협업 | Free / $10/month |
| **Coda** | 문서 + 테이블 (All-in-one) | Free / $10~$30/month |
| **Frame.io** | 영상/이미지 협업 검토 | Free / $9~$29/month |

---

## 16. 성능 최적화 & 캐싱

| 라이브러리 | 설명 | 설치 |
|---|---|---|
| **Pandas-Caching** | DataFrame 캐싱 | 커스텀 구현 필요 |
| **Redis-Py** | Redis 캐시 | `pip install redis` |
| **SQLAlchemy Caching** | SQL 쿼리 캐싱 | `pip install sqlalchemy` |
| **Functools lru_cache** | 함수 결과 캐싱 (Python 기본) | Built-in |
| **Joblib Memory** | 함수 캐싱 (대용량) | `pip install joblib` |

---

## 17. 배포 & 호스팅

| 서비스 | 설명 | 가격 |
|---|---|---|
| **Streamlit Cloud** | Streamlit 앱 무료 호스팅 | Free (공개) / Pro |
| **Heroku** | 앱 호스팅 | Free/$7~/month |
| **AWS EC2** | 인스턴스 기반 호스팅 | 종량제 |
| **Google Cloud** | 구글 클라우드 앱 호스팅 | 종량제 |
| **Azure App Service** | Microsoft 앱 호스팅 | $10~/month |
| **Docker** | 컨테이너 배포 | `apt install docker.io` (무료) |
| **Vercel** | 프론트엔드 배포 (React, Next.js) | Free / $20/month |
| **Netlify** | 정적 사이트 + 함수 배포 | Free / $19+/month |

---

## 참조

- **DataFrame 비교**: [Pandas vs Polars vs DuckDB](docs/2026-05-20/df-comparison.md)
- **차트 선택 가이드**: [언제 어떤 차트를 쓸까](docs/2026-05-20/chart-selection.md)
- **대시보드 벤치마크**: [Streamlit vs Dash vs Panel](docs/2026-05-20/dashboard-comparison.md)
- **엑셀 VBA → Python**: [엑셀 자동화 마이그레이션](docs/2026-05-20/excel-automation.md)
- **Google Sheets API 튜토리얼**: [gspread 시작하기](docs/2026-05-20/gspread-tutorial.md)

---

**최종 업데이트**: 2026-05-20  
**총 도구 개수**: 190+  
**카테고리**: 17개 (라이브러리, 도구, 서비스, 프레임워크)  
**유지보수**: 월별 신규 도구 추가
