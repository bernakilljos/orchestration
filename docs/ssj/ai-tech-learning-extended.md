# AI 신기술 학습 자료 — 확장편 (50+ 추가)

> 기본 10 기술 (`ai-tech-learning-pure.md`) 외에 진짜 뜨는 신기술 50+ 추가
> 카테고리 12개 × 4-10 기술 = 70+ 기술
> 작성: 2026-06-02

---

## A. LLM 핵심 아키텍처 진화 (Transformer 대안·진화)

### A1. Mixture of Experts (MoE)
**정의**: 토큰마다 다른 "전문가" subnetwork 활성. 전체 파라미터는 크지만 token 당 활성 파라미터만 사용.
- **DeepSeek V3** (671B 총 / 37B 활성), **Llama 4** (Mixtral 8x22B), **Switch Transformer**
- 핵심: Top-K routing + Load balancing loss
- 출처: arxiv.org/abs/1701.06538 (Shazeer 2017)

### A2. State Space Models (SSM) — Mamba 계열
**정의**: 시간 t 에 hidden state h_t 의 선형 dynamic system 으로 sequence 처리. Transformer O(n²) → O(n) 선형.
- **Mamba** (Gu·Dao 2023), **Mamba-2**, **Jamba** (AI21 — MoE+Mamba 하이브리드)
- 입력 의존 selective state space (HiPPO 기반)
- 1M+ context 효율
- 출처: arxiv.org/abs/2312.00752

### A3. Diffusion LLM
**정의**: 텍스트 생성에 diffusion 적용. 병렬 디코딩 가능.
- **Mercury** (Inception Labs 2025) — diffusion-based code LLM
- 100+ tokens/sec 병렬 생성
- 출처: arxiv.org/abs/2406.04329

### A4. Liquid Neural Networks
**정의**: 시간 변화하는 ODE 기반 NN. 적은 뉴런으로 적응적 학습.
- **MIT CSAIL** (Hasani et al.)
- 자율주행·로봇에 효율
- 출처: science.org/doi/10.1126/scirobotics.adh0102

### A5. RWKV / RetNet / Hyena
**정의**: Transformer attention 대체 후보들.
- **RWKV** — RNN + Transformer 하이브리드
- **RetNet** — retention mechanism
- **Hyena** — implicit convolution
- 출처: github.com/BlinkDL/RWKV-LM

### A6. Multi-Token Prediction (MTP)
**정의**: 다음 1 토큰 X, n 토큰 동시 예측. 학습 효율·추론 속도 ↑.
- Meta 2024, **Llama 4** 적용
- 출처: arxiv.org/abs/2404.19737

### A7. Flow Matching
**정의**: Diffusion 단순화. score function X, vector field 직접 학습.
- **Pi0** (Physical Intelligence) 로봇 모델 base
- 출처: arxiv.org/abs/2210.02747 (Lipman et al.)

### A8. Energy-Based Models (EBM)
**정의**: P(x) ∝ exp(-E(x)) — energy function 학습.
- Diffusion·score-based 의 이론적 base
- 출처: yann.lecun.com/exdb/publis/pdf/lecun-06.pdf

---

## B. AI 정렬·안전 (Alignment)

### B1. RLHF (Reinforcement Learning from Human Feedback)
**정의**: 인간 선호 데이터로 reward model → PPO 강화학습.
- InstructGPT (2022), GPT-4, Claude
- 단계: SFT → RM → PPO
- 출처: arxiv.org/abs/2203.02155

### B2. DPO (Direct Preference Optimization)
**정의**: RL 없이 preference pair 만으로 직접 학습. RLHF 비용 1/10.
- Rafailov et al. 2023 (Stanford)
- Bradley-Terry 모델 + KL 발산 closed-form
- 출처: arxiv.org/abs/2305.18290

### B3. KTO (Kahneman-Tversky Optimization)
**정의**: prospect theory (행동경제학) 기반. binary "좋다/나쁘다" 만 필요.
- Ethayarajh et al. 2024 (Contextual AI)
- 출처: arxiv.org/abs/2402.01306

### B4. IPO / ORPO / SimPO / SLiC
**정의**: DPO 변형들. 각각 다른 손실 함수·정규화.
- **ORPO** — odds ratio PO, SFT + 정렬 동시
- **SimPO** — reference model 불필요
- 출처: arxiv.org/abs/2403.07691

### B5. Constitutional AI (CAI)
**정의**: 헌법 (원칙) 박고 AI 가 자기 답 비판·수정. RLHF 대신 RLAIF.
- Anthropic, Bai et al. 2022
- Critique → Revise → Constitutional RL
- 출처: arxiv.org/abs/2212.08073

### B6. Process Reward Models (PRM)
**정의**: 최종 답 점수가 아닌 사고 **과정 step** 별로 점수.
- OpenAI 2023 (Lightman et al.)
- o1·o3 의 핵심
- 출처: arxiv.org/abs/2305.20050

### B7. Weak-to-Strong Generalization
**정의**: 약한 supervisor (작은 모델) 가 강한 학생 (큰 모델) 을 학습 — supervisor 한계 넘어서 일반화.
- OpenAI Superalignment 2023
- 출처: arxiv.org/abs/2312.09390

### B8. Eliciting Latent Knowledge (ELK)
**정의**: 모델 내부에 있는 "진짜 지식" 을 표면 답과 분리해 추출.
- ARC (Alignment Research Center)
- 출처: ai-alignment.com/2021/12/eliciting-latent-knowledge

### B9. Debate / AI Safety via Debate
**정의**: 두 AI 가 토론, 사람이 judge — 사람이 모르는 영역도 안전.
- OpenAI Irving et al. 2018
- 출처: arxiv.org/abs/1805.00899

### B10. Sleeper Agents / Backdoor
**정의**: 모델에 trigger 박아 특정 조건에서 악의적 행동.
- Anthropic 2024 — "재정렬 안 됨" 입증
- 출처: arxiv.org/abs/2401.05566

---

## C. AI 추론 가속·인프라

### C1. Speculative Decoding
**정의**: 작은 draft 모델이 빠르게 N 토큰 추정 → 큰 모델이 verify. 2-3x 가속.
- DeepMind, Leviathan et al. 2023
- 출처: arxiv.org/abs/2211.17192

### C2. FlashAttention 3
**정의**: GPU 메모리 위계 최적화 attention. H100에서 50%+ MFU.
- Dao et al. 2024
- 출처: arxiv.org/abs/2407.08608

### C3. PagedAttention / vLLM
**정의**: OS paging 처럼 KV cache 메모리 관리. throughput 2-4x ↑.
- UC Berkeley 2023
- 출처: arxiv.org/abs/2309.06180

### C4. Continuous Batching
**정의**: request 별 token-level batching. GPU 활용 ↑.
- 출처: github.com/huggingface/text-generation-inference

### C5. GPTQ / AWQ / GGUF (Quantization)
**정의**: 4-bit / 3-bit / 2-bit 양자화. 메모리 1/4 ~ 1/8.
- GPTQ (ICLR 2023), AWQ (MLSys 2024)
- 출처: arxiv.org/abs/2306.00978

### C6. Knowledge Distillation
**정의**: 큰 teacher → 작은 student 학습. soft logits 활용.
- Hinton et al. 2015
- DistilBERT, MiniLM, TinyLlama
- 출처: arxiv.org/abs/1503.02531

### C7. Pruning (Structured·Unstructured)
**정의**: 중요 안 한 weight 제거.
- SparseGPT, Wanda
- 출처: arxiv.org/abs/2306.11695

### C8. LoRA / QLoRA / DoRA
**정의**: Low-rank adapter 만 학습. 메모리 1%만.
- LoRA (Hu et al. 2021), QLoRA (4-bit + LoRA), DoRA
- 출처: arxiv.org/abs/2106.09685

### C9. ZeRO / FSDP / Tensor Parallelism
**정의**: 큰 모델 분산 학습.
- DeepSpeed ZeRO, PyTorch FSDP
- 출처: arxiv.org/abs/1910.02054

### C10. Megablocks / MoE Routing
**정의**: MoE 효율 GPU 커널.
- Stanford·Databricks
- 출처: arxiv.org/abs/2211.15841

---

## D. 멀티모달·생성

### D1. Any-to-Any Models
**정의**: 텍스트·이미지·영상·음성·코드 동시 입출력.
- **Gemini 2.5 Pro**, **GPT-4o**, **Chameleon** (Meta)
- 출처: arxiv.org/abs/2405.09818 (Chameleon)

### D2. Native Voice (음성 native)
**정의**: 텍스트 변환 없이 음성 → 모델 → 음성 직접.
- **GPT-4o Voice Mode**, **Hume EVI 3**, **Moshi**
- latency 200ms 이하
- 출처: arxiv.org/abs/2410.00037 (Moshi)

### D3. Native Image Generation
**정의**: 별도 diffusion X, LLM 이 직접 image token 생성.
- **GPT-Image-1**, **Gemini 2.5 image**, **Janus** (DeepSeek)
- 출처: arxiv.org/abs/2410.13848

### D4. Text-to-3D
**정의**: 텍스트 → 3D mesh / Gaussian splat.
- **Meshy**, **Tripo**, **Luma Genie**, **CLAY**
- DreamFusion·Magic3D 학술 base
- 출처: arxiv.org/abs/2209.14988

### D5. 3D Gaussian Splatting
**정의**: NeRF 대체. 100x 빠른 3D 재구성.
- Kerbl et al. SIGGRAPH 2023
- 출처: github.com/graphdeco-inria/gaussian-splatting

### D6. Diffusion Transformer (DiT)
**정의**: U-Net 대신 Transformer 로 diffusion. Sora·Stable Diffusion 3 의 base.
- Peebles & Xie 2023
- 출처: arxiv.org/abs/2212.09748

### D7. Tactile AI / Haptic
**정의**: 촉각 sensor 데이터 학습.
- Meta Digit, Tesla Optimus Skin
- 출처: digit.ml

### D8. Olfactory AI
**정의**: 냄새 분자 → 디지털화·생성.
- **Osmo** (Google spin-off)
- 출처: osmo.ai

### D9. Music Generation
**정의**: 가사·장르 → 완성된 음악.
- **Suno V4**, **Udio**, **MusicLM** (Google)
- 출처: arxiv.org/abs/2306.05284 (MusicLM)

### D10. Voice Cloning
**정의**: 몇 초 음성 → 완벽 복제.
- **ElevenLabs**, **PlayHT**, **Tortoise**
- 출처: elevenlabs.io/blog

---

## E. Agent 진화 (구체 시스템)

### E1. CodeAct
**정의**: Tool call X, Python code 자체를 action.
- Carnegie Mellon, Wang et al. 2024
- 출처: arxiv.org/abs/2402.01030

### E2. PaLM-E / RT-2 / Pi0
**정의**: VLM + 로봇 action token (앞서 다룸).

### E3. Voyager (NVIDIA)
**정의**: Minecraft 자율 탐험 LLM 에이전트. 평생 학습 skill library.
- 출처: arxiv.org/abs/2305.16291

### E4. MetaGPT
**정의**: 소프트웨어 개발팀 — PM·Architect·Engineer·QA AI 협업.
- 출처: arxiv.org/abs/2308.00352

### E5. ALOHA / Mobile ALOHA
**정의**: Stanford 양손 로봇. 50 시연으로 자율 작업.
- 출처: tonyzhaozh.github.io/aloha

### E6. RoboCat (DeepMind)
**정의**: Multi-task 로봇 foundation. self-improving.
- 출처: arxiv.org/abs/2306.11706

### E7. VoxPoser
**정의**: 자연어 → 3D voxel value map → 로봇 motion.
- Stanford
- 출처: voxposer.github.io

### E8. LeRobot (HuggingFace)
**정의**: 오픈 로봇 학습 플랫폼.
- 출처: github.com/huggingface/lerobot

---

## F. RAG·메모리 진화

### F1. HippoRAG
**정의**: 해마 (hippocampus) 영감 — Personalized PageRank on KG.
- Gutiérrez et al. 2024
- 출처: arxiv.org/abs/2405.14831

### F2. RAPTOR
**정의**: 재귀적 abstractive summary tree.
- Sarthi et al. ICLR 2024
- 출처: arxiv.org/abs/2401.18059

### F3. Corrective RAG (CRAG)
**정의**: 검색 결과 평가 → 부족하면 web search fallback.
- 출처: arxiv.org/abs/2401.15884

### F4. Adaptive RAG
**정의**: 질의 복잡도 분류기 → no-retrieval / single-step / multi-step.
- 출처: arxiv.org/abs/2403.14403

### F5. ColBERT v2 (Late Interaction)
**정의**: token-level multi-vector retrieval.
- Stanford
- 출처: arxiv.org/abs/2112.01488

### F6. BGE-M3 / Nomic Embed / Voyage AI
**정의**: 다국어·long context embedding 모델.
- BGE-M3 (BAAI), Nomic Atlas, Voyage-3
- 출처: huggingface.co/BAAI/bge-m3

### F7. Reranking (Cohere / Voyage)
**정의**: 검색 결과 cross-encoder 재정렬. 정확도 ↑.
- 출처: cohere.com/rerank

### F8. MemGPT / Letta
**정의**: OS-style 가상 메모리 — main context ↔ archival ↔ recall.
- Packer et al. 2023
- 출처: arxiv.org/abs/2310.08560

---

## G. AI 보안·공격

### G1. Indirect Prompt Injection
**정의**: 문서·이메일·웹에 숨긴 명령이 AI 행동 조작.
- OWASP LLM Top 10 #1
- 출처: arxiv.org/abs/2302.12173

### G2. Jailbreaking (DAN·Crescendo·MultiAttack)
**정의**: 안전 가드 우회 prompt.
- **Crescendo** (MS) — 점진적 정상→유해
- **PAIR** — 자동 jailbreak
- 출처: arxiv.org/abs/2310.08419 (PAIR)

### G3. Model Extraction / Stealing
**정의**: 질의-답 쌍으로 모델 복제.
- 출처: arxiv.org/abs/1609.02943

### G4. Data Poisoning
**정의**: 학습 데이터 일부 오염 → 모델 행동 변경.
- **Sleeper Agents** (Anthropic)

### G5. Membership Inference
**정의**: 특정 데이터가 학습 set 에 있었나 추론. 프라이버시 공격.
- 출처: arxiv.org/abs/1610.05820

### G6. Watermarking (KGW·Aaronson Hash)
**정의**: AI 생성 텍스트에 통계적 서명 박음.
- Kirchenbauer et al. 2023
- 출처: arxiv.org/abs/2301.10226

### G7. Confidential Computing 깊이
- **Intel SGX / TDX** — enclave
- **AMD SEV-SNP** — encrypted VM
- **NVIDIA H100 CC** — encrypted GPU memory
- **AWS Nitro Enclaves**

### G8. Fully Homomorphic Encryption (FHE) 깊이
- **CKKS** (실수), **BFV/BGV** (정수)
- 라이브러리: Microsoft SEAL, OpenFHE, Concrete
- 출처: github.com/microsoft/SEAL

### G9. Zero-Knowledge ML (zkML)
**정의**: 모델 가중치 공개 없이 추론 정확성 증명.
- Modulus Labs, EZKL, Giza
- 출처: ezkl.xyz

### G10. MPC (Secure Multi-Party)
- **SPDZ**, **ABY3**, **CrypTen** (Meta), **MP-SPDZ**
- 출처: github.com/data61/MP-SPDZ

---

## H. AI 거버넌스·평가

### H1. AI Risk Management Framework (NIST AI RMF)
- NIST 1.0 (2023) — Govern·Map·Measure·Manage
- 출처: nist.gov/itl/ai-risk-management-framework

### H2. EU AI Act 깊이
- 4 risk tier (Unacceptable·High·Limited·Minimal)
- 2025-02 발효 / 2026-08 GPAI / 2027-08 고위험 / 2030 전면
- 출처: artificialintelligenceact.eu

### H3. ISO 42001 (AI 관리시스템)
- 2024 발행, ISO 27001 형식
- 출처: iso.org/standard/81230.html

### H4. Model Cards / Datasheets
- Mitchell et al. 2019 (Google)
- 출처: arxiv.org/abs/1810.03993

### H5. HELM (Stanford 평가)
- 전체적 평가 benchmark
- 출처: crfm.stanford.edu/helm

### H6. MMLU / MMLU-Pro / GPQA
- 학술 추론 평가
- 출처: arxiv.org/abs/2009.03300

### H7. SWE-Bench / SWE-Bench Verified
- 소프트웨어 엔지니어링 평가
- Princeton
- 출처: swebench.com

### H8. Chatbot Arena (LMSYS)
- 인간 선호 ELO ranking
- 출처: chat.lmsys.org

---

## I. 도메인 AI

### I1. AlphaFold 3 / Boltz-1 / ESM 3
- 단백질·DNA·RNA 통합 예측
- Boltz-1 (MIT) — 오픈소스
- 출처: deepmind.google/discover/blog/alphafold-3

### I2. MatterGen / GNoME
- 신소재 생성 AI
- DeepMind GNoME: 220만 신물질
- 출처: deepmind.google/discover/blog/millions-of-new-materials-discovered-with-deep-learning

### I3. GraphCast / Pangu-Weather
- 기상 예측 AI (NWP 대체 수준)
- DeepMind·Huawei
- 출처: arxiv.org/abs/2212.12794

### I4. AlphaProof / AlphaGeometry 2
- 수학 올림피아드 풀이 AI (IMO 은메달)
- DeepMind 2024
- 출처: deepmind.google/discover/blog/ai-solves-imo-problems

### I5. Med-PaLM 2 / Glass / Hippocratic
- 의료 LLM (USMLE 90+)
- 출처: sites.research.google/med-palm

### I6. Harvey / CoCounsel / Spellbook
- 법무 LLM (계약·판례)
- 출처: harvey.ai

### I7. BloombergGPT / FinGPT
- 금융 도메인 LLM
- 출처: arxiv.org/abs/2303.17564

### I8. ESM Cambrian / ProtT5
- 단백질 언어 모델
- 출처: github.com/facebookresearch/esm

---

## J. AI 하드웨어

### J1. NVIDIA Blackwell (B200·GB200)
- 192GB HBM3e, 4nm, FP4 native
- GB200 NVL72 — 72 GPU rack
- 출처: nvidia.com/en-us/data-center/blackwell-architecture

### J2. Google TPU v6 (Trillium)
- 4.7x v5e 성능
- 출처: cloud.google.com/blog/products/compute/introducing-trillium-6th-gen-tpus

### J3. AMD MI300X / MI325X
- 192GB HBM3, ROCm
- 출처: amd.com/en/products/accelerators/instinct/mi300

### J4. Cerebras WSE-3
- wafer-scale chip — 4조 트랜지스터, 900K core
- 출처: cerebras.net

### J5. Groq LPU
- LLM 추론 ASIC. 500+ tokens/sec
- 출처: groq.com

### J6. Etched Sohu
- Transformer ASIC. 단일 모델 hardcoded → 20x 빠름
- 출처: etched.com

### J7. Photonic Computing
- **Lightmatter Passage** — 광 + 디지털
- **Lightelligence** — photonic AI
- 출처: lightmatter.co

### J8. Neuromorphic — Intel Loihi 3
- 스파이킹 NN, 100x 저전력
- 출처: intel.com/content/www/us/en/research/neuromorphic-computing.html

### J9. Quantum (Heron·Willow·Majorana 1)
- IBM Heron 156q, Google Willow 105q (error correction!), MS Majorana 1 (topological)
- 출처: research.ibm.com/blog/heron-quantum-processor

### J10. D-Wave Advantage 2 (Quantum Annealing)
- 7000+ qubit, 최적화 특화 (vs gate-based)
- 출처: dwavesys.com

---

## K. 신경과학·BCI

### K1. Neuralink Telepathy
- 1024 electrode, fully implantable
- 출처: neuralink.com

### K2. Synchron Stentrode
- 혈관 통한 BCI (개두 수술 X)
- 출처: synchron.com

### K3. Precision Neuroscience (Layer 7)
- 1024+ electrode flexible array
- 출처: precisionneuro.io

### K4. Paradromics
- high-bandwidth implantable
- 출처: paradromics.com

### K5. Meta CTRL-Labs
- EMG wristband (비침습)
- 출처: tech.fb.com/ar-vr/2021/03/inside-facebook-reality-labs-wrist-based-interaction

### K6. fMRI → Speech (Tang et al.)
- 뇌 fMRI → 자연어 디코딩 (UT Austin)
- 출처: nature.com/articles/s41593-023-01304-9

### K7. Project CETI
- 향유고래 언어 디코딩 (AI + 해양생물학)
- 출처: projectceti.org

---

## L. AI Math·Theory

### L1. Scaling Laws (Kaplan·Chinchilla)
- N (parameters), D (data), C (compute) 의 power law
- Chinchilla: D = 20·N optimal
- 출처: arxiv.org/abs/2203.15556

### L2. Grokking
- 학습 plateau 후 갑작스런 generalization
- 출처: arxiv.org/abs/2201.02177

### L3. Lottery Ticket Hypothesis
- 큰 NN 안에 학습된 small subnetwork ("winning ticket")
- 출처: arxiv.org/abs/1803.03635

### L4. Neural Tangent Kernel (NTK)
- 무한 width NN = kernel method
- 출처: arxiv.org/abs/1806.07572

### L5. Phase Transitions
- 학습 중 갑작스런 능력 출현
- 출처: arxiv.org/abs/2202.02061

### L6. Mechanistic Interpretability (앞서 다룸)

### L7. Universality Hypothesis
- 다른 NN 들도 비슷한 회로 학습
- 출처: distill.pub/2020/circuits/zoom-in

---

##  종합 — 총 70+ 추가 기술

| 카테고리 | 개수 |
|---|---|
| A. LLM 핵심 진화 | 8 |
| B. AI 정렬·안전 | 10 |
| C. 추론 가속·인프라 | 10 |
| D. 멀티모달·생성 | 10 |
| E. Agent 시스템 | 8 |
| F. RAG·메모리 | 8 |
| G. AI 보안·공격 | 10 |
| H. 거버넌스·평가 | 8 |
| I. 도메인 AI | 8 |
| J. AI 하드웨어 | 10 |
| K. BCI·신경 | 7 |
| L. 이론·수학 | 7 |
| **합계** | **104+** |

→ 기존 10 + 추가 104+ = **114+ 신기술 cover**.

---

## 사용자 학습 추천 순서

### Week 1-2: LLM 핵심
A1·A2·B1·B2·C8 — MoE·Mamba·RLHF·DPO·LoRA

### Week 3-4: Agent·RAG
E1·E3·F1·F2·F8 — CodeAct·Voyager·HippoRAG·RAPTOR·MemGPT

### Week 5-6: 멀티모달·피지컬
D1·D3·D6·VLA·World Models (이미 다룸)

### Week 7-8: 안전·정렬
B5·B6·B7·G1·G2 — Constitutional·PRM·Weak-to-Strong·Prompt Injection·Jailbreak

### Week 9-12: 깊이
- Mech Interp (Anthropic)
- Quantum ML 실습
- Causal AI 실습
- 도메인 (AlphaFold·MatterGen)

어떤 카테고리 / 기술 더 깊이?

---

## 다음 가능 — 본인이 더 발굴 가능한 영역

- **Bioengineering AI** (Ginkgo, Inceptive)
- **Robotics Foundation Datasets** (Open X-Embodiment)
- **AI for Mathematics** (FunSearch, AlphaEvolve)
- **Continual Learning** (catastrophic forgetting)
- **Active Learning**
- **Meta-Learning** (MAML 등)
- **Multi-Agent RL** (MARL)
- **Inverse Reinforcement Learning**
- **Imitation Learning** (행동 복제)
- **Self-Supervised Learning** (MAE·SimCLR·DINO)
- **Contrastive Learning**
- **Curriculum Learning**
- **Synthetic Speech** (보안 측면)
- **AI in Education** (Khan Academy Khanmigo)
- **AI in Climate** (ClimateBERT, ClimateGAN)
- **AI in Material Science** (MatBERT, MatSciBERT)
- **AI Drug Repurposing**
- **AI in Particle Physics** (CERN)
- **AI in Astronomy** (BERT-Galaxy)
- **AI in Linguistics** (low-resource MT)

→ 추가 20+ 영역 더 발굴 가능. 어디 더 파볼까?

---

## 델타 (2026-08-19 · 확장 8건 추가)

- **Qwen 3.8-27B** (Alibaba · 2026-08-14) — Apache 2.0 오픈 프론티어 · 262K context · SWE-bench Pro 61.7% (>Opus 4.6 Max)
- **Anthropic Model 2** (2026-08-14 disclosed) — 내부 Mythos 5 초과 · 외부 release X · RSP v3.4 근거
- **Managed Agents 4종** — session budget · advisor tool · inference geo pin · GitHub-hosted skills
- **Inference hooks** (Enterprise beta · 8/5) — 조직 AI security server · governed prompt allow/deny
- **Workbench → Playground** (8/18) — Console UI 개편 · all Messages API param + code exec·web search 데모
- **Claude Code v2.1.235** (8/18) — Inline spellcheck · prompt-cache LSP fix · Markdown depth 3+
- **Anthropic Risk Report v2** (RSP v3.4 · 8/14) — misalignment low 상향
- **Sonnet 5 $2/$10 확정** (8/10) — 9/1 인상 취소

**관련 memory**: [[ai-tech-2026-08-late]] · [[claude-code-changelog-august]]
