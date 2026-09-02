# AI 신기술 학습 자료 — 순수 기술편

> **목적**: 사업화·회사 매핑 0%, 기술 자체만 깊이 학습
> **대상**: 양자모델 · LLM · 피지컬 AI · 생성형 AI · UEBA 분야 학습자
> **작성**: 2026-06-02

---

## 1. Reasoning Models (추론 모델)

### 정의
모델이 답을 내기 전에 **사고 과정 (chain-of-thought)** 을 길게 생성한 후, 그 사고를 거쳐 최종 답을 도출하는 LLM. 추론에 더 많은 compute 를 쓰는 것 = 정답률 향상.

### 학문적 배경
- Wei et al. 2022, "Chain-of-Thought Prompting Elicits Reasoning"
- Kojima et al. 2022, "Let's think step by step"
- OpenAI 2024, "Learning to Reason with LLMs" (o1)
- DeepSeek 2025, "DeepSeek-R1: Incentivizing Reasoning"

### 핵심 동작 원리

```text
질문 → [내부 사고 토큰 생성 (수천~수만 token)]
       │ - 가설 세우기
       │ - 단계별 분해
       │ - 자기 검증
       │ - 잘못된 경로 폐기
       │ - 다시 시도
       └─ → 최종 답
```

**Test-Time Compute Scaling** (Snell et al. 2024):
- 같은 모델 + 더 긴 사고 = 더 나은 답
- compute 와 정확도 ≈ log-linear 관계
- AIME (수학), Codeforces (코딩) 벤치마크에서 입증

### 벤치마크 (2025 기준)

| 벤치마크 | GPT-4o | o1 | o3 | DeepSeek-R1 |
|---|---|---|---|---|
| AIME 2024 (수학) | 13.4% | 83.3% | **96.7%** | 79.8% |
| Codeforces | 11% | 89% | **95%** | 96.3% |
| GPQA Diamond | 50.6% | 78% | **87.7%** | 71.5% |

### 한계
- 추론 시간 비용 ↑ (10-100배)
- 단순 질문엔 과잉
- 환각 (hallucination) 여전 존재
- 사고 과정 자체가 truthful 인지 검증 어려움

### 다음 진화
- Process Reward Models (PRM) — 사고 과정 자체를 단계별 평가
- Multi-Agent Reasoning Debate
- Tree-Search with LLM (AlphaProof 식)

### 출처
- arxiv.org/abs/2201.11903 (CoT)
- openai.com/index/learning-to-reason-with-llms (o1)
- arxiv.org/abs/2501.12948 (DeepSeek R1)

---

## 2. Self-Critique / Reflexion

### 정의
AI 가 자기 답을 **다른 AI (또는 자기 자신)** 가 비판하고, 비판을 받아 답을 수정하는 반복 루프.

### 학문적 배경
- Yao et al. 2023, "Reflexion: Language Agents with Verbal Reinforcement Learning"
- Madaan et al. 2023, "Self-Refine"
- Asai et al. 2023, "Self-RAG"
- Bai et al. 2022, "Constitutional AI" (Anthropic)

### 알고리즘 — Reflexion 의사코드

```javascript
function reflexion_loop(query, max_iter, threshold):
    actor_prompt = query
    history = []
    for i in 1..max_iter:
        answer = actor_llm(actor_prompt)
        critique = critic_llm("답: {answer}. 비판하라.")
        score = parse(critique)
        history.append((answer, critique, score))
        if score >= threshold:
            return answer
        actor_prompt += f"\n이전 답: {answer}\n비판: {critique}\n수정하라."
    return best(history)
```

### 변형 비교

| 패턴 | 핵심 | 차이 |
|---|---|---|
| **Reflexion** | 자기 비판 → 재시도 | history 누적 활용 |
| **Self-Refine** | 답 → 피드백 → 수정 | iterative, 같은 모델 |
| **Self-RAG** | 검색 답 자기 평가 | RAG 결합 |
| **Constitutional AI** | 헌법 (원칙) 기반 자기 규제 | 외부 원칙 명시 |
| **Multi-Agent Debate** | 여러 AI 토론 → 합의 | parallel, 다양성 |
| **Chain-of-Verification** | 답 → 검증 질문 → 답 | 단계별 검증 |

### 효과 (실험)
- HotpotQA: 32% → 52% (Reflexion, GPT-4)
- HumanEval (코드): 67% → 91%
- 거짓양성 감소: 평균 40-60%

### 한계
- Critic 이 잘못 판단 시 오히려 답 악화
- 무한 루프 위험 (점수 임계 도달 못함)
- compute 비용 N배
- 비판 평가 자체의 정확도 한계

### 출처
- arxiv.org/abs/2303.11366 (Reflexion)
- arxiv.org/abs/2303.17651 (Self-Refine)
- arxiv.org/abs/2310.11511 (Self-RAG)
- arxiv.org/abs/2212.08073 (Constitutional AI)

---

## 3. Causal AI

### 정의
**상관관계 (correlation) 가 아닌 인과관계 (causation)** 를 데이터에서 추론하는 AI. Judea Pearl 의 do-calculus 와 인과 그래프 (DAG) 기반.

### Pearl 의 인과 사다리 (Ladder of Causation)

| 단계 | 질문 형태 | 수학 | 예 |
|---|---|---|---|
| 1. Association (연관) | "본다" | P(Y\|X) | 야근하는 사람이 부정 저지른다? |
| 2. Intervention (개입) | "한다" | P(Y\|do(X)) | 야근 강제하면 부정 늘어? |
| 3. Counterfactual (반사실) | "상상한다" | P(Y_x'\|X=x,Y=y) | 그 사람이 야근 안 했어도 부정 저질렀을까? |

LLM·일반 ML 은 1 단계만. Causal AI 가 2·3 단계 가능.

### 핵심 도구·수식

**do-calculus** (Pearl 의 3 규칙):
1. **Insertion/deletion of observations**
   P(y\|do(x), z, w) = P(y\|do(x), w) if Z ⊥ Y\|X,W in G_X̄
2. **Action/observation exchange**
   P(y\|do(x), do(z), w) = P(y\|do(x), z, w) if Z ⊥ Y\|X,W in G_X̄,Z_
3. **Insertion/deletion of actions**
   P(y\|do(x), do(z), w) = P(y\|do(x), w) if Z ⊥ Y\|X,W in G_X̄,Z(W)_

### DAG (Directed Acyclic Graph) 예제

```text
스트레스(S) ─→ 야근(O)
       │         │
       ▼         ▼
       부정(F)  ←┘
업무량(W) ─→ 야근
       │
       └────→ 부정
```

여기서 야근의 진짜 인과 효과 = backdoor adjustment:
P(F\|do(O)) = Σ_s,w P(F\|O, S=s, W=w) · P(S=s, W=w)

### 구현 도구

```python
# DoWhy (Microsoft)
from dowhy import CausalModel

model = CausalModel(data, treatment='야근', outcome='부정', graph=dag_str)
identified = model.identify_effect()
estimate = model.estimate_effect(identified, method='backdoor.propensity_score_matching')
refute = model.refute_estimate(identified, estimate, method='random_common_cause')
```

### Causal Discovery (그래프 자동 발견)
- **PC algorithm** (Spirtes·Glymour): 조건부 독립성 테스트
- **FCI**: 잠재 변수 허용
- **NOTEARS** (Zheng et al.): 연속 최적화 기반
- **CausalLearn**, **CausalNex** OSS

### 한계
- DAG 가정 (cycle 없음)
- 잠재 confounder 미관측 시 한계
- 데이터 양 큰 요구
- 도메인 지식 의존

### 출처
- Pearl 2009, "Causality: Models, Reasoning, and Inference"
- Pearl 2018, "The Book of Why"
- arxiv.org/abs/1605.03661 (DoWhy)

---

## 4. Agentic AI

### 정의
LLM 이 **자율 목표 → 계획 → 도구 호출 → 결과 관찰 → 다음 단계** 의 loop 를 스스로 돌리는 시스템. 단일 응답 X.

### 패러다임 — ReAct (Reasoning + Acting)

```text
Thought_1: 무엇을 알아야 하나?
Action_1: search("정보 X")
Observation_1: 검색 결과 ...
Thought_2: 결과로부터 무엇을 알았나?
Action_2: calculate(...)
...
Final Answer: ...
```

(Yao et al. 2022, ReAct)

### 주요 아키텍처

| 시스템 | 특징 |
|---|---|
| **AutoGPT** (2023) | 첫 self-prompting agent |
| **BabyAGI** | task list 관리 + LLM |
| **LangChain Agents** | 표준화 도구 호출 |
| **AutoGen** (Microsoft) | Multi-agent 대화 |
| **CrewAI** | 역할 기반 (Researcher·Writer·Critic) |
| **LangGraph** | 상태 기반 워크플로우 (graph) |
| **Claude Computer Use** | 화면 픽셀 보고 클릭 |
| **OpenAI Operator** | 웹 자율 |

### MCP (Model Context Protocol) — Anthropic 표준

```text
LLM ⇄ MCP Server (도구·자원)
       │
       ├─ Slack, Gmail, GitHub
       ├─ Filesystem, DB
       └─ Custom tools
```

JSON-RPC 기반 표준. 도구 간 호환성 표준화.

### Agent 평가 벤치마크
- **SWE-Bench** (소프트웨어 엔지니어링): Claude 3.7 — 70%+
- **WebArena** (웹 탐색): GPT-4 — 14%
- **OSWorld** (운영체제 작업): Claude — 22%
- **τ-bench** (사용자 시뮬레이션): Claude·GPT-4 — 50%

### 한계
- 긴 작업에서 일관성 잃음 (drift)
- 도구 호출 실패 시 회복 어려움
- 환각 (잘못된 행동) — 실제 영향
- 비용·시간 폭증
- 안전성 (보안·신뢰)

### 출처
- arxiv.org/abs/2210.03629 (ReAct)
- modelcontextprotocol.io (MCP)
- anthropic.com/news/computer-use

---

## 5. World Models

### 정의
관찰 (영상·이미지) 로부터 **물리 세계의 동역학** 을 학습하는 모델. 미래 상태 예측 가능. NVIDIA Jensen Huang 이 "Physical AI" 의 핵심으로 강조.

### 학문적 배경
- Ha & Schmidhuber 2018, "World Models" (오리지널)
- Hafner et al. 2019-2024, "DreamerV1·V2·V3" (강화학습 + WM)
- OpenAI 2024, "Video generation as world simulators" (Sora)
- NVIDIA 2025, "Cosmos World Foundation Models"

### 핵심 아키텍처 (Sora·Cosmos 식)

```text
입력: 영상 frames (텍스트 + 액션 옵션)
      ↓
   Video Tokenizer (3D VAE — spatio-temporal compression)
      ↓
   Diffusion Transformer (DiT)
      ↓
   Tokens → Pixel frames (디코딩)
      ↓
출력: 미래 영상 (또는 텍스트→영상 생성)
```

**Diffusion + Transformer 결합**:
- Latent space 에서 노이즈 점진적 제거
- Spatio-temporal attention
- Text·action conditioning

### NVIDIA Cosmos (2025)

3 모델군:
- **Cosmos-Predict**: 자율 운전·로봇용 미래 예측
- **Cosmos-Transfer**: 도메인 변환 (sim → real)
- **Cosmos-Reason**: 영상 기반 추론

### V-JEPA (Meta)
- Joint-Embedding Predictive Architecture
- 픽셀 생성 X, **임베딩 공간 예측**
- 효율적이고 self-supervised

### 활용
- 로봇 학습용 시뮬 데이터 무한 생성
- 자율주행 시나리오 시뮬레이션
- 게임·메타버스 환경 생성
- 영상 부분 편집·완성 (inpainting)

### 한계
- 물리 법칙 위반 가능 (이상한 손가락·중력 무시)
- 긴 영상 일관성 어려움
- compute 폭증 (GPU 수백~수천)
- 실제 카메라 데이터 학습 시 편향 학습 위험

### 출처
- Ha & Schmidhuber: arxiv.org/abs/1803.10122
- DreamerV3: arxiv.org/abs/2301.04104
- Sora: openai.com/research/video-generation-models-as-world-simulators
- NVIDIA Cosmos: developer.nvidia.com/cosmos

---

## 6. Vision-Language-Action (VLA)

### 정의
**비전 + 언어 + 행동 (로봇 액션)** 을 통합 학습한 foundation model. 로봇이 보고 듣고 자율 행동.

### 진화 흐름

| 연도 | 모델 | 특징 |
|---|---|---|
| 2023 | RT-1 (Google) | 첫 대규모 로봇 transformer |
| 2023 | RT-2 | Vision-Language model + 로봇 액션 token |
| 2024 | OpenVLA | 오픈소스 VLA |
| 2024 | Pi0 (Physical Intelligence) | flow matching 기반 |
| 2025 | NVIDIA GR00T | 휴머노이드 foundation model |
| 2025 | RT-X (DeepMind) | 22개 로봇 종 학습 |

### RT-2 아키텍처

```text
이미지 + 언어 명령 → VLM (PaLI-X / PaLM-E)
                        ↓
              [V/L tokens + Action tokens]
                        ↓
                 로봇 액션 (6-DoF gripper 등)
```

핵심: **action 을 별도 vocabulary token 으로 처리** → LLM 그대로 활용.

### Pi0 (Physical Intelligence 2024)

- Flow matching (diffusion 변형)
- 50+ 로봇 종 학습
- 자연어 명령 → 연속 액션 (joint torque)
- 더 부드러운 연속 행동 (token 양자화 X)

### 학습 데이터
- Open X-Embodiment Dataset: 22 로봇 종, 1M+ trajectories
- Bridge V2, RT-1 dataset, DROID
- Egocentric video (Ego4D, EPIC-Kitchens) — 인간 시연 활용

### 평가
- 일반화 — 학습 안 한 객체·환경에서 zero-shot 성능
- Long-horizon — 100+ step 작업
- Compositionality — 새 명령 조합

### 한계
- 실제 로봇 데이터 부족 (인간 시연으로 보완)
- Safety — 행동 보장 어려움
- 일반화 한계 (도메인 gap)
- 비용 — GPU + 로봇 hardware

### 출처
- RT-2: robotics-transformer2.github.io
- OpenVLA: openvla.github.io
- Pi0: physicalintelligence.company/blog/pi0
- NVIDIA GR00T: nvidia.com/en-us/ai/project-gr00t/

---

## 7. Quantum Machine Learning (QML)

### 정의
**양자 컴퓨터의 양자 중첩·얽힘** 을 활용해 ML 알고리즘을 가속·확장.

### 양자 우위 (Quantum Advantage) 가능 영역

| 알고리즘 | 양자 우위 |
|---|---|
| **Shor** | 소인수분해 (RSA 깨기) — exponential |
| **Grover** | 비정렬 검색 — quadratic |
| **HHL** | 선형 시스템 — exponential (조건 있음) |
| **QAOA** | 최적화 — heuristic 우위 |
| **VQE** | 화학 시뮬 — quadratic-cubic |
| **Quantum Kernel** | 분류 — 특정 feature space |

### Variational Quantum Circuit (VQC)

```text
classical 데이터 x
       ↓
[Feature Map U(x)] — 양자 상태 인코딩
       ↓
[Ansatz U(θ)] — 학습 가능 파라미터 (회전 게이트)
       ↓
[Measurement] — Pauli observable 측정
       ↓
classical loss → gradient → θ 업데이트 (classical optimizer)
```

→ **Quantum-Classical Hybrid**: 양자 회로 + classical gradient descent.

### Qiskit 예제 (Python)

```python
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.circuit.library import RawFeatureVector
from qiskit.circuit.library import RealAmplitudes
from qiskit.primitives import Sampler

feature_map = RawFeatureVector(num_features=4)
ansatz = RealAmplitudes(num_qubits=4, reps=3)
vqc = VQC(sampler=Sampler(), feature_map=feature_map, ansatz=ansatz)
vqc.fit(X_train, y_train)
score = vqc.score(X_test, y_test)
```

### 현재 양자 하드웨어 (2025)
- **IBM Heron** — 156 qubit, error rate ~0.3%
- **Google Willow** — 105 qubit, surface code error correction
- **IonQ Forte** — 36 qubit (trapped ion, high fidelity)
- **Quantinuum H2** — 56 qubit
- **PsiQuantum** — photonic, fault-tolerant 목표

### NISQ vs FTQC
- **NISQ** (Noisy Intermediate-Scale Quantum): 현재 — 양자 노이즈 큼, 작은 문제만
- **FTQC** (Fault-Tolerant): 미래 (2030+) — 양자 오류 정정으로 큰 문제 가능

### 한계
- 양자 오류·디코히어런스 — 짧은 회로만
- Barren plateau — 파라미터 gradient 사라짐
- Data encoding 비용 (classical → quantum) — bottleneck
- 양자 우위 입증된 ML 문제 극히 제한적

### 출처
- Biamonte et al. 2017, Nature, "Quantum Machine Learning"
- Schuld 2021, "Machine Learning with Quantum Computers" (책)
- qiskit.org/learn
- pennylane.ai/qml

---

## 8. GraphRAG (Graph Retrieval-Augmented Generation)

### 정의
Vector RAG 의 한계 (텍스트 청크 간 관계 모름) 를 극복하기 위해 **지식 그래프** 를 LLM 검색에 결합한 RAG 패턴.

### Microsoft GraphRAG (2024) 아키텍처

```text
1. Indexing (오프라인)
   원문 → LLM 추출 → entity·relation
              ↓
       Knowledge Graph 구축
              ↓
   Leiden 알고리즘 → Community detection
              ↓
   각 Community → LLM summary

2. Query Time
   질의 → 관련 community 선택
              ↓
   community summary + graph traversal
              ↓
   LLM 이 답 생성
```

### Vector RAG vs GraphRAG

| 항목 | Vector RAG | GraphRAG |
|---|---|---|
| 검색 방식 | embedding 유사도 | graph traversal + community |
| 관계 표현 | 묵시적 | **명시적** (edge) |
| 다단계 추론 | 약함 | 강함 |
| 전사 패턴 발견 | 못함 | community detection |
| 사전 비용 | 임베딩만 | LLM 추출 비용 |
| 질의 응답 | local context | local + global |

### 그래프 알고리즘

| 알고리즘 | 용도 |
|---|---|
| **Leiden** | Community detection (Louvain 개선) |
| **PageRank** | 노드 중요도 |
| **Betweenness Centrality** | 그래프 다리 식별 |
| **Random Walk** | embedding (node2vec, DeepWalk) |
| **Cypher (Neo4j)** | 그래프 질의 언어 |

### Local vs Global Search (Microsoft GraphRAG)

- **Local Search**: 특정 entity 중심 — "X 회사의 임원은?"
- **Global Search**: 전체 패턴 — "이 데이터셋의 주요 테마는?"

### 한계
- LLM 추출 비용 (인덱싱)
- 그래프 정확도 = LLM 추출 정확도
- 매우 큰 그래프 — 효율 문제
- 도메인 schema 설계 필요

### 출처
- microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery
- github.com/microsoft/graphrag
- arxiv.org/abs/2404.16130 (GraphRAG 논문)
- Neo4j Graph Data Science Library

---

## 9. Mechanistic Interpretability

### 정의
LLM 내부의 **attention head·MLP·feature** 가 무엇을 어떻게 계산하는지 **회로 (circuit) 단위로 분해·해석**.

### 학문적 배경 — Anthropic 핵심 연구
- Elhage et al. 2021, "A Mathematical Framework for Transformer Circuits"
- Olsson et al. 2022, "In-context Learning and Induction Heads"
- Templeton et al. 2024, "Scaling Monosemanticity" (Claude 3 Sonnet 분해)

### 핵심 개념

| 개념 | 설명 |
|---|---|
| **Circuit** | 특정 작업 수행하는 attention head·MLP 의 작은 부분 그래프 |
| **Feature** | 의미 단위 (예: "골든게이트 브리지" feature) |
| **Superposition** | 한 뉴런이 여러 feature 표현 (압축) |
| **Sparse Autoencoder (SAE)** | superposition 분해 도구 |
| **Activation Patching** | 일부 activation 만 바꿔 인과 검증 |

### Induction Head (간단 예)

Transformer 의 핵심 회로 중 하나:
1. Previous Token Head: "현재 토큰" → "직전 토큰" attention
2. Induction Head: pattern "...A B ... A" 보면 "B" 예측

→ **In-context learning 의 기초 메커니즘**.

### Sparse Autoencoder 작동

```text
LLM activation (12,288 dim) 
    ↓
SAE encoder (sparse, e.g. 1M features)
    ↓ (대부분 0, 일부 활성)
SAE decoder
    ↓
원본 activation 재구성
```

→ 활성된 sparse feature 가 **monosemantic** (한 의미만 표현).

### 실제 발견 (Claude 3 Sonnet, 2024)
- "Golden Gate Bridge" feature
- "Code error" feature  
- "Sycophancy" feature
- "내부 모순" feature
- "비밀 / 거짓말" feature

→ activation 켜고 끄면 모델 행동 변경 가능 (Golden Gate Claude 시연).

### 도구
- **TransformerLens** (Neel Nanda) — Python 라이브러리
- **Anthropic SAE 도구**
- **Goodfire AI** — 상용 SaaS
- **Captum** (Meta) — PyTorch 해석

### 한계
- 큰 모델 (70B+) 해석 어려움
- Sparse feature 발견 수동
- Feature 간 상호작용 복잡
- 안전성 보장 X

### 출처
- transformer-circuits.pub
- arxiv.org/abs/2209.10652 (Induction Heads)
- anthropic.com/news/mapping-mind-language-model

---

## 10. Affective Computing / Emotion AI

### 정의
인간의 **감정·정서·인지 상태** 를 컴퓨터가 인식·해석·시뮬·표현하는 분야. Rosalind Picard (MIT) 1995 정립.

### 신호 채널 (멀티모달)

| 채널 | 측정 | 도구 |
|---|---|---|
| **얼굴** | 미세표정·표정 변화·시선·동공 | OpenFace, Affectiva |
| **음성** | prosody (pitch·jitter·shimmer·energy) | openSMILE, librosa |
| **텍스트** | sentiment·emotion intensity | BERT-emotion, VADER |
| **생체** | HRV·GSR·EEG·체온 | Empatica E4, BIOPAC |
| **행동** | 타이핑 리듬·마우스 패턴·걸음걸이 | Behavioral Biometrics |
| **언어 패턴** | LIWC·perplexity·pause | NLP 분석 |

### Ekman 6 기본 감정 (전통적)
Joy · Sadness · Anger · Fear · Surprise · Disgust

### Plutchik Wheel (8 → 32 감정)
기본 8 + 강도 + 조합 → 32

### Dimensional Models
- **Valence-Arousal** (Russell): 2D 평면
- **PAD** (Mehrabian): Pleasure-Arousal-Dominance (3D)

### 핵심 데이터셋
- **AffectNet** — 1M 얼굴 이미지
- **CK+** (Cohn-Kanade) — 표정 시퀀스
- **IEMOCAP** — 음성·텍스트·얼굴
- **DEAP** — EEG + 음악 감정
- **WIDER FACE Emotion**

### Hume EVI (2024)
- Empathic Voice Interface
- 100+ 감정 분류 (단순 6 → 100+)
- 실시간 prosody + 언어 통합
- API 공개

### 모델 아키텍처

```text
얼굴 frames → 3D CNN / Vision Transformer → emotion logits
음성 spectrogram → wav2vec / HuBERT → prosody features
텍스트 → BERT-emotion → sentiment
        ↓
   Multimodal Fusion (late·attention·tensor)
        ↓
   최종 감정 분류 / dimensional 점수
```

### 한계
- **문화·개인차** — 같은 표정 다른 의미
- **연기 vs 진짜** 구분 어려움
- **윤리 문제** — 동의 없는 감정 추적 (EU AI Act 일부 금지)
- **소수자 편향** — 학습 데이터 편향
- 자기보고 (self-report) 와의 mismatch

### 윤리·법규
- **EU AI Act**: 직장·교육에서 감정 인식 — **고위험 또는 금지**
- 미국: 공중 보건·자율주행 영역 가능
- 한국: 명시적 규제 X (가이드 단계)

### 출처
- Picard 1997, "Affective Computing" (책)
- Hume AI: hume.ai
- Affectiva (SmartEye 인수): affectiva.com
- arxiv.org/abs/2308.02839 (Multimodal Emotion 서베이)

---

## 📚 추천 학습 경로

### 입문 (1개월)
1. Wei et al. "Chain-of-Thought" 논문 — Reasoning 입문
2. Yao "ReAct" + "Reflexion" — Agent 기초
3. Pearl "Book of Why" — Causal AI 직관

### 중급 (3개월)
4. Anthropic "Mapping the Mind" — Mechanistic Interpretability
5. Microsoft "GraphRAG" 논문 + OSS 실습
6. NVIDIA Cosmos 튜토리얼 — Physical AI

### 상급 (6개월)
7. IBM Quantum Network 가입 + Qiskit textbook
8. RT-2·OpenVLA 논문 + 로봇 시뮬
9. Sparse Autoencoder (TransformerLens) 실습

### 도구 환경 구축
```bash
# Python 환경
pip install dowhy graphrag qiskit transformer-lens
pip install dspy openai anthropic
pip install peft trl bitsandbytes  # fine-tuning

# 양자
pip install qiskit qiskit-machine-learning pennylane

# 그래프
pip install neo4j networkx

# 인과
pip install dowhy econml causalml

# 해석
pip install transformer-lens captum shap
```

---

## 참조 모음

- arxiv.org/list/cs.LG/recent — 최신 ML 논문
- transformer-circuits.pub — Mechanistic Interpretability
- hume.ai/research — Emotion AI
- developer.nvidia.com — Physical AI
- quantum-computing.ibm.com — Quantum
- microsoft.com/en-us/research/group/causal-ai — Causal

---

## 델타 (2026-08-19 · 순수 기술 갱신)

### 신규 순수 기술 4종

**A. Long-horizon Reasoning Control (Qwen 3.8-27B · 2026-08)**
- 사용자 지정 reasoning depth (`low`·`medium`·`high`) + context reuse/delete 제어
- edge 시나리오 (긴 문서 검토 시 중간 사고 삭제로 VRAM 절약)
- 원조: Alibaba Qwen team

**B. Multiagent Advisor Pattern (Anthropic Managed Agents · 2026-08-07)**
- primary thread 가 mid-turn 다른 model consulting · consulted model 은 stateless
- 계층 프롬프트 (main system + advisor 별 mini-system)
- 관련 논문: `Anthropic Managed Agents Documentation` (research preview)

**C. Session Budget Enforcement (Anthropic · 2026-08-07)**
- hard cap 도달 시 새 model request 시작 없이 `budget_reached` stop
- deployment level (모든 세션 공통) + session level override
- 원조: LLM cost governance research 흐름 (2025~ 흐름의 표준화)

**D. Adaptive Thinking Consolidation (Claude Sonnet 5 · Opus 5 · 2026-06~07)**
- `thinking:{"type":"enabled",budget_tokens}` (manual) 폐기 · adaptive 만 유지
- turn 별 필요 여부 자동 판단 · 낭비 사고 토큰 감소
- Opus 5 는 `disabled` 상태에서 effort xhigh/max = 400 error (thinking 강제)

### Interpretability 트렌드

- **Anthropic Risk Report v2 (2026-08-14 · RSP v3.4)**:
  - catastrophic-misalignment estimation `very low → low`
  - 근거: cybersecurity eval disclosure 관련 불확실성
  - Model 2 (Mythos 5 초과) 내부 approval 결과 새 misalignment 프로파일 없음
  - 6개월마다 발행 · 규제 응답 근거

**참조 링크 추가**:
- huggingface.co/Qwen/Qwen3.8-27B — 오픈 웨이트
- platform.claude.com/docs/en/managed-agents — Managed Agents 표준
- anthropic.com/news — Risk Report v2

**관련 memory**: [[ai-tech-2026-08-late]]
