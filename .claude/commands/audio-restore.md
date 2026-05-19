---
description: "오디오 복원 — 노이즈제거·대역확장·스템분리·보이스클로닝·AI작곡"
allowed-tools: Bash(python:*), Bash(pip:*), Bash(ffmpeg:*), Read, Write
---

# /audio-restore — 오디오 복원·편집

## 사용법
```text
/audio-restore <input> [--denoise] [--enhance] [--stems] [--transcribe]
```

## 노이즈 제거
```python
import noisereduce as nr
import soundfile as sf
data, rate = sf.read('noisy.wav')
clean = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.8)
sf.write('clean.wav', clean, rate)
```

## 음질 향상 (대역폭 확장 — 전화급→방송급)
```python
from voicefixer import VoiceFixer
vf = VoiceFixer()
vf.restore(input='phone_quality.wav', output='broadcast.wav', cuda=True, mode=2)
```

## 스템 분리 (보컬/드럼/베이스/기타)
```bash
demucs -n htdemucs --two-stems=vocals song.mp3
# 결과: separated/htdemucs/song/vocals.wav, no_vocals.wav

# 4-stem 분리
demucs -n htdemucs song.mp3
# 결과: vocals.wav, drums.wav, bass.wav, other.wav
```

## 음성 텍스트 변환 (STT)
```bash
# Whisper
whisper audio.mp3 --model large-v3 --language ko --output_format srt

# Faster Whisper (4x 빠름)
pip install faster-whisper
```

## AI 작곡
```python
from audiocraft.models import MusicGen
model = MusicGen.get_pretrained('facebook/musicgen-melody')
model.set_generation_params(duration=30)
wav = model.generate(['epic orchestral, cinematic, 120bpm'])
```

## 보이스 클로닝
```bash
# edge-tts (무료 한국어)
edge-tts --text "안녕하세요" --voice ko-KR-SunHiNeural --write-media output.mp3

# RVC (보이스 변환)
# GPT-SoVITS (한국어 보이스 클로닝)
```

## 참조
- `plugins/design_ppt/references/media-restoration-toolkit.md` § 3~4
