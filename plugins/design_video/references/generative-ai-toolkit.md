# Generative AI Toolkit — 생성형 AI 전체 카탈로그

> **목적**: 텍스트·이미지·영상·3D·아바타·음악 — AI 생성 도구 총정리

---

## 1. 영상 생성 (Text/Image → Video)

| 도구 | 특장 | 접근 | 비용 |
|------|------|------|------|
| **Runway Gen-3 Alpha** | 텍스트/이미지→영상, 모션 브러시 | runwayml.com | 유료 ($15/mo~) |
| **Pika** | 텍스트→영상, 이미지 애니메이트 | pika.art | 무료 티어 |
| **Kling** | 중국 AI 영상 (고품질, 긴 영상) | klingai.com | 무료 티어 |
| **Luma Dream Machine** | 텍스트/이미지→영상 | lumalabs.ai | 무료 티어 |
| **Stable Video Diffusion** | 로컬 실행 가능 | github | 무료 (GPU 필요) |
| **CogVideo/CogVideoX** | 오픈소스 (Tsinghua) | github | 무료 |
| **AnimateDiff** | Stable Diffusion + 모션 | github | 무료 |
| **ModelScope** | 텍스트→영상 (오픈소스) | github | 무료 |

```python
# Stable Video Diffusion (로컬)
pip install diffusers transformers accelerate
from diffusers import StableVideoDiffusionPipeline
pipe = StableVideoDiffusionPipeline.from_pretrained("stabilityai/stable-video-diffusion-img2vid-xt")
frames = pipe(image, num_frames=25).frames[0]
```

---

## 2. 이미지 생성 고급 (ControlNet / IP-Adapter / InstantID)

### Stable Diffusion 생태계
```bash
pip install diffusers         # Hugging Face Diffusers
pip install compel            # 프롬프트 가중치
pip install controlnet-aux    # ControlNet 전처리기
pip install ip-adapter        # 스타일/참조 이미지 제어
```

| 기법 | 용도 | 설치 |
|------|------|------|
| **ControlNet** | 포즈/엣지/깊이 제어 이미지 생성 | diffusers 내장 |
| **IP-Adapter** | 참조 이미지 스타일 전이 | github |
| **InstantID** | 1장 사진→다양한 포즈/스타일 | github |
| **PhotoMaker** | 얼굴 ID 유지 다양한 이미지 | github |
| **IC-Light** | 조명 변경 (재조명) | github |
| **FaceChain** | 디지털 분신 생성 | github |
| **Segment Anything (SAM 2)** | 클릭→세그멘테이션 (영상도) | pip install segment-anything-2 |

### 이미지 생성 서비스
| 서비스 | 특장 | 비용 |
|--------|------|------|
| **Midjourney** | 최고 품질 아트 | $10/mo~ |
| **DALL-E 3** | OpenAI, 텍스트 이해력 최강 | API 과금 |
| **Ideogram** | 텍스트 렌더링 최강 | 무료 티어 |
| **Flux** | Black Forest Labs, 빠른 고품질 | 무료/API |
| **Leonardo.ai** | 게임 에셋 특화 | 무료 티어 |
| **Scenario.gg** | 게임 에셋 AI (일관된 스타일) | 무료 티어 |

---

## 3. 3D 생성 (Text/Image → 3D Model)

| 도구 | 입력 | 출력 | 설치 |
|------|------|------|------|
| **TripoSR** | 1장 이미지 | 3D 메쉬 (.obj) | github (StabilityAI) |
| **InstantMesh** | 1장 이미지 | 3D 메쉬 | github |
| **Wonder3D** | 1장 이미지 | 멀티뷰 + 3D | github |
| **Zero123++** | 1장 이미지 | 멀티뷰 이미지 | github |
| **Shap-E** | 텍스트/이미지 | 3D (OpenAI) | pip install shap-e |
| **Point-E** | 텍스트 | 포인트 클라우드 | pip install point-e |
| **DreamGaussian** | 텍스트/이미지 | 3D Gaussian Splatting | github |
| **Meshy** | 텍스트/이미지 | 3D 게임 에셋 | meshy.ai (무료 티어) |
| **Luma Genie** | 텍스트 | 3D 모델 | lumalabs.ai |
| **Rodin Gen-1** | 텍스트/이미지 | 3D 캐릭터 | hyper.ai |

```python
# TripoSR (1장 → 3D)
pip install tsr
from tsr.system import TSR
model = TSR.from_pretrained("stabilityai/TripoSR")
mesh = model.run_image("character.png")
mesh.export("character.obj")
```

### 3D 뷰어 (웹)
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/examples/js/loaders/GLTFLoader.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js"></script>
```

---

## 4. 디지털 휴먼 / Talking Head (사진 → 말하는 아바타)

| 도구 | 특장 | 접근 | 비용 |
|------|------|------|------|
| **HeyGen** | 아바타 영상 생성 (100+ 아바타) | heygen.com | 유료 ($24/mo~) |
| **D-ID** | 사진→말하는 얼굴 | d-id.com | 무료 티어 |
| **SadTalker** | 사진+오디오→말하는 얼굴 (로컬) | github | 무료 |
| **MuseTalk** | 실시간 립싱크 (로컬) | github | 무료 |
| **Wav2Lip** | 오디오→립싱크 (비디오에 적용) | github | 무료 |
| **LivePortrait** | 사진→표정 전이 (실시간) | github | 무료 |
| **EMO** | Alibaba 감정 아바타 | github | 무료 |
| **AniPortrait** | 오디오→애니메이션 초상화 | github | 무료 |

```python
# SadTalker (로컬 — 사진+음성 → 영상)
python inference.py \
  --driven_audio audio.wav \
  --source_image face.jpg \
  --result_dir results/ \
  --enhancer gfpgan
```

---

## 5. 에이전트 프레임워크 (Multi-Agent)

| 프레임워크 | 특장 | 설치 |
|-----------|------|------|
| **CrewAI** | 역할 기반 멀티에이전트 (간단) | `pip install crewai` |
| **AutoGen** | Microsoft, 대화형 에이전트 | `pip install pyautogen` |
| **LangGraph** | LangChain 그래프 기반 워크플로우 | `pip install langgraph` |
| **Swarm** | OpenAI, 경량 핸드오프 | github |
| **Agency Swarm** | VRSEN, 도구 기반 에이전트 팀 | `pip install agency-swarm` |
| **Claude Agent SDK** | Anthropic 공식 | `pip install claude-agent-sdk` |
| **smolagents** | Hugging Face, 코드 에이전트 | `pip install smolagents` |
| **DSPy** | 프로그래밍 방식 프롬프트 최적화 | `pip install dspy-ai` |
| **Haystack** | deepset, RAG+에이전트 | `pip install haystack-ai` |

---

## 6. 파인튜닝 / 커스텀 모델

```bash
pip install peft              # LoRA/QLoRA (Hugging Face)
pip install trl               # RLHF/DPO 학습
pip install unsloth           # 2x 빠른 파인튜닝
pip install axolotl           # 올인원 파인튜닝
pip install llama-cpp-python  # GGUF 로컬 추론
pip install vllm              # 고속 LLM 서빙
pip install mlx-lm            # Apple Silicon LLM
pip install bitsandbytes      # 4bit/8bit 양자화
```

| 방법 | VRAM | 용도 |
|------|------|------|
| **Full Fine-tuning** | 40GB+ | 전체 모델 재학습 |
| **LoRA** | 8GB+ | 어댑터만 학습 (경량) |
| **QLoRA** | 4GB+ | 양자화 + LoRA (최소 VRAM) |
| **DPO** | 8GB+ | 선호도 학습 (RLHF 대안) |

---

## 7. 프롬프트 엔지니어링 고급 패턴

| 패턴 | 설명 |
|------|------|
| **Chain-of-Thought (CoT)** | "단계별로 생각해봐" |
| **Tree-of-Thought (ToT)** | 여러 사고 경로 탐색 후 최선 선택 |
| **Self-Consistency** | 같은 질문 N번 → 다수결 |
| **ReAct** | 추론+행동 반복 (도구 사용) |
| **Reflection** | 자기 답변 비판 후 개선 |
| **Meta-Prompting** | LLM이 프롬프트를 생성 |
| **Few-Shot** | 예시 3~5개 제공 |
| **Constitutional AI** | 원칙 기반 자기 수정 |

---

## 8. 평가 / 안전 (Evaluation & Safety)

```bash
pip install ragas             # RAG 평가 (faithfulness, relevance)
pip install deepeval          # LLM 평가 프레임워크
pip install promptfoo         # 프롬프트 A/B 테스트
pip install guardrails-ai     # 출력 검증 (가드레일)
pip install nemoguardrails    # NVIDIA 대화 안전
pip install langfuse          # LLM 관측성 (트레이싱)
pip install phoenix           # Arize Phoenix (LLM 관측) (이미 설치 가능)
pip install whylogs           # 데이터/모델 모니터링
```

---

## 9. 멀티모달 (Vision-Language)

| 모델 | 특장 | 접근 |
|------|------|------|
| **Claude 4.x Vision** | 이미지 이해 최강 | API |
| **GPT-4V/4o** | 멀티모달 범용 | API |
| **Gemini Pro Vision** | Google 멀티모달 | API |
| **LLaVA** | 오픈소스 VLM (로컬) | `pip install llava` |
| **Florence-2** | MS 비전 파운데이션 | `pip install transformers` |
| **Qwen-VL** | 알리바바 멀티모달 | `pip install transformers` |
| **InternVL** | 오픈소스 VLM (대규모) | github |
| **Moondream** | 경량 VLM (1.8B) | `pip install moondream` |

---

## 10. 코드 생성 / AI IDE

| 도구 | 특장 | 비용 |
|------|------|------|
| **Claude Code** | CLI 에이전트 (현재 사용 중) | API 과금 |
| **Cursor** | AI IDE (Claude/GPT 내장) | $20/mo |
| **Windsurf** | Codeium AI IDE | 무료 티어 |
| **Aider** | CLI 코딩 에이전트 | 무료 오픈소스 |
| **SWE-agent** | 자율 버그 수정 에이전트 | 무료 오픈소스 |
| **OpenHands** | 자율 소프트웨어 개발 | 무료 오픈소스 |
| **Bolt.new** | 풀스택 앱 즉시 생성 | 무료 티어 |
| **v0.dev** | UI 컴포넌트 생성 (Vercel) | 무료 티어 |
| **Lovable** | 앱 빌더 AI | 무료 티어 |

---

## Phase 로드맵

```text
Phase 1  LLM 텍스트 (Claude·Codex·Gemini 오케스트레이션)
Phase 2  디자인 (JS/CSS 100+ CDN)
Phase 3  미디어 (이미지·영상·오디오 복원·생성)
Phase 4  실시간 (WebSocket·WebRTC·대시보드·IoT)
Phase 5 🔜 자율 에이전트 (CrewAI·AutoGen·LangGraph)
Phase 6 🔜 엣지/온디바이스 (모바일 AI·TinyML·WASM)
```
