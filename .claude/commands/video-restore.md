---
description: "90년대~2000년대 저화질 영상 → 고화질 복원 (초해상도·프레임보간·디노이징·안정화·컬러보정)"
allowed-tools: Bash(python:*), Bash(pip:*), Bash(ffmpeg:*), Read, Write
---

# /video-restore — 영상 복원 파이프라인

## 사용법
```text
/video-restore <input_video> [--scale 2|4] [--fps 30|60] [--denoise] [--stabilize] [--colorize]
```

## 기본 동작 (전체 파이프라인)
1. FFmpeg 디노이징 (hqdn3d / nlmeans)
2. Real-ESRGAN 초해상도 (x2 또는 x4)
3. RIFE 프레임 보간 (15fps→30fps 또는 30fps→60fps)
4. 색감 자동 보정 (대비·채도 개선)
5. 오디오 복원 (noisereduce)
6. 최종 합성

## 도구 설치 (자동)
```bash
pip install realesrgan basicsr opencv-python noisereduce soundfile ffmpeg-python
# RIFE: git clone https://github.com/megvii-research/ECCV2022-RIFE
# GPU 권장: CUDA 11.8+
```

## 단계별 상세

### Step 1: 디노이징
```bash
ffmpeg -i input.mp4 -vf "hqdn3d=6:6:8:8" -c:a copy denoised.mp4
# 강한 노이즈: nlmeans 사용
ffmpeg -i input.mp4 -vf "nlmeans=10:7:5:3:3" -c:a copy denoised.mp4
```

### Step 2: 초해상도 (핵심)
```bash
# Real-ESRGAN (범용 최강)
python inference_realesrgan_video.py -i denoised.mp4 -o upscaled.mp4 -n RealESRGAN_x4plus -s 4

# 애니메이션/만화 전용
python inference_realesrgan_video.py -i denoised.mp4 -o upscaled.mp4 -n realesr-animevideov3 -s 4

# 얼굴 강화 (인물 중심 영상)
python inference_realesrgan_video.py -i denoised.mp4 -o upscaled.mp4 -n RealESRGAN_x4plus --face_enhance
```

모델 선택 가이드:
| 모델 | 용도 | 품질 | 속도 |
|------|------|------|------|
| RealESRGAN_x4plus | 실사 범용 | ★★★★★ | 느림 |
| RealESRGAN_x4plus_anime_6B | 애니메이션 | ★★★★★ | 보통 |
| realesr-animevideov3 | 애니메이션 비디오 | ★★★★ | 빠름 |
| RealESRNet_x4plus | 실사 (부드러움) | ★★★★ | 보통 |
| realesr-general-x4v3 | 범용 (경량) | ★★★ | 빠름 |

### Step 3: 프레임 보간 (부드러움)
```bash
# RIFE — 15fps → 30fps (exp=1), 30fps → 60fps (exp=1)
python inference_video.py --exp=1 --video=upscaled.mp4 --output=smooth.mp4

# 24fps → 60fps (2.5배 = exp=2 후 60fps 리샘플)
python inference_video.py --exp=2 --video=upscaled.mp4 --output=interpolated.mp4
ffmpeg -i interpolated.mp4 -r 60 -c:a copy smooth_60fps.mp4
```

### Step 4: 색감 보정
```bash
# 자동 대비·채도 개선
ffmpeg -i smooth.mp4 -vf "eq=contrast=1.2:brightness=0.03:saturation=1.3" color_corrected.mp4

# 화이트밸런스 (노란 빛 제거)
ffmpeg -i smooth.mp4 -vf "colorbalance=rs=0.1:gs=0:bs=0.1" wb_corrected.mp4

# 히스토그램 평활화 (자동)
ffmpeg -i smooth.mp4 -vf "histeq=strength=0.3" auto_enhanced.mp4

# 선명도 강화 (unsharp mask)
ffmpeg -i smooth.mp4 -vf "unsharp=5:5:1.0:5:5:0.0" sharpened.mp4
```

### Step 5: 오디오 복원
```python
import noisereduce as nr
import soundfile as sf

# 오디오 추출
import subprocess
subprocess.run(['ffmpeg', '-i', 'input.mp4', '-vn', '-acodec', 'pcm_s16le', 'audio.wav'])

# 노이즈 제거
data, rate = sf.read('audio.wav')
clean = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.8, stationary=True)
sf.write('clean_audio.wav', clean, rate)
```

### Step 6: 최종 합성
```bash
ffmpeg -i color_corrected.mp4 -i clean_audio.wav -c:v libx264 -crf 18 -c:a aac -b:a 192k -map 0:v -map 1:a final_restored.mp4
```

## 90년대 VHS/Hi8 특수 처리

VHS 특유의 문제:
- 인터레이스 (가로줄) → `yadif` 디인터레이스
- 컬러 블리딩 (색 번짐) → `colormatrix` 보정
- 트래킹 노이즈 (상하 흔들림) → `vidstabtransform` 안정화

```bash
# VHS 전용 파이프라인
ffmpeg -i vhs_tape.mp4 -vf "\
  yadif=1,\
  hqdn3d=8:8:10:10,\
  unsharp=5:5:0.8:5:5:0.0,\
  eq=contrast=1.3:saturation=1.4:brightness=0.02\
" -c:a copy vhs_cleaned.mp4

# 디인터레이스 + 안정화
ffmpeg -i vhs_tape.mp4 -vf "yadif=1,vidstabtransform=smoothing=30" stable.mp4
```

## 참조
- `plugins/design_ppt/references/media-restoration-toolkit.md` — 전체 도구 카탈로그
- `plugins/design_ppt/references/python-toolkit-pip.md` § 2 Video Processing
