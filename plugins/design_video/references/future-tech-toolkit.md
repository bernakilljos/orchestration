# Future Tech Toolkit — 양자 컴퓨팅·피지컬 AI·차세대 기술

> **목적**: 현재는 실험/연구 단계지만 곧 실용화될 기술 대비

---

## 1. 양자 컴퓨팅 (Quantum Computing)

### 프레임워크
| 도구 | 제공 | 설치 | 비고 |
|------|------|------|------|
| **Qiskit** | IBM | `pip install qiskit` | 가장 큰 생태계 |
| **Cirq** | Google | `pip install cirq` | 시카모어 프로세서 |
| **PennyLane** | Xanadu | `pip install pennylane` | 양자 ML 특화 |
| **Amazon Braket SDK** | AWS | `pip install amazon-braket-sdk` | 여러 QPU 접근 |
| **Q#** | Microsoft | .NET SDK | Azure Quantum |
| **Strawberry Fields** | Xanadu | `pip install strawberryfields` | 광자 양자 |

### 양자 ML (QML)
```python
# PennyLane — 양자 뉴럴 네트워크
import pennylane as qml
import numpy as np

dev = qml.device("default.qubit", wires=2)

@qml.qnode(dev)
def circuit(params):
    qml.RX(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# 하이브리드 양자-고전 최적화
opt = qml.GradientDescentOptimizer(stepsize=0.4)
params = np.array([0.5, 0.1])
for i in range(100):
    params = opt.step(circuit, params)
```

### 양자 시뮬레이터 (무료)
| 서비스 | QPU | 무료 |
|--------|-----|------|
| **IBM Quantum** | 127+ qubit | 무료 (큐 대기) |
| **Amazon Braket** | IonQ, Rigetti | $0.3/task~ |
| **Azure Quantum** | IonQ, Quantinuum | $500 크레딧 |
| **Google Quantum AI** | Sycamore | 연구 목적 |

### 양자 활용 사례
| 분야 | 양자 이점 |
|------|----------|
| **암호** | Shor 알고리즘 (RSA 해독), 양자 키 분배 (QKD) |
| **최적화** | 물류 경로, 포트폴리오, 스케줄링 (QAOA) |
| **시뮬레이션** | 분자·재료·약물 설계 |
| **ML** | 양자 SVM, 양자 GAN, 양자 강화학습 |

---

## 2. 피지컬 AI / 로보틱스

### 로봇 프레임워크
| 도구 | 특장 | 설치 |
|------|------|------|
| **ROS 2** | 로봇 운영체제 표준 | apt (Ubuntu) |
| **Isaac Sim** | NVIDIA 로봇 시뮬레이션 | NVIDIA Omniverse |
| **PyBullet** | 물리 시뮬레이션 (경량) | `pip install pybullet` |
| **MuJoCo** | DeepMind 물리 엔진 | `pip install mujoco` |
| **Gymnasium** | RL 환경 (OpenAI Gym 후속) | `pip install gymnasium` |
| **Stable Baselines3** | RL 알고리즘 모음 | `pip install stable-baselines3` |

### 자율주행
| 도구 | 특장 |
|------|------|
| **CARLA** | 오픈소스 자율주행 시뮬레이터 |
| **Autoware** | 오픈소스 자율주행 스택 |
| **Apollo** | 바이두 자율주행 |
| **comma.ai openpilot** | 오픈소스 ADAS |

### 드론
```python
pip install dronekit           # MAVLink 드론 제어
pip install airsim             # 드론/자동차 시뮬레이터 (MS)
```

### 휴머노이드 / 매니퓰레이터
| 프로젝트 | 특장 |
|---------|------|
| **NVIDIA GR00T** | 범용 휴머노이드 파운데이션 모델 |
| **Tesla Optimus** | Tesla 휴머노이드 |
| **Figure 01/02** | 범용 로봇 |
| **1X NEO** | OpenAI 투자 로봇 |

---

## 3. 뉴로모픽 컴퓨팅 (Neuromorphic)

| 칩 | 제조사 | 특장 |
|----|--------|------|
| **Loihi 2** | Intel | 스파이킹 뉴럴 네트워크 |
| **TrueNorth** | IBM | 100만 뉴런, 저전력 |
| **Akida** | BrainChip | 엣지 뉴로모픽 |
| **SpiNNaker** | Manchester Univ | 대규모 뇌 시뮬레이션 |

```python
pip install lava-nc            # Intel Lava (뉴로모픽 프레임워크)
pip install norse              # PyTorch 스파이킹 뉴럴 네트워크
pip install snnTorch           # SNN 학습 프레임워크
```

---

## 4. 생체 인터페이스 (BCI)

| 프로젝트 | 특장 |
|---------|------|
| **Neuralink** | 뇌 임플란트 (Elon Musk) |
| **OpenBCI** | 오픈소스 EEG | `pip install brainflow` |
| **Emotiv** | 소비자용 EEG 헤드셋 |
| **Muse** | 명상/집중도 측정 |

```python
pip install brainflow          # BCI 데이터 수집 (OpenBCI 호환)
pip install mne                # 뇌파 분석
pip install pyeeg              # EEG 특징 추출
```

---

## 5. 합성 생물학 / 바이오 AI

```python
pip install biopython          # 생물정보학
pip install rdkit              # 분자/화합물 설계
pip install deepchem           # 약물 발견 ML
pip install alphafold          # 단백질 구조 예측 (DeepMind)
pip install esm                # 단백질 언어 모델 (Meta)
```

---

## 6. 공간 컴퓨팅 (Spatial Computing)

### AR/VR/MR
| 플랫폼 | SDK |
|--------|-----|
| **Apple Vision Pro** | visionOS SDK (Swift) |
| **Meta Quest** | Meta XR SDK (Unity/Unreal) |
| **HoloLens 2** | MRTK (Mixed Reality Toolkit) |
| **WebXR** | 브라우저 AR/VR |

```html
<!-- WebXR (브라우저 VR) -->
<script src="https://cdn.jsdelivr.net/npm/aframe@1.5.0/dist/aframe-master.min.js"></script>
<a-scene>
  <a-box position="0 1 -3" color="#4CC3D9"></a-box>
  <a-sky color="#ECECEC"></a-sky>
</a-scene>
```

### 3D 스캐닝 / NeRF
```python
pip install nerfstudio         # NeRF (Neural Radiance Fields)
pip install gaussian-splatting # 3D Gaussian Splatting
pip install open3d             # 포인트 클라우드 처리
pip install trimesh            # 3D 메쉬 처리
```

---

## 7. 에너지 / 기후 AI

```python
pip install pvlib              # 태양광 시뮬레이션
pip install windpowerlib       # 풍력 시뮬레이션
pip install climatelearn       # 기후 예측 ML
pip install carbontracker      # ML 학습 탄소 배출 측정
```

---

## 8. 블록체인 / Web3

```python
pip install web3               # Ethereum (Web3.py)
pip install solana             # Solana
pip install brownie            # 스마트 컨트랙트 개발
pip install ape                # 스마트 컨트랙트 (Ape Framework)
```

```javascript
// ethers.js (CDN)
<script src="https://cdn.jsdelivr.net/npm/ethers@6.13.0/dist/ethers.umd.min.js"></script>
```

---

## 9. 포스트-양자 암호 (Post-Quantum Cryptography)

```python
pip install pqcrypto           # 포스트-양자 암호 알고리즘
pip install liboqs-python      # Open Quantum Safe
# NIST 표준: CRYSTALS-Kyber (키 교환), CRYSTALS-Dilithium (서명)
```

---

## Phase 로드맵 (최종)

```text
Phase 1 ✅ LLM 오케스트레이션 (Claude·Codex·Gemini)
Phase 2 ✅ 디자인 (JS/CSS 100+ CDN)
Phase 3 ✅ 미디어 (이미지·영상·오디오 복원·생성)
Phase 4 ✅ 실시간 (WebSocket·WebRTC·대시보드·IoT)
Phase 5 ✅ 생성형 AI (영상·3D·아바타·에이전트·파인튜닝)
Phase 6 ✅ 엣지/온디바이스 (모바일·TinyML·WASM)
Phase 7 ✅ 인프라 (DB·캐시·배포·CI/CD·K8s)
Phase 8 ✅ 비즈니스 로직 (인증·결제·예약·알림·검색·추천)
Phase 9 ✅ 미래 기술 (양자·로보틱스·뉴로모픽·BCI·공간컴퓨팅·Web3)
```
