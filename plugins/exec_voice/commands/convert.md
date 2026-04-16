---
description: "오디오 파일 변환·편집 — FFmpeg 기반 (mp3↔wav↔m4a, 자르기, 노이즈 제거)"
allowed-tools: Bash(ffmpeg:*), Bash(where:*), Bash(python:*)
---

## Context
- FFmpeg: !`where ffmpeg 2>/dev/null && echo OK || echo 없음`
- noisereduce: !`python -c "import noisereduce; print('OK')" 2>/dev/null || echo 없음`

## Your task

FFmpeg 없음 → `winget install Gyan.FFmpeg` 안내 후 중단.

### 변환 유형 (입력에 따라 자동 판단)

**형식 변환:**
```
ffmpeg -i input.m4a -acodec libmp3lame output.mp3
ffmpeg -i input.mp3 -acodec pcm_s16le output.wav
```

**구간 자르기:**
```
ffmpeg -i input.mp3 -ss 00:01:00 -to 00:03:00 -c copy output_cut.mp3
```

**볼륨 조절:**
```
ffmpeg -i input.mp3 -filter:a "volume=2.0" output_loud.mp3
```

**노이즈 제거 (noisereduce):**
```python
import noisereduce as nr
import soundfile as sf
import numpy as np

data, rate = sf.read("input.wav")
reduced = nr.reduce_noise(y=data, sr=rate)
sf.write("output_clean.wav", reduced, rate)
```

입력: `$ARGUMENTS` 형식으로 작업 지시 받아 적합한 명령 선택 후 실행.

### 결과
- 출력 파일: `docs/YYYY-MM-DD/audio/` 저장
- 파일 크기 비교 (변환 전/후)
