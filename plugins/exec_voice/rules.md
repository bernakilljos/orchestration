# exec_voice 플러그인 규칙

## 목적
음성 입력·출력·처리 자동화.
STT(음성→텍스트) / TTS(텍스트→음성) / 회의록 / 음성 명령 파이프라인.

## 파이프라인
```
음성 입력 (마이크/파일)
  → Whisper STT → 텍스트 변환
  → Claude 분석 (요약 / 태스크 생성 / 회의록)
  → edge-tts TTS → 음성 출력 (결과 읽어주기)
  → FFmpeg 저장 (mp3/wav)
```

## 사전 요구사항
- Whisper: `pip install openai-whisper`
- edge-tts: `pip install edge-tts`
- FFmpeg: `winget install Gyan.FFmpeg`
- Python 3.8+

상태 확인: `/status`

## 출력 규칙
- 음성 파일: `docs/YYYY-MM-DD/audio/` 저장
- 텍스트 변환본: `docs/YYYY-MM-DD/transcripts/` 저장
- 회의록: `docs/YYYY-MM-DD/meetings/` 저장

## 금지
- 음성 파일 원본 덮어쓰기
- 개인정보 포함 텍스트 외부 전송
