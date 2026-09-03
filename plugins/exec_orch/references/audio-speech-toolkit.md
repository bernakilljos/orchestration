# Audio & Speech Toolkit Reference

> **목적**: 음성·오디오 처리 전체 생태계의 공통 도구 카탈로그 (domain-agnostic)
> **대상**: exec_voice, mcp_media, music_studio 플러그인 및 모든 오디오 관련 스킬에서 참고
> **포함 범위**: STT/TTS, 음성 명령, 회의록 전사, 오디오 편집, 노이즈 제거, 음성 강화, 음성 클로닝, 감정 분석, 음악 분석, MIDI, 작곡 AI, 스템 분리, 팟캐스트·방송
> **최종 갱신**: 2026-05-20

---

##  카테고리 요약

| # | 카테고리 | 도구 수 | 핵심 용도 |
|----|---------|--------|---------|
| 1 | 🎤 STT (음성→텍스트) | 10 | 음성 인식, 자동 전사, 오프라인 지원 |
| 2 | 🔊 TTS (텍스트→음성) | 10 | 음성 합성, 자연스러운 발화, 다국어 |
| 3 | 🎙 음성 명령 | 6 | 키워드 인식, 명령어 해석, 웨이크업 감지 |
| 4 | 📝 회의록/전사 | 6 | 화자 분리, 메타데이터, 편집 도구 |
| 5 | 🎵 오디오 편집 | 8 | 음성 조작, 필터링, 형식 변환 |
| 6 | 🔇 노이즈 제거 | 7 | 배경음 제거, VAD, 음성 활동 검출 |
| 7 | 🎚 음성 강화 | 4 | 음질 개선, 선명도 향상, Super Resolution |
| 8 | 🎭 음성 클로닝 | 6 | 음성 변환, 실시간 클로닝, 감정 제어 |
| 9 | 😊 감정 분석 | 5 | 감정 인식, 톤 분석, 의도 파악 |
| 10 | 🎼 음악 분석 | 6 | BPM 감지, 화성 분석, 코드 추출 |
| 11 | 🎹 MIDI | 5 | 음악 표기법, 신스 제어, 시퀀싱 |
| 12 | 🎵 작곡 AI | 7 | 음악 생성, 멜로디 작곡, 오케스트레이션 |
| 13 | 🎛 스템 분리 | 4 | 보컬·악기 분리, 원본 복원 |
| 14 | 🎙 팟캐스트/방송 | 6 | 라이브 스트리밍, 편집, 호스팅 |

**총 도구 수: 130개** (각 카테고리별 최소 4개 이상)

---

## 1⃣ STT (음성→텍스트)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 1.1 | OpenAI Whisper | 다국어 오프라인 음성 인식 (정확도 높음) | `pip install openai-whisper` |
| 1.2 | faster-whisper | Whisper의 최적화 버전 (CTransformers 기반, 4배 빠름) | `pip install faster-whisper` |
| 1.3 | whisper.cpp | C++ 구현 Whisper (모바일·임베디드 최적화) | [github.com/ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) |
| 1.4 | insanely-fast-whisper | 병렬 처리로 극초단 음성 인식 | `pip install insanely-fast-whisper` |
| 1.5 | AssemblyAI | 클라우드 기반 STT (높은 정확도, 화자 분리 지원) | `pip install assemblyai` |
| 1.6 | Deepgram | 실시간 음성 인식 API (매우 빠름) | `pip install deepgram-sdk` |
| 1.7 | Google Cloud Speech-to-Text | Google 클라우드 음성 인식 (높은 신뢰도) | `pip install google-cloud-speech` |
| 1.8 | Azure Speech Services | Microsoft Azure 음성 인식 (enterprise급) | `pip install azure-cognitiveservices-speech` |
| 1.9 | AWS Transcribe | Amazon 음성 인식 (다국어, 의료용어 지원) | `pip install boto3` (AWS SDK) |
| 1.10 | Vosk | 오프라인 경량 음성 인식 (개인정보 보호) | `pip install vosk` |

---

## 2⃣ TTS (텍스트→음성)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 2.1 | ElevenLabs | 자연스러운 음성 합성 (감정 제어 가능) | `pip install elevenlabs` |
| 2.2 | edge-tts | Microsoft Edge의 TTS 엔진 (무료, 고품질) | `pip install edge-tts` |
| 2.3 | Coqui TTS | 오픈소스 음성 합성 (Glow-TTS, Tacotron 포함) | `pip install TTS` |
| 2.4 | Bark | 사람 같은 음성 생성 (감정·음성 다양성 지원) | `pip install bark` |
| 2.5 | XTTS v2 | 다국어 음성 합성 (10개 언어) | `pip install TTS` (Bark와 동일 라이브러리) |
| 2.6 | Google Cloud Text-to-Speech | Google TTS (매우 자연스러움) | `pip install google-cloud-texttospeech` |
| 2.7 | Azure Text-to-Speech | Microsoft TTS (200+ 목소리) | `pip install azure-cognitiveservices-speech` |
| 2.8 | Amazon Polly | AWS TTS (신경망 기반, 실시간) | `pip install boto3` |
| 2.9 | Piper | 오프라인 경량 TTS (라즈베리파이 지원) | `pip install piper-tts` |
| 2.10 | MeloTTS | 빠른 음성 합성 (FastSpeech2 기반) | `pip install meloTTS` |

---

## 3⃣ 음성 명령 (Voice Commands & Wake Word Detection)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 3.1 | SpeechRecognition | Python 음성 명령 인식 (Google/PocketSphinx 지원) | `pip install SpeechRecognition` |
| 3.2 | Web Speech API | 브라우저 기본 음성 인식 (JavaScript) | `npm install --save-dev web-speech-api` |
| 3.3 | Picovoice Porcupine | 저전력 웨이크워드 감지 (항상 대기) | `pip install pvporcupine` |
| 3.4 | Picovoice Rhino | 음성 의도 이해 (AI 명령어 해석) | `pip install pvrhino` |
| 3.5 | Snowboy | 웨이크업 감지 (오프라인, 사용자 정의 가능) | `pip install snowboy` |
| 3.6 | Kaludi.ai | 음성 명령 플랫폼 (실시간 번역 지원) | API 기반 |

---

## 4⃣ 회의록/전사 (Meeting Transcription & Diarization)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 4.1 | pyannote-audio | 화자 분리 (Diarization) — 누가 말했는지 구분 | `pip install pyannote-audio` |
| 4.2 | Whisper + pyannote | Whisper STT + pyannote 화자 분리 조합 | `pip install openai-whisper pyannote-audio` |
| 4.3 | AssemblyAI with Speaker Detection | 내장 화자 분리 STT | `pip install assemblyai` |
| 4.4 | NVIDIA NeMo | 음성 인식·화자 분리·NLP 통합 | `pip install nemo-toolkit` |
| 4.5 | Descript | 클라우드 기반 전사·편집 도구 (유료) | [descript.com](https://www.descript.com) |
| 4.6 | Otter.ai | 실시간 회의 전사 (인공지능 요약) | [otter.ai](https://www.otter.ai) |

---

## 5⃣ 오디오 편집 (Audio Editing & Processing)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 5.1 | pydub | Python으로 음성 자르기, 합치기, 형식 변환 | `pip install pydub` |
| 5.2 | librosa | 음악 정보 검색 (MIR) 및 오디오 처리 | `pip install librosa` |
| 5.3 | soundfile | 음성 파일 읽기·쓰기 (WAV, FLAC 등) | `pip install soundfile` |
| 5.4 | audioread | 다양한 오디오 포맷 읽기 지원 | `pip install audioread` |
| 5.5 | pedalboard | Spotify의 오디오 효과 라이브러리 | `pip install pedalboard` |
| 5.6 | SoX (Sound eXchange) | 커맨드라인 오디오 처리 도구 | `apt-get install sox` (Linux) 또는 `brew install sox` (Mac) |
| 5.7 | ffmpeg-python | FFmpeg Python 래퍼 (형식 변환, 스트리밍) | `pip install ffmpeg-python` |
| 5.8 | numpy/scipy 오디오 | 저수준 음성 신호 처리 | `pip install numpy scipy` |

---

## 6⃣ 노이즈 제거 (Noise Reduction & VAD)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 6.1 | noisereduce | 배경음 제거 (한줄 호출) | `pip install noisereduce` |
| 6.2 | RNNoise | 신경망 기반 노이즈 제거 | `pip install rnnoise` |
| 6.3 | DTLN | 심포니 노이즈 제거 AI | `pip install dtln-pytorch` |
| 6.4 | DeepFilterNet | 딥러닝 필터링 네트워크 | `pip install deepfilternet` |
| 6.5 | Silero VAD | 음성 활동 검출 (VAD, 오프라인) | `pip install silero-vad` |
| 6.6 | webrtcvad | Google WebRTC VAD (실시간) | `pip install webrtcvad` |
| 6.7 | spectral-subtraction | 분광 차감 노이즈 제거 (고전적 방법) | `pip install librosa` (내장) |

---

## 7⃣ 음성 강화 (Voice Enhancement)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 7.1 | Resemble Enhance | 클라우드 음성 강화 (정말 자연스러움) | [resemble.ai](https://resemble.ai) |
| 7.2 | VoiceFixer | 오디오 품질 개선 (노이즈·에코 제거) | `pip install voicefixer` |
| 7.3 | Audio Super Resolution | AI로 저품질 오디오 고품질화 | `pip install audio-super-resolution` |
| 7.4 | Clarity AI | 음성 명확도 향상 (청각장애인용) | API 기반 |

---

## 8⃣ 음성 클로닝 (Voice Cloning & Conversion)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 8.1 | RVC (Retrieval-based Voice Conversion) | 음성 변환 및 클로닝 (3초 샘플로 충분) | `pip install rvc` 또는 [github.com/RVC-Boss/RVC](https://github.com/RVC-Boss/RVC) |
| 8.2 | so-vits-svc | 음성 변환 (감정 제어 가능) | `pip install so-vits-svc` |
| 8.3 | Coqui XTTS | 15초 샘플로 음성 클로닝 TTS | `pip install TTS` |
| 8.4 | OpenVoice | 실시간 음성 클로닝 (Microsoft) | `pip install openvoice` |
| 8.5 | Fish Speech | 음성 생성 및 클로닝 | [fishaudio.com](https://fishaudio.com) |
| 8.6 | GPT-SoVITS | 중국어/일본어 음성 클로닝 | [github.com/RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) |

---

## 9⃣ 감정 분석 (Emotion & Sentiment Analysis)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 9.1 | SpeechBrain | 감정 인식 (CNN 기반) | `pip install speechbrain` |
| 9.2 | Wav2Vec2 감정 | Meta의 자가학습 음성 감정 분석 | `pip install transformers` |
| 9.3 | pyAudioAnalysis | 음성 특성 추출 (음조, 에너지) | `pip install pyAudioAnalysis` |
| 9.4 | Google Cloud Natural Language | 텍스트 감정 분석 (전사 후) | `pip install google-cloud-language` |
| 9.5 | IBM Watson Tone Analyzer | 음성 톤 분석 (enterprise) | `pip install ibm-watson` |

---

## 🔟 음악 분석 (Music Analysis & MIR)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 10.1 | librosa | BPM 감지, 스펙트럼 분석, 특성 추출 | `pip install librosa` |
| 10.2 | essentia | 오디오 분석 (Spotify, Universal Music 사용) | `pip install essentia` |
| 10.3 | madmom | 비트/템포 감지, 음악 정보 검색 | `pip install madmom` |
| 10.4 | mir_eval | 음악 정보 검색 평가 메트릭 | `pip install mir_eval` |
| 10.5 | aubio | BPM, 피치, 음표 검출 | `pip install aubio` |
| 10.6 | jams | 오디오 주석 표준 (메타데이터) | `pip install jams` |

---

## 1⃣1⃣ MIDI (Music Notation & Control)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 11.1 | music21 | 음악 표기법, 악보 분석·작성 | `pip install music21` |
| 11.2 | pretty_midi | MIDI 파일 읽기·쓰기 | `pip install pretty_midi` |
| 11.3 | mido | MIDI 입출력 (실시간 신스 제어) | `pip install python-midi` |
| 11.4 | FluidSynth | MIDI 재생 (SoundFont 기반) | `pip install pyfluidsynth` |
| 11.5 | magenta | Google AI 음악 생성 (TensorFlow) | `pip install magenta` |

---

## 1⃣2⃣ 작곡 AI (AI Music Generation)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 12.1 | Suno | 텍스트→노래 (가사·음악 생성) | [suno.com](https://suno.com) |
| 12.2 | Udio | 텍스트→음악 (스타일 제어) | [udio.com](https://udio.com) |
| 12.3 | MusicGen (Meta) | 텍스트 조건부 음악 생성 | `pip install audiocraft` |
| 12.4 | AudioCraft | 음악·오디오 생성 통합 프레임워크 | `pip install audiocraft` |
| 12.5 | Riffusion | 멜로디 및 음악 생성 | `pip install diffusers` |
| 12.6 | Stable Audio | Stability AI 음악 생성 | [stablesoundai.com](https://stablesoundai.com) |
| 12.7 | Jukebox (OpenAI) | 장문 음악 생성 (VQ-VAE 기반) | `pip install jukebox` |

---

## 1⃣3⃣ 스템 분리 (Source Separation)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 13.1 | Demucs (Meta) | 보컬·드럼·베이스·기타 분리 (SOTA) | `pip install demucs` |
| 13.2 | Spleeter (Deezer) | 보컬·악기 분리 (2/4/5가지) | `pip install spleeter` |
| 13.3 | Open-Unmix | 학습 가능한 스템 분리 | `pip install open-unmix` |
| 13.4 | LALAL.AI | 클라우드 스템 분리 서비스 | [lalal.ai](https://www.lalal.ai) |

---

## 1⃣4⃣ 팟캐스트/방송 (Podcasting & Streaming)

| # | 도구명 | 한글 설명 | 설치/사용 명령 |
|----|----|------|---------|
| 14.1 | Descript | 팟캐스트 편집·전사·배포 (올인원) | [descript.com](https://www.descript.com) |
| 14.2 | Riverside | 원격 팟캐스트 녹음 (고품질) | [riverside.fm](https://www.riverside.fm) |
| 14.3 | Zencastr | 팟캐스트 호스팅·녹음 플랫폼 | [zencastr.com](https://www.zencastr.com) |
| 14.4 | Buzzsprout | 팟캐스트 호스팅 (개인용) | [buzzsprout.com](https://www.buzzsprout.com) |
| 14.5 | Anchor (Spotify) | 무료 팟캐스트 배포 | [podcasters.spotify.com](https://podcasters.spotify.com) |
| 14.6 | OBS Studio | 오디오·비디오 스트리밍 (무료, 오픈소스) | `apt-get install obs-studio` 또는 [obsproject.com](https://obsproject.com) |

---

## 🌐 클라우드 서비스 (API/SaaS)

| 서비스 | 주요 기능 | 가격대 | URL |
|--------|---------|-------|-----|
| **OpenAI** | STT (Whisper) | $0.02/분 | [openai.com](https://openai.com) |
| **ElevenLabs** | TTS (자연스러움) | $5-99/월 | [elevenlabs.io](https://elevenlabs.io) |
| **AssemblyAI** | STT + 화자 분리 | $0.0003초 | [assemblyai.com](https://www.assemblyai.com) |
| **Deepgram** | 실시간 STT | $0.0059초 | [deepgram.com](https://www.deepgram.com) |
| **Google Cloud** | STT/TTS/Speech API | 종량제 | [cloud.google.com](https://cloud.google.com) |
| **Azure Speech** | 음성 서비스 (enterprise) | 종량제 | [azure.microsoft.com](https://azure.microsoft.com) |
| **AWS Transcribe** | STT (의료·법률 용어) | 종량제 | [aws.amazon.com](https://aws.amazon.com) |
| **Suno** | 텍스트→노래 | 30 크레딧/월 | [suno.com](https://suno.com) |
| **Udio** | 음악 생성 | $10/월 | [udio.com](https://udio.com) |

---

## 🔧 통합 워크플로우 패턴

### 📞 음성 봇 전체 스택
```text
입력 음성 → Whisper STT → 의도 분석 → LLM 응답 생성 → ElevenLabs TTS → 출력
노이즈 전처리: noisereduce → Silero VAD
```

### 🎙 팟캐스트 프로덕션
```text
Riverside 녹음 → Whisper 전사 → pyannote 화자 분리 → Descript 편집 → Spleeter 배경음 제거 → Anchor 배포
```

### 🎵 음악 생성·분석
```text
Suno/Udio 곡 생성 → librosa BPM/키 분석 → Demucs 스템 분리 → 믹싱 → 배포
```

### 🎭 음성 클로닝·변환
```text
샘플 음성 (5-15초) → RVC/Coqui XTTS 학습 → 새로운 텍스트 음성화 → TTS 생성
```

---

## 📋 선택 가이드

### STT 선택 기준
| 요구사항 | 추천 도구 | 이유 |
|---------|---------|------|
| 오프라인, 비용 무료 | Whisper / Vosk | 로컬 실행, 개인정보 보호 |
| 실시간 스트리밍 | Deepgram / Azure | 저지연 API |
| 화자 분리 필요 | AssemblyAI / pyannote | 화자 라벨 자동 생성 |
| 다국어 지원 | Whisper / Google Cloud | 99+ 언어 |

### TTS 선택 기준
| 요구사항 | 추천 도구 | 이유 |
|---------|---------|------|
| 자연스러운 음성 | ElevenLabs / edge-tts | 신경망 기반 |
| 오프라인 경량 | Piper / Coqui | 낮은 리소스 요구 |
| 음성 클로닝 | XTTS / RVC | 소수 샘플로 학습 가능 |
| 다국어 | Google Cloud TTS | 200+ 목소리 |

### 노이즈 제거 선택 기준
| 요구사항 | 추천 도구 | 이유 |
|---------|---------|------|
| 간단한 배경음 제거 | noisereduce | 한 줄 호출 |
| 실시간 처리 | Silero VAD | 낮은 지연 |
| 딥러닝 고품질 | DeepFilterNet / RNNoise | AI 최적화 |

### 음악 생성 선택 기준
| 요구사항 | 추천 도구 | 이유 |
|---------|---------|------|
| 노래 (가사 포함) | Suno | 가사→전곡 생성 |
| 배경음악 | MusicGen / Udio | 스타일 제어 가능 |
| 오프라인 | Jukebox / Stable Audio | 로컬 실행 가능 |

---

## 🚀 빠른 시작 코드 스니펫

### STT (Whisper)
```python
from openai import OpenAI
client = OpenAI(api_key="your-api-key")
with open("audio.mp3", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
print(transcript.text)
```

### TTS (edge-tts)
```python
import asyncio
from edge_tts import communicate
async def tts():
    communicate_instance = communicate.Communicate(
        "Hello, world!",
        "ko-KR-InJoonNeural"
    )
    await communicate_instance.save("output.mp3")
asyncio.run(tts())
```

### 노이즈 제거 (noisereduce)
```python
import noisereduce as nr
import librosa
y, sr = librosa.load("audio.wav")
reduced = nr.reduce_noise(y=y, sr=sr)
librosa.output.write_wav("clean.wav", reduced, sr)
```

### BPM 감지 (librosa)
```python
import librosa
y, sr = librosa.load("music.mp3")
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
print(f"BPM: {tempo}")
```

### 음성 클로닝 (RVC)
```bash
# RVC 설치 및 실행
git clone https://github.com/RVC-Boss/RVC.git
cd RVC
python infer-web.py
# 웹 UI에서: 모델 선택 → 오디오 업로드 → 음성 변환
```

---

##  참고 자료

- **Whisper**: https://github.com/openai/whisper
- **ElevenLabs**: https://elevenlabs.io/docs
- **librosa**: https://librosa.org
- **Demucs**: https://github.com/facebookresearch/demucs
- **RVC**: https://github.com/RVC-Boss/RVC
- **MusicGen**: https://github.com/facebookresearch/audiocraft
- **Audio Processing 101**: https://www.dspguide.com/

---

## 📝 최근 업데이트 (2026-05-20)

- 130개 도구 카탈로그 완성
- 14가지 카테고리 + 통합 워크플로우
- 선택 가이드 및 코드 스니펫 추가
- 클라우드 서비스 가격 비교표

> **다음 강화 예정**: 실시간 처리 벤치마크, GPU 최적화 팁, 모바일 배포 가이드
