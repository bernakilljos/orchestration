# Data Science & Analytics Toolkit Reference

> **목적**: 데이터 과학·분석 전체 생태계의 공통 도구 카탈로그 (domain-agnostic)
> **대상**: 모든 데이터 사이언스 플러그인·스킬에서 참고
> **최종 갱신**: 2026-05-20

---

##  카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|----|---------|--------|---------|
| 1 | 📁 데이터 처리 | 8 | DataFrames, 병렬 처리, 메모리 최적화 |
| 2 | 🔢 수치 연산 | 8 | 선형대수, 최적화, 기호 계산 |
| 3 | 📈 시각화 | 12 | 정적·대시보드·인터랙티브 차트 |
| 4 | 🧠 ML 프레임워크 | 9 | 고전 머신러닝, Boosting, AutoML |
| 5 | 🔗 딥러닝 | 7 | 신경망, 프레임워크, 학습 유틸 |
| 6 | 💬 NLP | 13 | 텍스트 처리, 임베딩, LLM 통합 |
| 7 | 👁 CV (컴퓨터 비전) | 8 | 객체 감지, 분할, 변환 |
| 8 | ⏰ 시계열 분석 | 9 | 예측, 이상 탐지, 분해 |
| 9 | 🤖 AutoML | 8 | 자동 모델 선택, 하이퍼 튜닝 |
| 10 | 🚀 MLOps | 10 | 모델 추적, 배포, 모니터링 |
| 11 | 🏪 피처 스토어 | 4 | 피처 관리, 공유, 버전 관리 |
| 12 |  데이터 품질 | 6 | 검증, 테스트, 이상 탐지 |
| 13 | 📓 노트북 | 6 | 대화형 분석, 개발 환경 |
| 14 | 🔀 ETL/파이프라인 | 7 | 워크플로우 자동화, 스케줄링 |
| 15 | 🔍 벡터 DB/임베딩 | 10 | 유사도 검색, RAG, 임베딩 저장 |
| 16 | 🔤 LLM 도구 | 7 | 모델 실행, 최적화, 양자화 |
| 17 | 📝 실험 추적 | 5 | 메타데이터, 결과, 비교 |
| 18 | 🔎 설명 가능 AI | 8 | 해석, 피처 중요도, 정보성 |

**총 도구 수: 145개** (각 카테고리별 최소 4개 이상)

---

## 1⃣ 데이터 처리 (Data Processing & Wrangling)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 1.1 | pandas | Python의 기본 데이터 분석 라이브러리 — DataFrame 및 Series 조작 | `pip install pandas` |
| 1.2 | polars | 멀티스레드 병렬 처리 기반의 고성능 DataFrame 라이브러리 | `pip install polars` |
| 1.3 | dask | 분산 메모리 컴퓨팅으로 대용량 데이터 병렬 처리 | `pip install dask` |
| 1.4 | modin | pandas와 호환되는 병렬 데이터프레임 | `pip install modin` |
| 1.5 | vaex | 백터화된 메모리 매핑으로 극대용량 데이터 처리 | `pip install vaex` |
| 1.6 | pyarrow | 열 기반 데이터 형식 및 IPC 포맷 지원 | `pip install pyarrow` |
| 1.7 | datatable | R의 data.table 영감의 고속 처리 | `pip install datatable` |
| 1.8 | DuckDB | 프로세스 내 SQL 쿼리 엔진 | `pip install duckdb` |

---

## 2⃣ 수치 연산 (Numerical Computing)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 2.1 | NumPy | 멀티차원 배열 및 선형대수 기본 라이브러리 | `pip install numpy` |
| 2.2 | SciPy | 최적화, 통계, 적분, 신호 처리 확장 | `pip install scipy` |
| 2.3 | SymPy | 기호 수학 계산 및 정규 표현식 | `pip install sympy` |
| 2.4 | JAX | GPU/TPU 기반 변환 미분 수치 계산 | `pip install jax jaxlib` |
| 2.5 | numexpr | 복잡한 수치식 고속 평가 | `pip install numexpr` |
| 2.6 | statsmodels | 통계 모델링 및 가설 검정 | `pip install statsmodels` |
| 2.7 | scikit-spatial | 공간 데이터 기하학 계산 | `pip install scikit-spatial` |
| 2.8 | cvxpy | 볼록 최적화 문제 풀이 | `pip install cvxpy` |

---

## 3⃣ 시각화 (Visualization & Dashboard)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 3.1 | matplotlib | 기본 정적 및 동적 2D/3D 그래프 라이브러리 | `pip install matplotlib` |
| 3.2 | seaborn | 통계적 데이터 시각화 (matplotlib 기반) | `pip install seaborn` |
| 3.3 | plotly | 인터랙티브 웹 기반 그래프 | `pip install plotly` |
| 3.4 | bokeh | 대용량 데이터 인터랙티브 시각화 | `pip install bokeh` |
| 3.5 | altair | 선언적 시각화 문법 (Vega 기반) | `pip install altair` |
| 3.6 | dash | Plotly 기반 웹 대시보드 프레임워크 | `pip install dash` |
| 3.7 | streamlit | 빠른 데이터 앱/대시보드 구축 | `pip install streamlit` |
| 3.8 | gradio | ML 모델 데모 인터페이스 | `pip install gradio` |
| 3.9 | panel | Jupyter 및 웹 기반 대시보드 | `pip install panel` |
| 3.10 | plotnine | R의 ggplot2 Python 포트 | `pip install plotnine` |
| 3.11 | holoviews | 다차원 데이터 동적 시각화 | `pip install holoviews` |
| 3.12 | pydot | Graphviz 인터페이스로 그래프 그리기 | `pip install pydot` |

---

## 4⃣ ML 프레임워크 (Traditional & Boosting)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 4.1 | scikit-learn | 분류, 회귀, 클러스터링, 피처 엔지니어링 | `pip install scikit-learn` |
| 4.2 | XGBoost | 그래디언트 부스팅 의사결정나무 | `pip install xgboost` |
| 4.3 | LightGBM | 빛 그래디언트 부스팅 머신 | `pip install lightgbm` |
| 4.4 | CatBoost | 범주형 변수 최적화 부스팅 | `pip install catboost` |
| 4.5 | H2O AutoML | 분산 머신러닝 및 자동화 | `pip install h2o` |
| 4.6 | Vowpal Wabbit | 온라인 학습 및 스트리밍 데이터 | `pip install vowpalwabbit` |
| 4.7 | MLxtend | 머신러닝 확장 유틸리티 | `pip install mlxtend` |
| 4.8 | imbalanced-learn | 불균형 데이터 처리 리샘플링 | `pip install imbalanced-learn` |
| 4.9 | hmmlearn | 숨겨진 마르코프 모델 | `pip install hmmlearn` |

---

## 5⃣ 딥러닝 (Deep Learning Frameworks)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 5.1 | PyTorch | GPU 최적화 동적 신경망 프레임워크 | `pip install torch torchvision torchaudio` |
| 5.2 | TensorFlow | 엔드-투-엔드 머신러닝 플랫폼 | `pip install tensorflow` |
| 5.3 | Keras | 고수준 신경망 API (TensorFlow 내장) | `pip install keras` |
| 5.4 | FastAI | PyTorch 기반 실용적 딥러닝 라이브러리 | `pip install fastai` |
| 5.5 | PyTorch Lightning | PyTorch 학습 자동화 및 구조화 | `pip install pytorch-lightning` |
| 5.6 | Flux.jl | Julia 기반 기계학습 라이브러리 | `pip install juliabase` |
| 5.7 | MXNet | 분산 딥러닝 프레임워크 | `pip install mxnet` |

---

## 6⃣ NLP (자연어 처리)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 6.1 | spaCy | 프로덕션 NLP 파이프라인 | `pip install spacy` |
| 6.2 | Hugging Face Transformers | BERT, GPT 등 사전학습 모델 | `pip install transformers` |
| 6.3 | NLTK | 자연어 처리 입문 라이브러리 | `pip install nltk` |
| 6.4 | Gensim | 토픽 모델링, Word2Vec, Doc2Vec | `pip install gensim` |
| 6.5 | sentence-transformers | 문장 임베딩 모델 | `pip install sentence-transformers` |
| 6.6 | LangChain | LLM 응용 프로그램 프레임워크 | `pip install langchain` |
| 6.7 | LlamaIndex (GPT Index) | LLM 기반 데이터 인덱싱 및 검색 | `pip install llama-index` |
| 6.8 | TextBlob | 간단한 텍스트 처리 및 감정 분석 | `pip install textblob` |
| 6.9 | RAKE | 자동 키워드 추출 | `pip install rake-nltk` |
| 6.10 | polyglot | 다국어 NLP | `pip install polyglot` |
| 6.11 | fastText | 빠른 텍스트 분류 및 임베딩 | `pip install fasttext` |
| 6.12 | patterns | 웹 마이닝 및 NLP 도구 | `pip install patterns` |
| 6.13 | PyTorch-NLP | NLP 기초 유틸리티 | `pip install pytorch-nlp` |

---

## 7⃣ CV (컴퓨터 비전)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 7.1 | OpenCV | 컴퓨터 비전 알고리즘 기본 라이브러리 | `pip install opencv-python` |
| 7.2 | torchvision | PyTorch 비전 모델 및 데이터셋 | `pip install torchvision` |
| 7.3 | Ultralytics YOLO | 실시간 객체 감지 모델 | `pip install ultralytics` |
| 7.4 | Detectron2 | Facebook AI 객체 감지 프레임워크 | `pip install detectron2` |
| 7.5 | MMDetection | OpenMMLab 객체 감지 도구 | `pip install mmdet` |
| 7.6 | scikit-image | 이미지 처리 알고리즘 | `pip install scikit-image` |
| 7.7 | Pillow | 기본 이미지 조작 라이브러리 | `pip install pillow` |
| 7.8 | imgaug | 이미지 증강 라이브러리 | `pip install imgaug` |

---

## 8⃣ 시계열 분석 (Time Series)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 8.1 | Prophet | Facebook 시계열 예측 라이브러리 | `pip install prophet` |
| 8.2 | statsmodels | 시계열 분석 및 ARIMA 모델 | `pip install statsmodels` |
| 8.3 | tslearn | 시계열 머신러닝 | `pip install tslearn` |
| 8.4 | darts | 멀티변량 시계열 라이브러리 | `pip install darts` |
| 8.5 | sktime | 통일된 시계열 ML 프레임워크 | `pip install sktime` |
| 8.6 | NeuralProphet | 신경망 시계열 예측 | `pip install neural-prophet` |
| 8.7 | GLUONTS | 시계열 학습 도구 | `pip install gluonts` |
| 8.8 | PyFlux | 베이지안 시계열 모델링 | `pip install pyflux` |
| 8.9 | tbats | 시계열 분해 및 부스팅 | `pip install tbats` |

---

## 9⃣ AutoML (자동 머신러닝)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 9.1 | AutoGluon | AWS 자동 머신러닝 | `pip install autogluon` |
| 9.2 | FLAML | 빠른 경량 자동 머신러닝 | `pip install flaml` |
| 9.3 | auto-sklearn | 머신러닝 파이프라인 자동화 | `pip install auto-sklearn` |
| 9.4 | PyCaret | 로우코드 머신러닝 | `pip install pycaret` |
| 9.5 | Optuna | 하이퍼파라미터 최적화 프레임워크 | `pip install optuna` |
| 9.6 | Ray Tune | 분산 하이퍼파라미터 튜닝 | `pip install ray[tune]` |
| 9.7 | Hyperopt | 베이지안 하이퍼파라미터 탐색 | `pip install hyperopt` |
| 9.8 | scikit-optimize | 순차 모델 기반 최적화 | `pip install scikit-optimize` |

---

## 🔟 MLOps (모델 운영 & 배포)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 10.1 | MLflow | 모델 생명주기 관리 및 추적 | `pip install mlflow` |
| 10.2 | Weights & Biases | 실험 추적 및 모델 모니터링 | `pip install wandb` |
| 10.3 | DVC | 데이터 및 모델 버전 관리 | `pip install dvc` |
| 10.4 | BentoML | 머신러닝 서비스 배포 프레임워크 | `pip install bentoml` |
| 10.5 | Seldon | 머신러닝 모델 서빙 플랫폼 | `pip install seldon-core` |
| 10.6 | KServe | Kubernetes 기반 모델 서빙 | `pip install kserve` |
| 10.7 | FastAPI | 고성능 API 구축 프레임워크 | `pip install fastapi` |
| 10.8 | TFServing | TensorFlow 모델 서빙 시스템 | `pip install tensorflow-serving-api` |
| 10.9 | cortex | 머신러닝 모델 배포 플랫폼 | `pip install cortex` |
| 10.10 | Kubeflow | Kubernetes 기반 ML 워크플로우 | `pip install kubeflow` |

---

## 1⃣1⃣ 피처 스토어 (Feature Store)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 11.1 | Feast | 오픈소스 피처 저장소 플랫폼 | `pip install feast` |
| 11.2 | Tecton | 엔터프라이즈 피처 저장소 | `pip install tecton` |
| 11.3 | Hopsworks | 엔터프라이즈 ML 기능 플랫폼 | `pip install hopsworks` |
| 11.4 | Featuretools | 자동 피처 엔지니어링 | `pip install featuretools` |

---

## 1⃣2⃣ 데이터 품질 (Data Quality & Validation)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 12.1 | Great Expectations | 데이터 검증 및 문서화 | `pip install great-expectations` |
| 12.2 | Pandera | 통계 기반 데이터 검증 | `pip install pandera` |
| 12.3 | Evidently AI | 모델 및 데이터 모니터링 | `pip install evidently` |
| 12.4 | Deepchecks | 모델 신뢰성 검사 | `pip install deepchecks` |
| 12.5 | Dataclasses-json | 데이터 클래스 직렬화 검증 | `pip install dataclasses-json` |
| 12.6 | Schemathesis | 자동화된 API 테스트 | `pip install schemathesis` |

---

## 1⃣3⃣ 노트북 & IDE (Interactive Computing)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 13.1 | Jupyter | 클래식 대화형 노트북 | `pip install jupyter` |
| 13.2 | JupyterLab | 현대식 Jupyter 개발 환경 | `pip install jupyterlab` |
| 13.3 | Marimo | 반응형 Python 노트북 | `pip install marimo` |
| 13.4 | Hex | 협업 데이터 애플리케이션 플랫폼 | `pip install hexdata` |
| 13.5 | Observable | 반응형 JavaScript 노트북 (Python 통합) | N/A (웹 기반) |
| 13.6 | Databricks | Apache Spark 기반 분석 플랫폼 | `pip install databricks-sql-connector` |

---

## 1⃣4⃣ ETL/파이프라인 (Workflow Orchestration)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 14.1 | Apache Airflow | 분산 작업 스케줄링 플랫폼 | `pip install apache-airflow` |
| 14.2 | Prefect | 모던 워크플로우 오케스트레이션 | `pip install prefect` |
| 14.3 | Dagster | 데이터 오케스트레이션 프레임워크 | `pip install dagster` |
| 14.4 | Luigi | Spotify 기반 파이프라인 도구 | `pip install luigi` |
| 14.5 | Mage.ai | 현대식 데이터 파이프라인 엔진 | `pip install mage-ai` |
| 14.6 | Apache Beam | 배치 및 스트리밍 데이터 처리 | `pip install apache-beam` |
| 14.7 | Kedro | 재현 가능한 데이터 파이프라인 | `pip install kedro` |

---

## 1⃣5⃣ 벡터 DB & 임베딩 (Vector Database & Embeddings)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 15.1 | FAISS | Facebook 유사도 검색 라이브러리 | `pip install faiss-cpu` or `faiss-gpu` |
| 15.2 | Pinecone | 관리형 벡터 데이터베이스 | `pip install pinecone-client` |
| 15.3 | Weaviate | 오픈소스 벡터 검색 엔진 | `pip install weaviate-client` |
| 15.4 | Qdrant | 고성능 벡터 검색 데이터베이스 | `pip install qdrant-client` |
| 15.5 | Milvus | 오픈소스 벡터 데이터베이스 | `pip install pymilvus` |
| 15.6 | ChromaDB | LLM 앱 임베딩 데이터베이스 | `pip install chromadb` |
| 15.7 | LanceDB | AI 애플리케이션 벡터 데이터베이스 | `pip install lancedb` |
| 15.8 | Elasticsearch | 텍스트 및 벡터 검색 엔진 | `pip install elasticsearch` |
| 15.9 | OpenSearch | AWS 오픈소스 검색 엔진 | `pip install opensearchpy` |
| 15.10 | Vespa | AI 서빙 플랫폼 | `pip install vespa` |

---

## 1⃣6⃣ LLM 도구 (Large Language Models)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 16.1 | vLLM | LLM 고속 추론 엔진 | `pip install vllm` |
| 16.2 | Ollama | 오픈소스 LLM 실행 | `pip install ollama` |
| 16.3 | llama.cpp | C++ 기반 경량 LLM 추론 | `pip install llama-cpp-python` |
| 16.4 | text-generation-inference | Hugging Face 텍스트 생성 서버 | `pip install text-generation` |
| 16.5 | ExLlamaV2 | 극한 최적화된 Llama 추론 | `pip install exllamav2` |
| 16.6 | bitsandbytes | 양자화 및 메모리 최적화 | `pip install bitsandbytes` |
| 16.7 | AutoGPTQ | GPTQ 양자화 구현 | `pip install auto-gptq` |

---

## 1⃣7⃣ 실험 추적 (Experiment Tracking)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 17.1 | Neptune | 메타데이터 및 모델 추적 플랫폼 | `pip install neptune` |
| 17.2 | Comet ML | 실험 추적 및 최적화 | `pip install comet-ml` |
| 17.3 | ClearML | 엔터프라이즈 실험 관리 | `pip install clearml` |
| 17.4 | Sacred | 과학 실험 추적 프레임워크 | `pip install sacred` |
| 17.5 | TensorBoard | TensorFlow 시각화 도구 | `pip install tensorboard` |

---

## 1⃣8⃣ 설명 가능 AI (Explainability & Interpretability)

| # | 도구명 | 설명 | 설치 명령 |
|----|--------|------|---------|
| 18.1 | SHAP | Shapley 가치 기반 설명 | `pip install shap` |
| 18.2 | LIME | 로컬 모델 불가지론적 설명 | `pip install lime` |
| 18.3 | Captum | PyTorch 모델 해석 라이브러리 | `pip install captum` |
| 18.4 | InterpretML | Microsoft 해석 가능성 도구 | `pip install interpret` |
| 18.5 | Alibi | 모델 설명 및 이상 탐지 | `pip install alibi` |
| 18.6 | ELI5 | 머신러닝 모델 설명 | `pip install eli5` |
| 18.7 | pdpbox | 부분 의존성 플롯 | `pip install pdpbox` |
| 18.8 | TreeExplainer | 트리 모델 해석 | `pip install shap` |

---

##  추가 통합 & 유틸리티

### 데이터 검색 & 카탈로깅
| 도구명 | 설명 | 설치 |
|-------|------|------|
| Apache Atlas | 데이터 거버넌스 메타데이터 | `pip install apache-atlas-client` |
| OpenMetadata | 오픈소스 데이터 카탈로그 | `pip install openmetadata-ingestion` |
| Collibra | 엔터프라이즈 데이터 거버넌스 | `pip install collibra-platform-sdk` |

### 분산 컴퓨팅
| 도구명 | 설명 | 설치 |
|-------|------|------|
| PySpark | Apache Spark Python API | `pip install pyspark` |
| Ray | 분산 컴퓨팅 프레임워크 | `pip install ray` |
| Dask Distributed | Dask 분산 스케줄러 | `pip install dask[distributed]` |

### 성능 프로파일링
| 도구명 | 설명 | 설치 |
|-------|------|------|
| line_profiler | 라인별 프로파일링 | `pip install line_profiler` |
| memory_profiler | 메모리 사용량 프로파일링 | `pip install memory_profiler` |
| cProfile | Python 내장 프로파일러 | 내장 |
| py-spy | 샘플링 프로파일러 | `pip install py-spy` |

---

## 🔄 워크플로우 권장 조합

### 프로토타이핑 (빠른 개발)
```text
데이터: pandas + numpy
분석: scipy + statsmodels
시각화: matplotlib + seaborn
ML: scikit-learn + XGBoost
추적: MLflow
```

### 프로덕션 (확장성)
```text
데이터: polars + DuckDB + pyarrow
파이프라인: Airflow + Prefect
ML: PyTorch + Hugging Face Transformers
서빙: FastAPI + BentoML
모니터링: Weights & Biases + Evidently
```

### 대규모 데이터 (분산 처리)
```text
데이터: dask + PySpark + polars
컴퓨팅: Ray + Dask Distributed
ML: AutoGluon + H2O
스토리지: DuckDB + Milvus (벡터)
오케스트레이션: Dagster + Kubeflow
```

### RAG/LLM 애플리케이션
```text
임베딩: sentence-transformers
벡터DB: ChromaDB + LanceDB + Weaviate
검색: FAISS + Elasticsearch
LLM: vLLM + Ollama + LangChain
추적: Neptune + Weights & Biases
```

---

##  선택 기준

| 상황 | 추천 도구 |
|------|---------|
| 데이터가 **메모리에 맞음** (<10GB) | pandas + scikit-learn + matplotlib |
| 데이터가 **메모리 초과** | polars / dask / Spark |
| **속도 우선** | polars + vLLM + FAISS |
| **해석성 우선** | statsmodels + SHAP + LIME |
| **자동화 우선** | AutoGluon + PyCaret + Optuna |
| **프로덕션 서빙** | FastAPI + BentoML + KServe |
| **협업 필요** | JupyterLab + MLflow + W&B |
| **실시간 처리** | Ray + Kafka + Milvus |

---

## 📌 참고

- 모든 pip 패키지는 `pip install --upgrade` 로 최신 버전 유지
- 호환성 확인: `pip check` (의존성 충돌)
- 환경 격리: `python -m venv venv` 권장
- 버전 고정: `requirements.txt` 사용
- 더 상세한 비교: 각 도구 공식 문서 참고

---

> **작성일**: 2026-05-20  
> **적용 범위**: 모든 데이터 과학 플러그인 & 스킬  
> **정기 갱신**: 분기별 (새 도구·버전 추가)
