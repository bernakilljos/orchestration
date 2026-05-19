# Media Restoration Toolkit — 이미지·영상·오디오 복원·보정·AI 생성

> **목적**: 2000년대 저화질 영상, 오래된 사진, 열악한 녹음 → AI 복원
> **환경**: Python + CUDA GPU 권장 (CPU 가능하나 느림)

---

## 1. 이미지 복원 (Image Restoration)

### 1.1 초해상도 (Super Resolution) — 저화질 → 고화질

| 도구 | 배율 | 특장 | 설치 |
|------|------|------|------|
| **Real-ESRGAN** | x2/x4 | 범용 최강, 애니메이션도 OK | `pip install realesrgan` |
| **SwinIR** | x2/x4 | 트랜스포머 기반, 텍스처 보존 | `pip install swinir` |
| **HAT** | x2/x4 | 2024 SOTA, SwinIR 개선 | github clone |
| **StableSR** | x4 | Stable Diffusion 기반 (디테일 생성) | github clone |
| **BSRGAN** | x4 | 실제 열화(블러+노이즈) 강건 | `pip install basicsr` |

```python
# Real-ESRGAN 사용법
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
upsampler = RealESRGANer(scale=4, model_path='RealESRGAN_x4plus.pth', model=model)
output, _ = upsampler.enhance(img, outscale=4)
```

### 1.2 얼굴 복원 (Face Restoration)

| 도구 | 특장 | 설치 |
|------|------|------|
| **CodeFormer** | 최강 얼굴 복원 (눈·코·입 재생성) | `pip install codeformer-pip` |
| **GFP-GAN** | 얼굴 + 배경 동시 복원 | `pip install gfpgan` |
| **VQFR** | VQ 코드북 기반 (선명도 강조) | github clone |
| **RestoreFormer** | 트랜스포머 기반 얼굴 복원 | github clone |

```python
# CodeFormer — 옛날 졸업사진 복원
import subprocess
subprocess.run([
    'python', 'inference_codeformer.py',
    '-w', '0.7',           # 0=원본 유지, 1=AI 최대
    '--input_path', 'old_photos/',
    '--output_path', 'restored/',
    '--bg_upsampler', 'realesrgan',  # 배경도 업스케일
    '--face_upsample'
])
```

### 1.3 오래된 사진 복원 (Old Photo Restoration)

| 도구 | 특장 | 설치 |
|------|------|------|
| **Bringing-Old-Photos-Back-to-Life** | MS Research, 스크래치·색바램 제거 | github clone |
| **DeOldify** | 흑백→컬러 (컬러라이제이션) | `pip install deoldify` |
| **Colorize** | 자동 컬러화 + 수동 힌트 | github clone |

```python
# DeOldify — 흑백 사진 컬러화
from deoldify import device
from deoldify.visualize import get_image_colorizer
colorizer = get_image_colorizer(artistic=True)
colorizer.plot_transformed_image('bw_photo.jpg', render_factor=35)
```

### 1.4 노이즈 제거 (Denoising)

| 도구 | 특장 | 설치 |
|------|------|------|
| **NAFNet** | 2022 SOTA, 빠르고 정확 | github clone |
| **Restormer** | 트랜스포머 기반, 비·안개·블러 제거 | github clone |
| **DnCNN** | CNN 기반 가우시안 노이즈 | `pip install basicsr` |
| **scikit-image** | 전통 필터 (NLM, bilateral) | `pip install scikit-image` |

### 1.5 배경 제거 / 교체

| 도구 | 특장 | 설치 |
|------|------|------|
| **rembg** | 원클릭 배경 제거 (U2-Net) | `pip install rembg[gpu]` |
| **SAM** (Segment Anything) | 클릭/프롬프트 기반 세그멘테이션 | `pip install segment-anything` |
| **transparent-background** | InSPyReNet 기반 | `pip install transparent-background` |
| **backgroundremover** | CLI 도구 | `pip install backgroundremover` |

---

## 2. 영상 복원 (Video Restoration)

### 2.1 영상 초해상도 — 480p/720p → 1080p/4K

| 도구 | 특장 | 설치 |
|------|------|------|
| **Real-ESRGAN (Video)** | 프레임별 업스케일 | `pip install realesrgan` |
| **BasicVSR++** | 시간축 활용 (전후 프레임 참조) | `pip install basicsr` |
| **RealBasicVSR** | 실제 영상 열화에 강건 | github clone |
| **EDVR** | 다중 프레임 정렬+융합 | `pip install basicsr` |
| **VRT** | Video Restoration Transformer | github clone |

```bash
# Real-ESRGAN 비디오 업스케일 (CLI)
python inference_realesrgan_video.py \
  -i old_video.mp4 \
  -o restored_video.mp4 \
  -n realesr-animevideov3 \
  -s 4 \
  --suffix _4x
```

```python
# Python으로 프레임별 처리
import cv2
from realesrgan import RealESRGANer

cap = cv2.VideoCapture('old_video.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3))*4, int(cap.get(4))*4

out = cv2.VideoWriter('restored.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    enhanced, _ = upsampler.enhance(frame, outscale=4)
    out.write(enhanced)
cap.release(); out.release()
```

### 2.2 프레임 보간 (Frame Interpolation) — 15fps → 60fps

| 도구 | 특장 | 설치 |
|------|------|------|
| **RIFE** | 실시간 보간 (최강 속도) | github clone |
| **FILM** | Google, 대규모 움직임 강건 | `pip install frame-interpolation` |
| **DAIN** | 깊이 인식 보간 | github clone |
| **FLAVR** | 다중 프레임 동시 생성 | github clone |
| **IFRNet** | 경량 실시간 보간 | github clone |

```bash
# RIFE — 24fps → 60fps
python inference_video.py \
  --exp=2 \
  --video=old_24fps.mp4 \
  --output=smooth_60fps.mp4
```

### 2.3 영상 안정화 (Stabilization)

```python
# OpenCV 영상 안정화
import cv2
stabilizer = cv2.videostab.TwoPassStabilizer()
# 또는 vidgear
from vidgear.gears.stabilizer import Stabilizer
stab = Stabilizer(smoothing_radius=25, border_size=5)
```

### 2.4 영상 노이즈 제거

| 도구 | 특장 | 설치 |
|------|------|------|
| **FastDVDnet** | 시간축 활용 빠른 디노이징 | github clone |
| **VRT** | 트랜스포머 기반 (최고 품질) | github clone |
| **hqdn3d** | FFmpeg 내장 필터 | FFmpeg 기본 |

```bash
# FFmpeg 내장 디노이징
ffmpeg -i noisy.mp4 -vf "hqdn3d=4:4:6:6" clean.mp4

# 고급: nlmeans (Non-Local Means)
ffmpeg -i noisy.mp4 -vf "nlmeans=10:7:5:3:3" clean.mp4
```

### 2.5 컬러 보정 / 색감 복원

```bash
# FFmpeg 색 보정
ffmpeg -i faded.mp4 -vf "eq=contrast=1.3:brightness=0.05:saturation=1.4" vibrant.mp4

# 자동 화이트밸런스
ffmpeg -i yellowish.mp4 -vf "colorbalance=rs=0.1:gs=0:bs=0.1" corrected.mp4

# 히스토그램 평활화 (대비 자동 개선)
ffmpeg -i low_contrast.mp4 -vf "histeq" enhanced.mp4
```

### 2.6 흑백 영상 컬러화

| 도구 | 특장 | 설치 |
|------|------|------|
| **DeOldify (Video)** | 자동 컬러화 (안정적) | `pip install deoldify` |
| **DDColor** | 2023 SOTA 컬러화 | github clone |
| **Colorize-Video** | 프레임별 + 시간 일관성 | github clone |

---

## 3. 오디오 복원·보정 (Audio Restoration)

### 3.1 노이즈 제거 / 음질 개선

| 도구 | 특장 | 설치 |
|------|------|------|
| **noisereduce** | 스펙트럴 게이팅 노이즈 제거 | `pip install noisereduce` |
| **DeepFilterNet** | DNN 실시간 노이즈 제거 | `pip install deepfilternet` |
| **Resemble Enhance** | AI 음성 향상 (해상도 업) | github clone |
| **Voicefixer** | 음성 복원 (대역폭 확장+디노이즈+디리버브) | `pip install voicefixer` |
| **AudioSR** | 오디오 초해상도 (16kHz→48kHz) | github clone |

```python
# noisereduce — 기본 노이즈 제거
import noisereduce as nr
import soundfile as sf

data, rate = sf.read('noisy_recording.wav')
reduced = nr.reduce_noise(y=data, sr=rate, stationary=True)
sf.write('clean.wav', reduced, rate)
```

```python
# Voicefixer — 오래된 녹음 복원
from voicefixer import VoiceFixer
vf = VoiceFixer()
vf.restore(input='old_recording.wav', output='restored.wav', cuda=True, mode=0)
# mode: 0=기본, 1=강력, 2=최강
```

### 3.2 스템 분리 (Stem Separation)

| 도구 | 출력 | 설치 |
|------|------|------|
| **Demucs** (Meta) | 보컬/드럼/베이스/기타 (4-stem) | `pip install demucs` |
| **Spleeter** (Deezer) | 2/4/5 stem | `pip install spleeter` |
| **UVR** (Ultimate Vocal Remover) | GUI + 10+ 모델 | 별도 설치 |
| **Music Source Separation** | ByteDance | github clone |

```bash
# Demucs — 보컬 분리
demucs -n htdemucs --two-stems=vocals old_song.mp3
# 결과: separated/htdemucs/old_song/vocals.wav, no_vocals.wav
```

### 3.3 AI 작곡 / 음악 생성

| 도구 | 특장 | 접근 |
|------|------|------|
| **Suno** | 텍스트→노래 (가사+멜로디+보컬) | suno.com (웹) |
| **Udio** | 텍스트→음악 (고품질) | udio.com (웹) |
| **MusicGen** (Meta) | 텍스트→음악 (로컬) | `pip install audiocraft` |
| **Bark** (Suno) | 텍스트→음성+효과음 | `pip install suno-bark` |
| **AudioLDM2** | 텍스트→오디오 | `pip install diffusers` |
| **Stable Audio** | Stability AI 음악 생성 | API |

```python
# MusicGen — 로컬 AI 작곡
from audiocraft.models import MusicGen
model = MusicGen.get_pretrained('facebook/musicgen-melody')
model.set_generation_params(duration=30)
wav = model.generate(['epic orchestral battle music, cinematic, 120bpm'])
# wav → .wav 저장
```

### 3.4 편곡 / 코드 분석

| 도구 | 특장 | 설치 |
|------|------|------|
| **librosa** | BPM, 키, 코드 진행 분석 | `pip install librosa` |
| **madmom** | 비트 추적, 코드 인식 | `pip install madmom` |
| **Omnizart** | 다악기 MIDI 추출 | `pip install omnizart` |
| **Basic Pitch** (Spotify) | 오디오→MIDI (정확도 높음) | `pip install basic-pitch` |
| **Magenta** (Google) | AI 작곡·편곡·드럼 | `pip install magenta` |

```python
# Basic Pitch — 노래 → MIDI
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
model_output, midi_data, note_events = predict('song.wav')
midi_data.write('song.mid')
```

### 3.5 TTS (Text-to-Speech) / 보이스 클로닝

| 도구 | 특장 | 설치 |
|------|------|------|
| **edge-tts** | Microsoft TTS (무료, 한국어 우수) | `pip install edge-tts` |
| **Coqui TTS** | 로컬 다국어 TTS + 보이스 클로닝 | `pip install TTS` |
| **Bark** | 감정·효과음 포함 음성 | `pip install suno-bark` |
| **Fish Speech** | 제로샷 보이스 클로닝 | github clone |
| **GPT-SoVITS** | 한국어 보이스 클로닝 (로컬) | github clone |
| **RVC** (Retrieval VC) | 보이스 변환 (커버곡) | github clone |
| **so-vits-svc** | 보이스 변환 (노래) | github clone |

```python
# edge-tts — 한국어 음성 생성
import asyncio, edge_tts
async def speak():
    tts = edge_tts.Communicate("안녕하세요, 자동 개발 에이전트입니다.", "ko-KR-SunHiNeural")
    await tts.save("output.mp3")
asyncio.run(speak())
```

---

## 4. 통합 워크플로우 (복원 파이프라인)

### 4.1 2000년대 저화질 영상 복원

```bash
# Step 1: 노이즈 제거
ffmpeg -i old_2003.avi -vf "hqdn3d=6:6:8:8" denoised.mp4

# Step 2: 초해상도 (480p → 1080p)
python inference_realesrgan_video.py -i denoised.mp4 -o upscaled.mp4 -s 2

# Step 3: 프레임 보간 (15fps → 30fps)
python inference_video.py --exp=1 --video=upscaled.mp4 --output=smooth.mp4

# Step 4: 색감 보정
ffmpeg -i smooth.mp4 -vf "eq=contrast=1.2:saturation=1.3" final.mp4

# Step 5: 오디오 복원 (별도)
python -c "
import noisereduce as nr; import soundfile as sf
d, r = sf.read('old_audio.wav')
sf.write('clean_audio.wav', nr.reduce_noise(y=d, sr=r), r)
"

# Step 6: 오디오 합성
ffmpeg -i final.mp4 -i clean_audio.wav -c:v copy -map 0:v -map 1:a restored_2003.mp4
```

### 4.2 오래된 사진 복원 (흑백·손상)

```bash
# Step 1: 스크래치·손상 제거
python run.py --input_folder old_photos/ --output_folder scratched_removed/ --GPU 0

# Step 2: 컬러화 (흑백이면)
python colorize.py --input scratched_removed/ --output colorized/

# Step 3: 얼굴 복원
python inference_codeformer.py -w 0.7 --input_path colorized/ --output_path faces_restored/

# Step 4: 전체 업스케일 (x4)
python inference_realesrgan.py -i faces_restored/ -o final/ -s 4
```

### 4.3 오래된 녹음 복원

```python
# Step 1: 노이즈 제거
import noisereduce as nr
import soundfile as sf
data, sr = sf.read('cassette_1995.wav')
clean = nr.reduce_noise(y=data, sr=sr, prop_decrease=0.8)

# Step 2: 대역폭 확장 (8kHz→48kHz)
from voicefixer import VoiceFixer
vf = VoiceFixer()
vf.restore(input='clean.wav', output='hifi.wav', cuda=True, mode=2)

# Step 3: EQ 보정 (저음 부스트)
from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter
audio = AudioSegment.from_wav('hifi.wav')
# 커스텀 EQ는 pedalboard 사용
```

---

## 5. GPU 요구사항

| 작업 | VRAM 최소 | 권장 |
|------|-----------|------|
| Real-ESRGAN (이미지) | 2GB | 4GB+ |
| Real-ESRGAN (영상) | 4GB | 8GB+ |
| CodeFormer (얼굴) | 4GB | 6GB+ |
| BasicVSR++ (영상) | 8GB | 12GB+ |
| RIFE (프레임 보간) | 2GB | 4GB+ |
| Demucs (스템 분리) | 4GB | 8GB+ |
| MusicGen (작곡) | 8GB | 16GB+ |
| Stable Diffusion (이미지 생성) | 6GB | 12GB+ |

**CPU 가능하지만 10~100x 느림**. CUDA GPU 강력 권장.

---

## 참조

- Real-ESRGAN: github.com/xinntao/Real-ESRGAN
- CodeFormer: github.com/sczhou/CodeFormer
- RIFE: github.com/megvii-research/ECCV2022-RIFE
- Demucs: github.com/facebookresearch/demucs
- MusicGen: github.com/facebookresearch/audiocraft
- Basic Pitch: github.com/spotify/basic-pitch
- DeOldify: github.com/jantic/DeOldify
