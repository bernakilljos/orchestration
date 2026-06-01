# 20개 AI 신기술 깊이 + AI Risk Lighthouse 시스템 설계

> **목적**: 부서·ITCEN CORE 시너지 큰 20개 기술 깊이 + Lighthouse 자율 검증 시스템 본인 (Claude Code) 자체 구현
> **원본**: `ai-tech-catalog-50.md` / `ai-tech-applications-100.md`
> **작성**: 2026-06-01

---

## 🎯 깊이 들어갈 20개 기술 (시너지·임팩트 순)

| # | 기술 | 핵심 / 아키텍처 | 부서·ITCEN 접목 | 한국 진입자 |
|---|---|---|---|---|
| 1 | **Self-Critique / Reflexion** | LLM 답 → critique LLM → 재시도 (최대 3회) → 합의 | UEBA 점수 2단계 검증 = 부서 IP | 거의 없음 ⭐⭐⭐ |
| 2 | **Causal AI** | Pearl 인과 그래프·do-calculus·DoWhy | 행동위험 인과 추론·사고 원인 분석 | 거의 없음 ⭐⭐⭐ |
| 3 | **GraphRAG** | Knowledge Graph 추출 → community detection → LLM 답 | 행동패턴 그래프·내부 자금 흐름 | 거의 없음 ⭐⭐⭐ |
| 4 | **Agentic AI** | Plan-Act-Reflect 루프·MCP 도구 호출·메모리 | 24/7 자율 Risk Officer | 추격 중 |
| 5 | **Multi-Agent Systems** | CrewAI·AutoGen·LangGraph 협업·토론·합의 | 위험점수 다중 AI 합의 | 추격 중 |
| 6 | **World Models** | 영상 → 물리법칙 학습 (Cosmos·Sora·V-JEPA) | 디지털트윈 자동 학습·사고 시뮬 | 거의 없음 |
| 7 | **Vision-Language-Action (VLA)** | 비전 + 언어 + 행동 통합 foundation | 작업자·딜러 의도 추론 | 거의 없음 |
| 8 | **Reasoning Models (o3·R1)** | Chain-of-Thought 학습·test-time compute | 고위험 사건 깊은 추론 | 추격 중 |
| 9 | **Neurosymbolic AI** | LLM + 기호 룰 + 인과 통합 | 법규 룰 + LLM 융합 GRC | 학계만 |
| 10 | **Affective Computing** | 얼굴·음성·생체 → 감정 분류 | 카지노 딜러·금융 직원 스트레스 | 거의 없음 |
| 11 | **Mechanistic Interpretability** | AI 회로 분해 (Anthropic·Goodfire) | EU AI Act 설명가능성 의무 | 거의 없음 |
| 12 | **Behavioral Biometrics** | 타이핑·마우스·걸음 → 상시 인증 | VMS·금융 차세대 인증 | BioCatch 일부 |
| 13 | **Federated Learning** | 데이터 안 모으고 모델만 학습 | 컨소시엄 부정탐지·금융 협력 | 추격 중 |
| 14 | **Confidential Computing** | NVIDIA H100 CC·Intel SGX → 메모리 암호화 | AI 모델 격리·고객 데이터 분석 | 추격 중 |
| 15 | **Synthetic Data Generation** | LLM·diffusion 으로 합성 학습데이터 생성 | 행동AI 학습데이터 무한 생성 | 거의 없음 |
| 16 | **Memory Architectures (MemGPT·Letta)** | OS-style 가상메모리·일화·의미 메모리 | 직원·고객 행동 영구 학습 | 학계 |
| 17 | **Constitutional AI** | 헌법(원칙) 박고 AI 가 자기 규제 | 부서 SOP·법규 헌법화 | Anthropic 만 |
| 18 | **Quantum ML (QML)** | Variational Quantum Circuit + 고전 학습 | 금융 부정거래 양자최적화 | KAIST·KISTI |
| 19 | **Deepfake Detection / C2PA** | 음성·영상 위조 탐지·콘텐츠 출처 표준 | 보이스피싱법 2026 의무 | 추격 중 |
| 20 | **AI Risk Lighthouse** ⭐ | 회사 AI·내부통제·행동위험 자동 감사·점수 | **부서가 만들 한국 표준** | **없음** ⭐⭐⭐ |

---

## 📐 각 기술 깊이

### 1. Self-Critique / Reflexion (★★★ 부서 즉시 도입)

**원리**:
- 1차 LLM 이 답 생성 → 2차 LLM (critique role) 이 비판 → 1차 LLM 이 수정 → N회 반복 → 합의
- Reflexion (Yao et al.) / Self-RAG / Constitutional AI / Multi-Agent Debate 등 변형

**아키텍처**:
```text
사용자 질의 → Actor LLM (1차 답)
                ↓
          Critic LLM (비판·점수)
                ↓
      점수 < 임계 → Actor 재시도 (피드백 반영)
      점수 ≥ 임계 → 합의 답 반환
```

**구현 예제 (Python pseudo)**:
```python
def reflexion_loop(query, max_iter=3, threshold=0.8):
    actor_prompt = f"질의: {query}\n답하세요."
    for i in range(max_iter):
        answer = llm(actor_prompt)
        critique = llm(f"답: {answer}\n비판하세요. 점수 0-1.")
        score = parse_score(critique)
        if score >= threshold:
            return answer, score
        actor_prompt = f"{actor_prompt}\n이전 답: {answer}\n비판: {critique}\n수정하세요."
    return answer, score
```

**ITCEN CORE 부서 접목**:
- 행동위험 점수 1차 (UEBA 모델) → 2차 LLM 이 "왜 이 점수인지" 비판 → 합의점수
- 알람 정확도 ↑ (거짓양성 50% 감소 기대)
- 부서 핵심 차별화 IP

**우리 솔루션 적용 사례** (orchestration_v1):
- `.claude/hooks/verify-subagent-confidence.sh` — 서브에이전트 답 confidence 검증
- `.claude/skills/haiku-validator.md` — Haiku 가 Sonnet/Opus 답 재검토
- `plugins/exec_orch/hooks/post-codex-verify.sh` — Codex 환각 자동 검출

---

### 2. Causal AI (★★★ 행동위험 인과)

**원리**:
- 상관관계 ≠ 인과관계. 인과는 개입 (do-calculus) 으로만 식별 가능
- Pearl 의 Causal Hierarchy: ① 관찰 (P(Y|X)) ② 개입 (P(Y|do(X))) ③ 반사실 (P(Y_x'|X=x, Y=y))

**아키텍처**:
```bash
관측 데이터 + 도메인 지식 → 인과 그래프 (DAG)
                              ↓
                       do-calculus 식별
                              ↓
                   인과 효과 추정 (회귀·매칭·IV)
                              ↓
                   "원인 X 가 Y 에 얼마나 기여"
```

**도구**:
- **DoWhy** (Microsoft) — Python, 4단계 (modeling·identification·estimation·refutation)
- **Causica** (Microsoft) — Deep Learning 기반
- **EconML** — 계량경제 인과
- **CausalML** (Uber) — uplift 모델링

**ITCEN CORE 부서 접목**:
- 부정거래의 진짜 원인 (단순 패턴 매칭 X)
- 중대재해 인과 추적 (어떤 요인이 사고를 일으켰나)
- 이직·횡령의 선행 행동 인과 추론

**Lighthouse 활용**: AI Risk Lighthouse 가 "왜 위험점수가 높은가" 인과적 설명 제공.

---

### 3. GraphRAG (★★★ 행동패턴 그래프)

**원리**:
- Vector RAG 단점: 텍스트 청크 간 관계 모름 → 다단계 추론 약함
- GraphRAG: LLM 으로 entity·relation 추출 → Knowledge Graph 구축 → community detection → 질의 시 graph traversal

**Microsoft GraphRAG 아키텍처**:
```text
원문 → LLM 추출 → entity·relation
                      ↓
              Knowledge Graph
                      ↓
        Community detection (Leiden 알고리즘)
                      ↓
            Community summary (LLM)
                      ↓
         질의 → graph traversal + summary → LLM 답
```

**ITCEN CORE 부서 접목**:
- **행동패턴 그래프**: 직원 ↔ 거래 ↔ 결재 ↔ 출입 ↔ 시간 노드·엣지
- 부정 패턴 = graph cycle / community
- 자금세탁 = 다중 hop 거래 그래프
- 카지노 부정 = 딜러·플레이어·테이블 관계 그래프

---

### 4. Agentic AI

**원리**: Plan-Act-Reflect 루프
```text
사용자 목표 → LLM (Plan) → 도구 호출 (Act) → 결과 관찰 → LLM (Reflect) → 다음 단계
                                                              ↓
                                                       목표 달성? → 끝
```

**핵심 기술**:
- **MCP (Anthropic 표준)** — 외부 도구 호출 표준
- **Computer-Use** (Claude) — 화면 픽셀 보고 클릭
- **Browser-Use** — 웹 자율 탐색
- **Memory** — 장기 작업 컨텍스트

**ITCEN CORE 접목**:
- 24/7 Risk Officer Agent (자율 점검·보고)
- 내부회계 자율 감사 (분식·횡령 24/7)
- 컴플라이언스 자율 모니터링

---

### 5. Multi-Agent Systems

**원리**: 여러 AI 가 역할 분담·협업·토론
- **CrewAI** — 역할 기반 (Researcher, Writer, Critic)
- **AutoGen** (Microsoft) — 대화형 협업
- **LangGraph** — 상태 기반 워크플로우

**합의 메커니즘**:
- Majority voting (다수결)
- Weighted by confidence
- Debate → judge

**ITCEN CORE**:
- 위험점수 = UEBA + 회계 + VMS + GRC 4 에이전트 합의
- 카지노 부정 = 게임·자금·CCTV·딜러 4 관점 토론

---

### 6. World Models (NVIDIA Physical AI 핵심)

**원리**: 영상에서 물리법칙·인과·예측 학습
- **NVIDIA Cosmos** — 비디오 토큰화 + 디퓨전 / 자동회귀 양면
- **OpenAI Sora** — 텍스트→영상 + 물리 시뮬
- **Google Genie** — 액션 → 게임 환경
- **Meta V-JEPA** — 영상 self-supervised

**활용**: 디지털트윈 학습데이터 무한 생성 → 행동 패턴 시뮬

**ITCEN CORE**:
- 디지털트윈 + Cosmos = 공장·건설현장 사고 시뮬레이션
- 부정행위 시나리오 무한 생성 (학습 데이터)

---

### 7. Vision-Language-Action (VLA)

**원리**: 비전 + 언어 + 행동 통합 모델 (보고 듣고 행동)
- RT-2 (Google) / Pi0 (Physical Intelligence) / OpenVLA / NVIDIA GR00T

**ITCEN CORE**:
- AI CCTV → 행동 보고 → 자연어 보고서 자동 생성
- 카지노 딜러 의도·이상행동 추론
- 작업자 PPE 미착용 + 자율 알람

---

### 8. Reasoning Models (o3·R1·Extended Thinking)

**원리**: 추론 시간 길게 = 정답률 ↑
- Test-time compute scaling: 같은 모델이 더 오래 생각 = 성능 ↑
- o3 (OpenAI) / DeepSeek R1 (오픈소스) / Claude Extended Thinking

**부서**: 고위험 사건 = 시간 들여 깊이 추론. 일반 사건 = 빠르게.

---

### 9. Neurosymbolic AI

**원리**: LLM (직관) + 기호 룰 (정확) + 인과 그래프 (구조) 융합
- LLM 단점: 환각·룰 위반·일관성 부족
- 기호 룰 단점: 새 상황 약함
- 결합 = 각자 강점 + 약점 보완

**부서**: 한국 금감원·EU AI Act 규제 룰 + LLM 직관 = 차세대 GRC

---

### 10. Affective Computing

**원리**: 멀티모달 (얼굴·음성·생체) → 감정 분류
- Affectiva·Hume·Realeyes 글로벌 OEM
- 한국 시장 거의 없음

**ITCEN CORE**:
- 카지노 딜러 스트레스 사전 감지 → 부정행위 예방
- 금융 직원 행동위험 + 감정 = 차원 확장
- 카지노 플레이어 도박중독 조기경보

---

### 11. Mechanistic Interpretability

**원리**: AI 내부 회로 (attention head·MLP) 분해·해석
- Anthropic 핵심 연구 (2024-2026)
- Goodfire AI (해석 SaaS)

**ITCEN CORE**:
- EU AI Act 2027 의무: 고위험 AI 결정 설명 가능
- 부서 위험점수 = 왜 그런가 자동 설명
- 규제 보고 자동화

---

### 12. Behavioral Biometrics

**원리**: 타이핑 리듬·마우스 움직임·걸음걸이로 상시 인증
- BioCatch·Nuance·Mastercard
- "한 번 로그인 X, 세션 내 상시 검증"

**ITCEN CORE**:
- VMS·금융 차세대 인증
- 내부자위협 = 사용자 행동 변화 탐지
- 부서 행동분석의 자연 확장

---

### 13. Federated Learning

**원리**: 각 고객사 데이터를 자기 서버에 두고 모델 weight 만 공유 → 중앙에서 합산 학습
- NVIDIA FLARE / Flower / Owkin (의료)

**ITCEN CORE**:
- 금융권 컨소시엄 부정탐지 (은행 간 거래 데이터 공유 X)
- 부서 행동AI = 여러 고객사 데이터 안 모으고 학습
- 개인정보 의무 100% 충족

---

### 14. Confidential Computing

**원리**: CPU/GPU 가 메모리 사용 중에도 암호화 (Intel SGX·AMD SEV·NVIDIA H100 CC)

**ITCEN CORE**:
- 고객 데이터 분석 시 격리 (분석자도 데이터 못 봄)
- AI 모델 격리 실행 (모델 도용 방어)
- 금감원·국정원 의무 추세

---

### 15. Synthetic Data Generation

**원리**: LLM·diffusion 으로 학습데이터 합성. 통계적 동등 + 개인정보 0
- Gretel / Mostly AI / Tonic

**ITCEN CORE**:
- 행동AI 학습데이터 무한 생성
- 개인정보 가명·익명 법 의무 100% 충족
- 부족한 부정 사례 = 합성으로 채움

---

### 16. Memory Architectures (MemGPT·Letta)

**원리**: AI 가 OS-style 가상 메모리 운영
- Short-term (context window) ↔ Long-term (vector DB) ↔ Working memory
- 영구 학습·일화 기억·의미 기억

**ITCEN CORE**:
- AI Risk Officer 가 1년치 행동 영구 학습
- 직원·고객별 행동 히스토리 누적
- 같은 위험 패턴 재발견 시 즉시 알람

---

### 17. Constitutional AI (Anthropic)

**원리**: AI 가 따라야 할 헌법 (원칙) 박고 AI 가 자기 답을 헌법에 비교 → 위반 시 수정
- RLHF 대체·보완

**ITCEN CORE**:
- 부서 SOP·법규 = AI 헌법
- 모든 위험점수가 SOP·법규 준수 자동 검증
- 컴플라이언스 자동화

---

### 18. Quantum ML (QML)

**원리**: 양자컴퓨터 (또는 시뮬레이터) 로 ML 학습
- Variational Quantum Circuit (VQC) = 양자-고전 하이브리드
- Quantum Kernel Methods

**ITCEN CORE**:
- IBM Quantum Network 무료 가입
- 금융 부정거래 양자최적화 (대량 거래 패턴)
- 한국 양자 시대 선점

---

### 19. Deepfake Detection / C2PA

**원리**:
- Deepfake: GAN·diffusion 생성 미디어 탐지 (Reality Defender·Hive·Pindrop)
- C2PA: 콘텐츠 출처 표준 (Adobe·Microsoft·BBC·NYT)

**ITCEN CORE**:
- 보이스피싱법 2026 의무
- 금융권 통화·영상 위조 탐지
- 회계·법무 문서 출처 검증

---

### 20. 🌟 AI Risk Lighthouse (부서가 만들 한국 표준)

**컨셉**:
- Google Lighthouse 가 웹페이지 점수 매기듯 (성능·접근성·SEO)
- **AI Risk Lighthouse** = 회사 AI 시스템·내부통제·행동위험을 자동 감사·점수 매김
- ITCEN CORE 가 한국 표준 만들면 = 모든 한국 기업 의무 도입 잠재

**검증 항목 (Lighthouse audit categories)**:
| 카테고리 | 검사 항목 |
|---|---|
| **Self-Critique** | AI 결정에 2단계 검증 있는가? confidence 점수 공개? |
| **Causal AI** | 위험점수에 인과 설명 있는가? 단순 상관관계만? |
| **Behavioral Coverage** | UEBA·VMS·CCTV 데이터 통합? 단일 source? |
| **Interpretability** | AI 결정 설명 가능? (EU AI Act 의무) |
| **Privacy (PET)** | Federated·Confidential·동형암호 적용? |
| **Compliance** | 한국 법규·EU AI Act 자동 추적? |
| **Quality** | 거짓양성·거짓음성 자동 모니터링? |
| **Self-Improvement** | 실패 사례 학습·반복 방지? |

**점수 산정 (0-100)**:
- 8 카테고리 × 가중치 → 종합 점수
- 100 = 한국 최고 수준
- 60- = 컴플라이언스 위반 위험

**부서가 만들 수 있는 자산**:
- 한국 표준 lobby (KISA·금감원 협력)
- 점수 IP 영구 보유
- 모든 한국 기업이 매년 검증 의무 (정기 매출)
- 컨설팅 + 인증 사업

---

## 🛡️ Lighthouse 본인 (Claude Code) 자체 구현 — orchestration_v1 자산 활용

`orchestration_v1` 의 rule·hook·skill 을 묶어 **Claude Code 가 자기 작업 자율 검증·재시도** 하는 Lighthouse-style 시스템.

### 활용 자산 매핑

| Lighthouse 카테고리 | 우리 자산 | 활용 |
|---|---|---|
| **Self-Critique** | `verify-subagent-confidence.sh` hook + `haiku-validator.md` | 본인 답 → Haiku 재검토 |
| **Causal 추론** | `auto-planner.md` 5단계 (전수·분석·실행·확인·보고) | 행동에 이유 명시 |
| **Coverage** | `failure-mode.md` Evidence·Coverage·Recency 3차원 | 전수조사 의무 |
| **Interpretability** | `auto-planner.md` 의 "보고" 단계 | 결정 근거 항상 명시 |
| **Privacy** | `approval-gate.py` | 위험 명령 사전 승인 |
| **Compliance** | `.claude/rules/*.md` 11개 룰 | 자동 강제 |
| **Quality** | `verify-image-fit.py`·`verify-docx-visual.py`·`verify-render-coverage.py` | 산출물 자동 검증 |
| **Self-Improvement** | `learn.md` skill + memory 시스템 | 실패 패턴 영구 기록 |

### 통합 시스템 설계

```text
사용자 요청
    ↓
[1] auto-planner skill 자동 활성 (5단계 plan)
    ↓
[2] 작업 시작 — 매 단계마다 confidence 평가
    ↓
[3] PreToolUse hook (approval-gate) — 위험 명령 차단
    ↓
[4] 작업 실행
    ↓
[5] PostToolUse hook (verify-*.py) — 산출물 자동 검증
    ↓
[6] FAIL → 자동 재시도 (max 3) → 여전히 FAIL → 사용자 보고
    ↓
[7] PASS → haiku-validator 가 최종 답 critique
    ↓
[8] 종합 점수 (Lighthouse-style) 보고
    ↓
[9] learn skill → 실패 패턴·성공 패턴 영구 기록
```

### 새로 추가할 hook·skill (점진 구현)

| 신규 자산 | 역할 |
|---|---|
| `claude-self-critique.sh` (PostToolUse hook) | 본인 응답 직후 자기 답 점수화 |
| `lighthouse-audit.md` (skill) | 매 응답 끝에 8 카테고리 점수 표 출력 |
| `agentic-loop.md` (skill) | 본인이 자기 작업 자율 반복 (max 3 turn) |
| `causal-explanation.md` (skill) | 모든 결정에 인과 설명 의무 |

### 기대 효과

- 사용자가 짚어주지 않아도 본인이 끝까지 자율 진행
- 매 응답 끝에 자기 작업 점수 (Self-Critique 결과)
- 점수 낮으면 자동 재시도
- "농땡이 안 피움" 체질화

---

## 부서가 만들 K-Lighthouse 표준 사업화

1. **2026-Q4**: 부서가 Lighthouse 8 카테고리 + 점수 모델 IP 확보
2. **2027-Q1**: ITCEN CORE 내부회계·GRC 고객 1차 베타 (100社)
3. **2027-Q2**: KISA·금감원·개인정보위 표준 lobby
4. **2027-Q3**: 한국 K-AI Risk Lighthouse 공식 표준 등록
5. **2028+**: 모든 한국 대기업 의무 도입 (5000社 × 1억 = 5천억)
6. **2029+**: 글로벌 수출 (K-Standard → 동남아·중동)

---

## 참고

- 50 기술: `ai-tech-catalog-50.md`
- 100 접목: `ai-tech-applications-100.md`
- 우리 솔루션: `.claude/rules/`, `plugins/exec_orch/skills/`, `.claude/hooks/`
- 작성일: 2026-06-01
