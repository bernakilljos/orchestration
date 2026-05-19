# RMS Enterprise Tech Toolkit — 리스크관리시스템 핵심 기술 10가지

> **목적**: RMS(Risk Management System) 제품에 적용 가능한 엔터프라이즈 기술 총정리
> **대상**: 내부통제·감사·컴플라이언스·금융·공공 영역

---

## 1. Explainable AI (XAI) — 설명 가능한 AI

### 왜 중요한가
AI가 "위험도 0.814"만 말하면 임원·감사팀이 못 믿음. **판단 근거를 감사 가능한 형태로 설명** 필수.

### RMS 적용: Explainable Risk AI
```text
위험도 상승 원인:
1. 휴일 야간 고액 결제
2. 거래 직후 ERP 접속
3. 사전 품의 없음
4. 동일 승인자 빠른 승인 반복
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **SHAP** | Shapley 값 기반 특성 중요도 | `pip install shap` |
| **LIME** | 로컬 해석 (개별 예측 설명) | `pip install lime` |
| **Captum** | PyTorch 모델 해석 (Meta) | `pip install captum` |
| **ELI5** | 모델 가중치 시각화 | `pip install eli5` |
| **InterpretML** | Microsoft XAI 통합 | `pip install interpret` |
| **Alibi** | 반사실적 설명 (Counterfactual) | `pip install alibi` |
| **OmniXAI** | 표/이미지/텍스트 통합 XAI | `pip install omnixai` |
| **AI Fairness 360** | 공정성 검사 (IBM) | `pip install aif360` |

```python
# SHAP — 위험도 판단 근거 설명
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# 개별 거래 설명
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])
# → "야간거래(+0.15), 고액(+0.12), 품의없음(+0.09), 빠른승인(+0.08)"

# 글로벌 특성 중요도
shap.summary_plot(shap_values, X_test)
```

### 감사 보고서 자동 생성
```python
def generate_risk_explanation(transaction, shap_values, feature_names):
    """감사팀용 위험도 설명 자동 생성"""
    contributions = sorted(
        zip(feature_names, shap_values),
        key=lambda x: abs(x[1]), reverse=True
    )
    
    explanation = f"위험도: {transaction['risk_score']:.3f}\n\n"
    explanation += "위험도 상승 원인:\n"
    for i, (feat, val) in enumerate(contributions[:5]):
        if val > 0:
            explanation += f"  {i+1}. {feat} (기여도: +{val:.3f})\n"
    
    return explanation
```

---

## 2. Privacy Enhancing Technologies (PETs) — 프라이버시 보호 기술

### RMS 적용: Privacy-Preserving Risk Analytics
> 개인정보와 민감 업무 데이터를 보호하면서 리스크 분석 수행

### 기술 스택
| 기술 | 설명 | 도구 |
|------|------|------|
| **익명화 (Anonymization)** | 식별 불가능하게 변환 | `pip install anonymizedf` |
| **가명처리 (Pseudonymization)** | 대체 식별자 부여 | `pip install faker` |
| **차등 프라이버시 (DP)** | 노이즈 추가로 개인 보호 | `pip install opacus` |
| **연합학습 (FL)** | 데이터 이동 없이 모델 학습 | `pip install flwr` |
| **동형암호 (HE)** | 암호화 상태에서 연산 | `pip install tenseal` |
| **안전한 다자간 연산 (MPC)** | 여러 참가자 공동 연산 | `pip install mpyc` |
| **합성데이터 (Synthetic)** | 실제와 유사한 가짜 데이터 | `pip install sdv` |
| **TEE (Trusted Execution)** | 보안 영역에서 처리 | Intel SGX / ARM TrustZone |

```python
# 차등 프라이버시 — PyTorch 모델 학습
from opacus import PrivacyEngine
privacy_engine = PrivacyEngine()
model, optimizer, data_loader = privacy_engine.make_private(
    module=model, optimizer=optimizer, data_loader=train_loader,
    noise_multiplier=1.1, max_grad_norm=1.0,
)
# ε=3.0 미만이면 개인정보 보호 우수

# 합성데이터 — 실제 거래 데이터 대체
from sdv.single_table import GaussianCopulaSynthesizer
synthesizer = GaussianCopulaSynthesizer(metadata)
synthesizer.fit(real_transactions)
synthetic = synthesizer.sample(num_rows=10000)
# → AI 학습·PoC에 사용 (실제 고객 데이터 불필요)
```

### 대기업·금융·공공 영업 키워드
- "개인정보 영향평가 통과"
- "가명정보 결합 전문기관 인증"
- "데이터 주권 보장"

---

## 3. Zero Trust Architecture — 제로 트러스트

### RMS 적용: Zero Trust RMS
> 사용자, 승인자, Agent, API, 시스템 접속을 매번 권한·상황·행동 기반으로 검증

### 핵심 원칙
```text
1. 내부망도 신뢰하지 않는다
2. 모든 접근을 매번 검증한다
3. 최소 권한 원칙 적용
4. 지속적 모니터링
```

### AI Agent 시대 Zero Trust 질문
```text
- 이 Agent가 이 전표를 조회해도 되는가?
- 이 사용자가 이 시간에 이 결재를 승인해도 되는가?
- 이 API 호출은 원래 업무 흐름에 맞는가?
- 이 데이터 export 요청은 정당한가?
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **OPA (Open Policy Agent)** | 정책 기반 접근 제어 엔진 | Docker |
| **Casbin** | RBAC/ABAC 라이브러리 | `pip install casbin` |
| **SPIFFE/SPIRE** | 서비스 ID 관리 | Docker |
| **Keycloak** | IAM (인증·인가) | Docker |
| **Istio** | 서비스 메쉬 (mTLS) | K8s |
| **HashiCorp Vault** | 시크릿 관리 + 동적 자격증명 | Docker |
| **Teleport** | 제로 트러스트 접근 프록시 | Docker |

```python
# Casbin — ABAC 정책 (상황 기반 접근 제어)
import casbin
e = casbin.Enforcer("model.conf", "policy.csv")

# 정책: 야간에는 고액 전표 조회 불가
# sub=user, obj=invoice, act=read, env={"time": "23:00", "amount": 50000000}
allowed = e.enforce("park_jisu", "invoice_001", "read", {"time": "23:00"})
# → False (야간 고액 거래 조회 차단)
```

---

## 4. Generative UI / Conversational BI — 대화형 리스크 BI

### RMS 적용: Conversational Risk BI
> 자연어 질문으로 리스크 데이터 조회, 분석, 시각화, 보고서 생성

### 사용자 질의 예시
```text
"이번 달 접대성 비용 중 위험도 높은 건만 보여줘"
"박지수 관련 HOLD 사유 요약해줘"
"승인자별 빠른 승인 패턴을 그래프로 보여줘"
"감사보고서 초안 만들어줘"
"지난 분기 대비 위험 거래 증감 추이 보여줘"
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **Streamlit** | Python 대시보드 (즉시) | `pip install streamlit` |
| **Gradio** | AI 데모 UI | `pip install gradio` |
| **Chainlit** | LLM 챗 UI | `pip install chainlit` |
| **Panel** | Python 대시보드 (HoloViz) | `pip install panel` |
| **Vanna** | 자연어→SQL 변환 | `pip install vanna` |
| **Text2SQL** | LLM 기반 SQL 생성 | LangChain 통합 |
| **AG-UI** | 에이전트→프론트엔드 | `npm install @ag-ui/client` |
| **CopilotKit** | AI 통합 React UI | `npm install @copilotkit/react-core` |

```python
# Vanna — 자연어 → SQL → 시각화
import vanna
vn = vanna.VannaDefault(model='gpt-4', api_key=KEY)
vn.connect_to_postgres(...)

# "이번 달 위험도 0.7 이상 거래 보여줘"
sql = vn.generate_sql("이번 달 위험도 0.7 이상 거래 보여줘")
df = vn.run_sql(sql)
fig = vn.generate_plotly_code(df)
```

---

## 5. Synthetic Data — 합성데이터

### RMS 적용
> 실제 고객 데이터 없이 AI 학습·테스트·PoC 수행

### 왜 중요한가
- 실제 전표·결재 데이터 = 민감 정보 (외부 반출 불가)
- AI 모델 학습에 대량 데이터 필요
- 합성데이터 = 통계적 특성 유지 + 개인정보 0

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **SDV** | 테이블·시계열·관계형 합성 (MIT) | `pip install sdv` |
| **Gretel** | 엔터프라이즈 합성데이터 (SaaS) | `pip install gretel-client` |
| **Mostly AI** | 엔터프라이즈 합성 (EU) | SaaS |
| **Faker** | 규칙 기반 가짜 데이터 | `pip install faker` |
| **Mimesis** | 고속 가짜 데이터 (100x Faker) | `pip install mimesis` |
| **CTGAN** | GAN 기반 테이블 합성 | `pip install ctgan` |
| **DataSynthesizer** | 차등 프라이버시 합성 | `pip install DataSynthesizer` |
| **ydata-synthetic** | 시계열 합성 | `pip install ydata-synthetic` |

```python
# SDV — RMS 거래 데이터 합성
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(real_transactions)

synth = CTGANSynthesizer(metadata, epochs=300)
synth.fit(real_transactions)
synthetic_data = synth.sample(num_rows=50000)

# 품질 검증
from sdv.evaluation.single_table import evaluate_quality
quality = evaluate_quality(real_transactions, synthetic_data, metadata)
print(f"합성데이터 품질: {quality.get_score():.2%}")
# → "합성데이터 품질: 89.3%"
```

---

## 6. Knowledge Graph / Semantic AI — 지식 그래프

### RMS 적용: Risk Knowledge Graph
> 사용자·조직·거래처·전표·증빙·정책·감사기준을 의미 기반으로 연결

### 관계 예시
```text
[박지수] --소속--> [경영지원팀]
[박지수] --결재--> [전표_001]
[전표_001] --거래처--> [ABC물산]
[전표_001] --증빙--> [영수증_001]
[전표_001] --위반?--> [품의규정 3조]
[ABC물산] --계약--> [연간계약_2026]
[전표_001] --승인자--> [김팀장] --빠른승인--> [패턴_의심]
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **Neo4j** | 그래프 DB 표준 | Docker |
| **NetworkX** | Python 그래프 분석 | `pip install networkx` |
| **ArangoDB** | 멀티모델 (문서+그래프) | Docker |
| **Amazon Neptune** | 관리형 그래프 DB | AWS |
| **LlamaIndex Knowledge Graph** | LLM + 지식 그래프 | `pip install llama-index` |
| **LangChain GraphQA** | LLM 기반 그래프 QA | `pip install langchain` |
| **rdflib** | RDF/SPARQL 처리 | `pip install rdflib` |
| **pyvis** | 그래프 시각화 | `pip install pyvis` |

```python
# Neo4j — 위험 관계 탐지
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "pw"))

with driver.session() as session:
    # 빠른 승인 패턴 탐지
    result = session.run("""
        MATCH (approver:User)-[a:APPROVED]->(invoice:Invoice)
        WHERE a.elapsed_seconds < 60
        AND invoice.amount > 10000000
        WITH approver, COUNT(a) AS fast_approvals
        WHERE fast_approvals > 5
        RETURN approver.name, fast_approvals
        ORDER BY fast_approvals DESC
    """)
    for record in result:
        print(f"⚠️ {record['approver.name']}: {record['fast_approvals']}건 빠른 승인")
```

---

## 7. Event-Driven Architecture — 이벤트 기반 아키텍처

### RMS 적용: Real-Time Event Risk Pipeline
> 카드·전표·승인·접속·문서열람 이벤트 발생 즉시 리스크 판단

### 이벤트 흐름
```text
카드 승인 발생
  → 이벤트 수신 (Kafka)
  → 룰 탐지 (Flink/Python)
  → 그래프 업데이트 (Neo4j)
  → 위험도 계산 (XAI 모델)
  → HOLD 후보 등록
  → 알림 (Slack/Email/Push)
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **Apache Kafka** | 이벤트 스트리밍 표준 | Docker Compose |
| **Apache Flink** | 실시간 스트림 처리 | Docker |
| **Redis Streams** | 경량 이벤트 큐 | `pip install redis` |
| **NATS** | 초경량 메시징 | Docker |
| **Debezium** | CDC (DB 변경 캡처) | Docker |
| **Celery** | Python 비동기 태스크 | `pip install celery[redis]` |
| **FastStream** | Python 이벤트 프레임워크 | `pip install faststream[kafka]` |
| **Temporal** | 워크플로우 오케스트레이션 | Docker |

```python
# FastStream — 실시간 리스크 이벤트 처리
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.subscriber("card-transactions")
async def handle_transaction(data: dict):
    risk_score = calculate_risk(data)
    if risk_score > 0.7:
        await register_hold(data, risk_score)
        explanation = explain_risk(data, risk_score)
        await notify_auditor(data, explanation)
```

---

## 8. Data Fabric / Data Mesh — 데이터 통합

### RMS 적용: Risk Data Fabric
> 분산된 업무 데이터를 RMS가 분석 가능한 형태로 연결하는 데이터 통합 계층

### RMS가 먹어야 하는 데이터
```text
[ERP] ──────────────┐
[전자결재] ───────────┤
[법인카드] ───────────┤
[인사시스템] ──────────┤──→ [Risk Data Fabric] ──→ [RMS 분석 엔진]
[권한관리] ───────────┤
[문서중앙화] ──────────┤
[출입시스템] ──────────┤
[메일/메신저] ─────────┤
[감사시스템] ──────────┘
```

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **Airbyte** | 오픈소스 ETL (350+ 커넥터) | Docker |
| **Apache Airflow** | 워크플로우 오케스트레이션 | `pip install apache-airflow` |
| **dbt** | SQL 변환 (ELT) | `pip install dbt-core` |
| **Great Expectations** | 데이터 품질 검증 | `pip install great-expectations` |
| **Apache Spark** | 대규모 데이터 처리 | `pip install pyspark` |
| **Trino** | 분산 SQL 쿼리 엔진 | Docker |
| **Delta Lake** | 데이터 레이크 ACID | `pip install delta-spark` |
| **Apache Iceberg** | 테이블 포맷 (Netflix) | Spark 플러그인 |
| **Dagster** | 데이터 오케스트레이션 | `pip install dagster` |
| **Prefect** | 워크플로우 (Airflow 대안) | `pip install prefect` |

---

## 9. Green AI / Sustainable IT — 지속가능한 AI

### 왜 중요한가
- ESG 보고서에 AI 탄소 배출 포함 필요
- 대형 모델 학습 = 탄소 배출 큼
- 경량화·효율화 = 비용 절감 + ESG 점수

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **CodeCarbon** | ML 학습 탄소 배출 측정 | `pip install codecarbon` |
| **CarbonTracker** | GPU 에너지 추적 | `pip install carbontracker` |
| **Zeus** | GPU 에너지 최적화 | `pip install zeus-ml` |
| **Eco2AI** | 에코 AI 추적 | `pip install eco2ai` |

```python
# CodeCarbon — AI 학습 탄소 배출 측정
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()
model.fit(X_train, y_train)  # 모델 학습
emissions = tracker.stop()
print(f"탄소 배출: {emissions:.4f} kg CO2")
# → ESG 보고서에 포함
```

### RMS 적용
- 모델 경량화 (Phi-3 / Gemma 2B vs GPT-4)
- 추론 최적화 (ONNX / TensorRT)
- 캐싱 (반복 분석 캐시)
- 에너지 사용 보고 (ESG 대응)

---

## 10. AI Governance — AI 거버넌스

### RMS 적용: Responsible Risk AI
> AI 모델의 공정성·투명성·책임성 보장

### 프레임워크
| 프레임워크 | 제공 | 설명 |
|-----------|------|------|
| **EU AI Act** | EU | AI 규제 법률 (2024 발효) |
| **NIST AI RMF** | 미국 | AI 리스크 관리 프레임워크 |
| **ISO 42001** | 국제 | AI 관리 시스템 표준 |
| **금융위 AI 가이드라인** | 한국 | 금융 AI 사용 기준 |

### 도구
| 도구 | 특장 | 설치 |
|------|------|------|
| **AI Fairness 360** | 공정성 검사 (IBM) | `pip install aif360` |
| **Responsible AI Toolbox** | 공정성+해석성 (MS) | `pip install raiwidgets` |
| **Guardrails AI** | 출력 검증 | `pip install guardrails-ai` |
| **NeMo Guardrails** | 대화 안전 (NVIDIA) | `pip install nemoguardrails` |
| **Giskard** | ML 모델 검증 + 취약점 탐지 | `pip install giskard` |
| **Evidently** | ML 모니터링 (드리프트 감지) | `pip install evidently` |
| **WhyLabs** | 데이터+모델 관측 | `pip install whylogs` |

---

## RMS 기술 스택 종합 아키텍처

```text
┌─────────────────────────────────────────────────────────┐
│                    RMS Architecture                      │
│                                                         │
│  ┌─── Data Fabric ───┐  ┌─── AI Engine ────┐           │
│  │ ERP·결재·카드·인사 │  │ XAI (SHAP/LIME) │           │
│  │ Airbyte → Kafka   │──│ Knowledge Graph  │           │
│  │ dbt → Delta Lake  │  │ Synthetic Data   │           │
│  └───────────────────┘  └────────┬─────────┘           │
│                                  │                      │
│  ┌─── Event Pipeline ──┐  ┌─────┴── Security ────┐    │
│  │ Kafka → Flink       │  │ Zero Trust (OPA)      │    │
│  │ 실시간 룰 탐지       │  │ PETs (DP/FL/HE)      │    │
│  │ HOLD 자동 등록      │  │ AI Governance         │    │
│  └─────────────────────┘  └──────────────────────┘    │
│                                                         │
│  ┌─── UI ────────────────────────────────────────┐     │
│  │ Conversational BI (자연어 질의)                  │     │
│  │ Generative UI (동적 대시보드)                    │     │
│  │ XAI 설명 보고서 자동 생성                        │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  Green AI: 탄소 배출 측정 + 모델 경량화                   │
└─────────────────────────────────────────────────────────┘
```
