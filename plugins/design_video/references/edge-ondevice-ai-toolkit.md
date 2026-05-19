# Edge / On-Device AI Toolkit — 모바일·브라우저·IoT AI

> **Phase 6**: 클라우드 → 엣지/디바이스로. 오프라인·저지연·프라이버시

---

## 1. 브라우저 AI (WebAssembly / WebGPU)

### 추론 프레임워크
| 도구 | 특장 | CDN/설치 |
|------|------|----------|
| **Transformers.js** | Hugging Face 모델 브라우저 실행 | `<script src="https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2/dist/transformers.min.js">` |
| **ONNX Runtime Web** | ONNX 모델 브라우저 추론 | `<script src="https://cdn.jsdelivr.net/npm/onnxruntime-web@1.17.3/dist/ort.min.js">` |
| **TensorFlow.js** | TF 모델 브라우저/Node 실행 | `<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.19.0/dist/tf.min.js">` |
| **MediaPipe** | 얼굴/손/포즈 실시간 (Google) | `<script src="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm/vision_wasm_internal.js">` |
| **WebLLM** | LLM 브라우저 실행 (WebGPU) | npm install @mlc-ai/web-llm |
| **web-stable-diffusion** | SD 브라우저 실행 (WebGPU) | github |

```javascript
// Transformers.js — 브라우저에서 감정 분석
import { pipeline } from '@xenova/transformers';
const classifier = await pipeline('sentiment-analysis');
const result = await classifier('이 영화 정말 좋아요!');
// [{label: 'POSITIVE', score: 0.99}]

// 브라우저에서 이미지 분류
const detector = await pipeline('object-detection', 'Xenova/detr-resnet-50');
const result = await detector('photo.jpg');
```

```javascript
// TensorFlow.js — 실시간 포즈 감지
const model = await poseDetection.createDetector(
  poseDetection.SupportedModels.MoveNet
);
const poses = await model.estimatePoses(video);
```

### WebGPU 가속
```javascript
// WebGPU 지원 확인
if ('gpu' in navigator) {
  const adapter = await navigator.gpu.requestAdapter();
  const device = await adapter.requestDevice();
  // WebGPU 가속 AI 추론 가능
}
```

---

## 2. 모바일 AI (iOS / Android)

### 크로스플랫폼
| 프레임워크 | 언어 | AI 통합 |
|-----------|------|---------|
| **React Native** | JS/TS | TensorFlow Lite, ONNX, CoreML 브릿지 |
| **Flutter** | Dart | tflite_flutter, google_mlkit |
| **Kotlin Multiplatform** | Kotlin | ONNX, TF Lite |
| **MAUI** | C# | ONNX Runtime, ML.NET |
| **Capacitor** | Web→Native | 웹 AI + 네이티브 브릿지 |

### iOS
```sql
CoreML          — Apple 네이티브 ML (Vision, NLP, Sound)
Create ML       — 모델 학습 (Mac에서)
MLX             — Apple Silicon 최적화 추론
coremltools     — PyTorch/TF → CoreML 변환
```

### Android
```text
TensorFlow Lite — 모바일 추론 표준
ML Kit          — Google 사전학습 API (OCR, 얼굴, 바코드)
NNAPI           — Android 하드웨어 가속
MediaPipe       — 실시간 비전/오디오
Executorch      — PyTorch 모바일 실행
```

### 모델 변환
```bash
pip install coremltools       # PyTorch → CoreML (iOS)
pip install tflite-support    # PyTorch → TF Lite (Android)
pip install onnx onnxruntime  # PyTorch → ONNX (범용)
pip install ai-edge-torch     # PyTorch → TF Lite (Google 최신)
pip install executorch        # PyTorch → ExecuTorch (Meta)
```

---

## 3. 로컬 LLM (On-Device Large Language Models)

### 실행 엔진
| 도구 | 특장 | 설치 |
|------|------|------|
| **Ollama** | 원클릭 로컬 LLM (이미 설치 가능) | ollama.com |
| **llama.cpp** | C++ 최적화 (CPU/GPU) | github |
| **vLLM** | 고속 서빙 (PagedAttention) | `pip install vllm` |
| **MLX** | Apple Silicon 최적화 | `pip install mlx-lm` |
| **LM Studio** | GUI 로컬 LLM | lmstudio.ai |
| **Jan** | 오픈소스 ChatGPT 대안 (로컬) | jan.ai |
| **GPT4All** | CPU 로컬 LLM | gpt4all.io |
| **koboldcpp** | 경량 로컬 LLM 서버 | github |

### 경량 모델 (엣지 가능)
| 모델 | 파라미터 | RAM | 용도 |
|------|---------|-----|------|
| **Phi-3 Mini** | 3.8B | 4GB | 범용 (Microsoft) |
| **Gemma 2** | 2B/9B | 2~8GB | 범용 (Google) |
| **Llama 3.2** | 1B/3B | 1~3GB | 모바일 (Meta) |
| **Qwen 2.5** | 0.5B~72B | 0.5~48GB | 다국어 (Alibaba) |
| **SmolLM** | 135M~1.7B | 0.2~2GB | 초경량 (HF) |
| **TinyLlama** | 1.1B | 1GB | 임베디드 |
| **Moondream** | 1.8B | 2GB | 비전+언어 |

```bash
# Ollama — 원클릭 실행
ollama run phi3
ollama run gemma2:2b
ollama run llama3.2:1b
```

---

## 4. TinyML / 마이크로컨트롤러 AI

| 프레임워크 | 타겟 | 설치 |
|-----------|------|------|
| **TensorFlow Lite Micro** | Arduino, ESP32, STM32 | C++ 라이브러리 |
| **Edge Impulse** | 센서 데이터 ML (GUI) | edgeimpulse.com |
| **TinyMaix** | 초경량 NN (<10KB RAM) | github |
| **microTVM** | TVM 컴파일러 → MCU | apache/tvm |
| **CMSIS-NN** | ARM Cortex-M 최적화 | ARM github |

```python
# Edge Impulse — 센서 데이터 → 모델 → MCU 배포
pip install edgeimpulse       # Python SDK
# 또는 CLI
npm install -g edge-impulse-cli
edge-impulse-data-forwarder   # 센서 데이터 수집
edge-impulse-blocks           # 커스텀 처리 블록
```

### 지원 하드웨어
| 보드 | AI 가속 | 가격 |
|------|---------|------|
| **Raspberry Pi 5** | CPU (NPU 없음) | $60 |
| **Coral Dev Board** | Edge TPU (4 TOPS) | $150 |
| **NVIDIA Jetson Nano** | CUDA GPU (128코어) | $149 |
| **NVIDIA Jetson Orin Nano** | CUDA GPU (1024코어, 40 TOPS) | $249 |
| **Arduino Nano 33 BLE** | TFLite Micro | $25 |
| **ESP32-S3** | TFLite Micro | $5 |
| **Orange Pi AI Pro** | Ascend NPU (8 TOPS) | $110 |
| **Qualcomm RB3 Gen 2** | Hexagon DSP + NPU | $200 |

---

## 5. WASM AI (WebAssembly)

```bash
# 모델 → WASM 컴파일
pip install emscripten        # C/C++ → WASM
pip install pyodide           # Python → WASM (브라우저에서 Python)

# ONNX → WASM
npm install onnxruntime-web   # ONNX Runtime WASM 백엔드
```

```html
<!-- Pyodide — 브라우저에서 Python + NumPy + scikit-learn -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js"></script>
<script>
  const pyodide = await loadPyodide();
  await pyodide.loadPackage(['numpy', 'scikit-learn']);
  pyodide.runPython(`
    from sklearn.linear_model import LinearRegression
    import numpy as np
    X = np.array([[1], [2], [3]])
    y = np.array([2, 4, 6])
    model = LinearRegression().fit(X, y)
    print(model.predict([[4]]))  # [8.]
  `);
</script>
```

---

## 6. Federated Learning (연합 학습)

```bash
pip install flwr              # Flower — 연합 학습 프레임워크
pip install pysyft            # PySyft — 프라이버시 보존 ML
pip install opacus            # DP-SGD (차등 프라이버시)
pip install tenseal           # 동형 암호화 ML
```

| 기법 | 용도 |
|------|------|
| **Federated Averaging** | 디바이스에서 학습, 서버에서 집계 |
| **Differential Privacy** | 개인정보 보호 학습 |
| **Homomorphic Encryption** | 암호화된 데이터로 추론 |
| **Secure Aggregation** | 안전한 모델 업데이트 집계 |

---

## 7. AI 모델 최적화 (경량화)

```bash
pip install optimum           # Hugging Face 모델 최적화
pip install neural-compressor # Intel 양자화/프루닝
pip install torch-pruning     # PyTorch 구조적 프루닝
pip install onnxoptimizer     # ONNX 그래프 최적화
pip install openvino          # Intel 추론 최적화
```

| 기법 | 효과 | 도구 |
|------|------|------|
| **양자화 (Quantization)** | 모델 크기 4x 축소 | bitsandbytes, GPTQ, AWQ |
| **프루닝 (Pruning)** | 불필요 뉴런 제거 | torch-pruning |
| **증류 (Distillation)** | 큰 모델 → 작은 모델 | transformers |
| **스파시티 (Sparsity)** | 희소 연산 가속 | neural-compressor |

---

## 8. 오프라인 음성 AI

| 도구 | 기능 | 설치 |
|------|------|------|
| **Whisper.cpp** | 오프라인 STT (C++) | github |
| **Vosk** | 오프라인 STT (경량, 20+ 언어) | `pip install vosk` |
| **Piper** | 오프라인 TTS (경량, 빠름) | github |
| **Coqui TTS** | 오프라인 TTS (다국어) | `pip install TTS` |
| **Silero** | 오프라인 STT/TTS/VAD | `pip install silero` |
| **sherpa-onnx** | 오프라인 STT/TTS/키워드 (모바일) | `pip install sherpa-onnx` |

```python
# Vosk — 오프라인 한국어 음성 인식
from vosk import Model, KaldiRecognizer
import wave

model = Model("vosk-model-ko-0.22")
wf = wave.open("recording.wav", "rb")
rec = KaldiRecognizer(model, wf.getframerate())
while True:
    data = wf.readframes(4000)
    if len(data) == 0: break
    rec.AcceptWaveform(data)
print(rec.FinalResult())
```

---

## 9. 프라이버시 AI

| 도구 | 용도 | 설치 |
|------|------|------|
| **LangChain + Ollama** | 완전 로컬 RAG | `pip install langchain-ollama` |
| **PrivateGPT** | 로컬 문서 QA | github |
| **LocalAI** | OpenAI API 호환 로컬 서버 | github |
| **AnythingLLM** | 로컬 문서 챗봇 (GUI) | github |
| **Danswer** | 기업 문서 검색 (셀프호스팅) | github |

---

## 추천 조합

### 브라우저 AI 앱
```text
Transformers.js + ONNX Runtime Web + Pyodide + TensorFlow.js
```

### 모바일 AI 앱
```text
React Native + TF Lite + CoreML/NNAPI + Whisper.cpp
```

### IoT 센서 AI
```text
Edge Impulse + ESP32-S3 + TFLite Micro + MQTT
```

### 완전 오프라인 어시스턴트
```text
Ollama (Phi-3) + Vosk (STT) + Piper (TTS) + ChromaDB (RAG)
```

### 프라이버시 문서 검색
```text
PrivateGPT + Ollama + ChromaDB + LangChain
```
