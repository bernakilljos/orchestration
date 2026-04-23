---
description: "미디어/AI 처리 설치 — Whisper(STT)·TTS·FFmpeg(MCP 옵션)"
allowed-tools: Bash(pip:*), Bash(npm:*), Bash(winget:*), Bash(where:*), Bash(powershell:*)
---

## Context
- Python: !`python --version 2>/dev/null || echo "없음"`
- Node.js: !`node --version 2>/dev/null || echo "없음"`
- ffmpeg: !`where ffmpeg 2>/dev/null && echo "설치됨" || echo "없음"`
- whisper: !`python -c "import whisper; print('설치됨')" 2>/dev/null || echo "없음"`
- edge-tts: !`python -c "import edge_tts; print('설치됨')" 2>/dev/null || echo "없음"`

## Your task

Context 확인 후 미설치된 것만 설치한다.

### 1. FFmpeg (영상/음성 처리 엔진)

**경로 A: 시스템 설치 (권장)**
```bash
# Windows: winget
winget install Gyan.FFmpeg

# winget 없으면: Chocolatey
choco install ffmpeg -y
```

**경로 B: MCP 사용 (선택)**
```bash
npm install -g mcp-ffmpeg
claude mcp add ffmpeg -s user -- npx -y mcp-ffmpeg
```
- 패키지: `mcp-ffmpeg` v1.0.5 또는 `ffmpeg-mcp-server` v1.0.2

### 2. Whisper STT (음성인식)

**경로 A: Python 직접 (권장 — 일반적)**
```bash
pip install openai-whisper

# GPU 있으면 추가 (CUDA 118)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
- 패키지: `openai-whisper` v1.0.2+

**경로 B: MCP 사용 (선택)**
```bash
npm install -g whisper-mcp
claude mcp add whisper -s user -- npx -y whisper-mcp
```
- 패키지: `whisper-mcp` v0.1.1 (로컬 오디오 전용)

### 3. TTS (텍스트→음성) — 2가지 선택

**옵션 A: Microsoft Edge TTS (무료, 한국어 지원)**
```bash
pip install edge-tts
python -c "import edge_tts; print('TTS OK')"
```
- 패키지: `edge-tts` v1.0.1+

**옵션 B: MCP 사용 (선택)**
```bash
npm install -g edge-tts-mcp-server
claude mcp add tts -s user -- npx -y edge-tts-mcp-server
```
- 패키지: `edge-tts-mcp-server` v1.0.17

**옵션 C: ElevenLabs (유료, 고품질)**
```bash
pip install elevenlabs
# API_KEY 필요: https://elevenlabs.io
```

또는 MCP:
```bash
npm install -g elevenlabs-mcp-enhanced
claude mcp add elevenlabs -s user -- npx -y elevenlabs-mcp-enhanced
```
- 패키지: `elevenlabs-mcp-enhanced` v0.9.11

---

## 설치 완료 후 테스트

```bash
# FFmpeg 버전 확인
ffmpeg -version

# Whisper 테스트
python -c "import whisper; print('Whisper OK')"

# Edge-TTS 테스트
python -c "import edge_tts; print('Edge-TTS OK')"

# (옵션) MCP 상태 확인
claude mcp list
```

---

## 결과 보고

| 도구 | 선택 | 상태 | 역할 |
|------|------|------|------|
| FFmpeg | 시스템 / MCP | 설치됨/실패 | 영상 변환·편집·추출 |
| Whisper | Python / MCP | 설치됨/실패 | 음성→텍스트 (한국어 지원) |
| TTS | Edge / ElevenLabs / MCP | 설치됨/실패 | 텍스트→음성 (한국어 지원) |

---

## 팁

- **Python vs MCP**: Python = 가볍고 직접 제어, MCP = Claude 문맥 통합. 팀 선호에 따라 선택.
- **한글 지원**: Whisper·Edge-TTS 모두 한국어 기본 지원.
- **GPU 최적화**: Whisper GPU 활성 시 음성 처리 3~5배 빠름 (여유 있으면 권장).
- **비용**: Edge-TTS 무료, ElevenLabs 유료 (한 달 10K 크레딧).
