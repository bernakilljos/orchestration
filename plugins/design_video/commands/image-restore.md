---
description: "이미지 복원 — 초해상도·얼굴복원·컬러화·배경제거·노이즈제거·스크래치제거"
allowed-tools: Bash(python:*), Bash(pip:*), Read, Write
---

# /image-restore — 이미지 복원 파이프라인

## 사용법
```text
/image-restore <input> [--scale 2|4] [--face] [--colorize] [--remove-bg] [--denoise]
```

## 도구별 용도

### 초해상도 (저해상도 → 고해상도)
```bash
# Real-ESRGAN x4 (범용)
python -m realesrgan -i input.jpg -o output.jpg -s 4

# 얼굴 포함 영상
python -m realesrgan -i input.jpg -o output.jpg -s 4 --face_enhance
```

### 얼굴 복원 (흐릿한 얼굴 → 선명)
```bash
# CodeFormer (최강)
python inference_codeformer.py -w 0.7 --input_path photos/ --output_path restored/ --bg_upsampler realesrgan --face_upsample

# GFP-GAN
python inference_gfpgan.py -i photos/ -o restored/ -v 1.4 -s 4 --bg_upsampler realesrgan
```

### 흑백 → 컬러
```python
from deoldify.visualize import get_image_colorizer
colorizer = get_image_colorizer(artistic=True)
colorizer.plot_transformed_image('bw.jpg', render_factor=35)
```

### 배경 제거
```python
from rembg import remove
from PIL import Image
output = remove(Image.open('photo.jpg'))
output.save('no_bg.png')
```

### 노이즈 제거
```python
import cv2
img = cv2.imread('noisy.jpg')
denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
cv2.imwrite('clean.jpg', denoised)
```

### 스크래치·손상 제거
```bash
# Bringing-Old-Photos-Back-to-Life (MS Research)
python run.py --input_folder damaged/ --output_folder fixed/ --with_scratch --GPU 0
```

## 오래된 사진 전체 파이프라인
1. 스크래치 제거 → 2. 컬러화 (흑백이면) → 3. 얼굴 복원 → 4. 전체 업스케일

## 참조
- `plugins/design_ppt/references/media-restoration-toolkit.md` § 1
