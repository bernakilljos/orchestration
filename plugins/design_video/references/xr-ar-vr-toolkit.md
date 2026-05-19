# XR / AR / VR Toolkit — 확장현실·증강현실·가상현실 개발 도구

> **목적**: 웹 XR부터 네이티브 AR/VR까지 개발 도구 총정리

---

## 1. WebXR (브라우저 XR — 설치 없이 즉시 체험)

### 프레임워크
```html
<!-- A-Frame — 가장 쉬운 WebVR/AR (Mozilla) -->
<script src="https://cdn.jsdelivr.net/npm/aframe@1.6.0/dist/aframe-master.min.js"></script>
<a-scene>
  <a-box position="0 1 -3" color="#4CC3D9" shadow></a-box>
  <a-sphere position="-1 1.5 -5" radius="1.25" color="#EF2D5E"></a-sphere>
  <a-cylinder position="1 0.75 -3" radius="0.5" height="1.5" color="#FFC65D"></a-cylinder>
  <a-plane position="0 0 -4" rotation="-90 0 0" width="4" height="4" color="#7BC8A4"></a-plane>
  <a-sky color="#ECECEC"></a-sky>
</a-scene>
```

```html
<!-- Three.js + WebXR -->
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/examples/js/controls/OrbitControls.js"></script>

<!-- Babylon.js — 풀 3D 엔진 + WebXR 내장 -->
<script src="https://cdn.jsdelivr.net/npm/babylonjs@7.10.1/babylon.js"></script>
<script src="https://cdn.jsdelivr.net/npm/babylonjs-loaders@7.10.1/babylonjs.loaders.min.js"></script>

<!-- PlayCanvas — 3D 게임 엔진 (WebXR) -->
<script src="https://cdn.jsdelivr.net/npm/playcanvas@1.72.0/build/playcanvas.min.js"></script>

<!-- Model Viewer — 3D 모델 뷰어 (Google, AR 내장) -->
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js"></script>
<model-viewer src="model.glb" ar auto-rotate camera-controls></model-viewer>

<!-- 8th Wall — 웹 AR (마커리스, SLAM) -->
<!-- 상용, 월 $99~ -->
```

### A-Frame 컴포넌트
```html
<!-- AR 모드 (카메라 기반) -->
<a-scene embedded arjs>
  <a-marker preset="hiro">
    <a-box position="0 0.5 0" color="tomato"></a-box>
  </a-marker>
  <a-entity camera></a-entity>
</a-scene>
<script src="https://cdn.jsdelivr.net/npm/aframe-ar@0.2.1/aframe-ar.min.js"></script>

<!-- 핸드 트래킹 -->
<a-scene webxr="requiredFeatures: hand-tracking">
  <a-entity hand-tracking-controls="hand: left"></a-entity>
  <a-entity hand-tracking-controls="hand: right"></a-entity>
</a-scene>

<!-- 물리 엔진 -->
<script src="https://cdn.jsdelivr.net/npm/aframe-physics-system@4.0.1/dist/aframe-physics-system.min.js"></script>
```

---

## 2. AR (증강현실)

### 모바일 AR SDK
| SDK | 플랫폼 | 특장 |
|-----|--------|------|
| **ARKit** | iOS | Apple 네이티브, LiDAR, 씬 재구성 |
| **ARCore** | Android | Google 네이티브, 환경 이해 |
| **Vuforia** | 크로스플랫폼 | 이미지/오브젝트 인식 최강 |
| **Wikitude** | 크로스플랫폼 | SLAM + 이미지 트래킹 |
| **Lightship (Niantic)** | 크로스플랫폼 | 포켓몬GO 기술, VPS |
| **Snap AR** | Snapchat | Lens Studio (소셜 AR) |
| **Meta Spark** | Instagram/FB | 소셜 AR 필터 |
| **ZapWorks** | 웹+앱 | 코드 없이 AR 제작 |

### AR.js (웹 AR — 마커 기반)
```html
<script src="https://cdn.jsdelivr.net/npm/ar.js@3.4.5/aframe/build/aframe-ar.js"></script>
```

### Python AR
```bash
pip install opencv-python     # ArUco 마커 인식
pip install mediapipe          # 얼굴/손/포즈 AR
```

---

## 3. VR (가상현실)

### VR 헤드셋 SDK
| SDK | 헤드셋 | 특장 |
|-----|--------|------|
| **Meta Quest SDK** | Quest 3/Pro | OpenXR, 핸드트래킹, MR |
| **SteamVR/OpenXR** | Valve Index, HTC Vive | PC VR 표준 |
| **Apple visionOS** | Vision Pro | Swift, RealityKit, SwiftUI |
| **PSVR 2 SDK** | PlayStation | 게임 전용 |
| **Pico SDK** | Pico 4 | 중국 시장 + 글로벌 |

### Unity XR (크로스플랫폼)
```text
Unity XR Interaction Toolkit — 표준 XR 인터랙션
XR Plugin Management — 멀티 헤드셋 자동 전환
OpenXR Plugin — 표준 API
```

### Unreal Engine VR
```text
VR Template — 기본 VR 프로젝트
OpenXR — 크로스 헤드셋
Meta XR Plugin — Quest 최적화
```

---

## 4. 3D 모델링 / 에셋

| 도구 | 특장 | 비용 |
|------|------|------|
| **Blender** | 오픈소스 3D 표준 (모델링+애니메이션+렌더링) | 무료 |
| **Spline** | 웹 3D 에디터 (코드 export) | 무료 |
| **Sketchfab** | 3D 모델 마켓 + 뷰어 | 무료+유료 |
| **Ready Player Me** | 아바타 생성 API | 무료 (10k MAU) |
| **Meshy** | AI 텍스트→3D | 무료 티어 |
| **TripoSR** | 이미지→3D (로컬) | 무료 |
| **Polycam** | 3D 스캔 (LiDAR/사진) | 무료 |
| **Luma AI** | NeRF/3DGS 스캔 | 무료 |

### 3D 파일 형식
| 형식 | 용도 |
|------|------|
| **glTF/GLB** | 웹 3D 표준 ("JPEG of 3D") |
| **USDZ** | Apple AR 표준 |
| **FBX** | 게임 엔진 교환 |
| **OBJ** | 범용 (레거시) |
| **STL** | 3D 프린팅 |

### Python 3D
```bash
pip install trimesh           # 3D 메쉬 조작
pip install open3d            # 포인트 클라우드
pip install pyvista           # 3D 시각화
pip install vedo              # 3D 과학 시각화
pip install pygltflib         # glTF 읽기/쓰기
pip install pyrender          # 오프스크린 3D 렌더링
```

---

## 5. 소셜 / 멀티플레이어 XR

| 플랫폼 | 특장 |
|--------|------|
| **VRChat** | 소셜 VR (아바타, 월드) |
| **Rec Room** | 소셜 게임 플랫폼 |
| **Spatial** | 비즈니스 미팅 VR |
| **Gather** | 2D/3D 가상 오피스 |
| **Frame VR** | 웹 기반 VR 공간 |
| **Mozilla Hubs** | 오픈소스 소셜 VR (웹) |

### 멀티플레이어 인프라
```bash
# Colyseus — WebSocket 멀티플레이어 서버
npm install colyseus

# Photon — 실시간 멀티플레이어 (Unity)
# Normcore — VR 멀티플레이어 SDK

# Croquet — 동기화 프레임워크
npm install @croquet/croquet
```

---

## 6. 공간 오디오

```bash
pip install pyloudnorm        # 라우드니스 측정
```

```html
<!-- Resonance Audio (Google) — 공간 오디오 -->
<script src="https://cdn.jsdelivr.net/npm/resonance-audio@1.0.0/build/resonance-audio.min.js"></script>

<!-- Howler.js + 공간 오디오 -->
<script src="https://cdn.jsdelivr.net/npm/howler@2.2.4/dist/howler.min.js"></script>
```

```javascript
// Web Audio API 공간 오디오
const ctx = new AudioContext();
const panner = ctx.createPanner();
panner.panningModel = 'HRTF';
panner.setPosition(1, 0, -1);  // x, y, z
```

---

## 7. NeRF / 3D Gaussian Splatting (사진→3D)

```bash
pip install nerfstudio         # NeRF 통합 프레임워크
pip install gsplat             # 3D Gaussian Splatting
pip install viser              # 3D 웹 뷰어 (Python)

# Instant-NGP (NVIDIA) — 초고속 NeRF
# 3D Gaussian Splatting — github.com/graphdeco-inria/gaussian-splatting
```

```html
<!-- 3DGS 웹 뷰어 -->
<script src="https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.min.js"></script>
<!-- antimatter15/splat — 웹 기반 3DGS 뷰어 -->
```

---

## 추천 조합

### 웹 AR 체험 (가장 쉬움)
```text
A-Frame + AR.js + Model Viewer + Three.js
```

### 모바일 AR 앱
```text
Unity + ARKit/ARCore + Vuforia + Ready Player Me
```

### VR 게임/체험
```text
Unity XR Toolkit + OpenXR + Meta Quest SDK + Blender
```

### 3D 스캔→웹
```text
Polycam/Luma AI → glTF → Model Viewer → 웹 배포
```

### AI 3D 생성
```text
TripoSR (이미지→3D) + Meshy (텍스트→3D) + Blender (편집) → glTF
```
