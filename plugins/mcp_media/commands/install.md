---
description: "미디어/AI 처리 설치 — Whisper(STT)·TTS·FFmpeg"
allowed-tools: Bash(pip:*), Bash(winget:*), Bash(where:*), Bash(powershell:*)
---

## Context
- Python: !`python --version 2>/dev/null || echo "없음"`
- ffmpeg: !`where ffmpeg 2>/dev/null && echo "설치됨" || echo "없음"`
- whisper: !`python -c "import whisper; print('설치됨')" 2>/dev/null || echo "없음"`
- edge-tts: !`python -c "import edge_tts; print('설치됨')" 2>/dev/null || echo "없음"`

## Your task

Context 확인 후 미설치된 것만 설치한다.

### 1. FFmpeg (영상/음성 처리 엔진)
```
winget install Gyan.FFmpeg
```
winget 없으면:
```powershell
# Chocolatey
choco install ffmpeg -y
```

### 2. Whisper STT (OpenAI 음성인식)
```
pip install openai-whisper
```
GPU 있으면 추가:
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. TTS (Microsoft Edge TTS — 무료, 한국어 지원)
```
pip install edge-tts
```

설치 완료 후 동작 테스트:
```
# FFmpeg 버전 확인
ffmpeg -version

# Whisper 테스트
python -c "import whisper; print('Whisper OK')"

# TTS 테스트
python -c "import edge_tts; print('TTS OK')"
```

결과 보고:

| 도구 | 상태 | 역할 |
|------|------|------|
| FFmpeg | 설치됨/실패 | 영상 변환·편집·추출 |
| Whisper | 설치됨/실패 | 음성→텍스트 (한국어 지원) |
| edge-tts | 설치됨/실패 | 텍스트→음성 (한국어 지원) |

"이제 `/plug_media` 로 설치된 도구들을 Claude가 직접 호출할 수 있습니다."
