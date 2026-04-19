---
description: "음성 도구 설치 상태 확인 — Whisper·edge-tts·FFmpeg"
allowed-tools: Bash(where:*), Bash(python:*)
---

## Context
- Python: !`python --version 2>/dev/null || echo 없음`
- Whisper: !`python -c "import whisper; print('OK')" 2>/dev/null || echo 없음`
- edge-tts: !`python -c "import edge_tts; print('OK')" 2>/dev/null || echo 없음`
- FFmpeg: !`where ffmpeg 2>/dev/null && echo OK || echo 없음`

## Your task

위 Context 기반으로 상태 표 출력:

| 도구 | 상태 | 역할 |
|------|------|------|
| Python | OK/없음 | 기반 런타임 |
| Whisper | OK/없음 | 음성→텍스트 (STT) |
| edge-tts | OK/없음 | 텍스트→음성 (TTS) |
| FFmpeg | OK/없음 | 오디오 변환·편집 |

없는 항목 설치 명령어 출력:
```
pip install openai-whisper
pip install edge-tts
winget install Gyan.FFmpeg
```
