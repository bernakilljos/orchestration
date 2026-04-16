# exec_voice — Codex 지시서

## Codex 역할
음성 처리 스크립트 구현.
Whisper·edge-tts·FFmpeg 활용 코드 작성 및 실행.

## 처리 순서
1. task-instruction.md 의 음성 처리 태스크 확인
2. Python 스크립트 작성 (whisper/edge_tts/ffmpeg)
3. 실행 및 결과 파일 생성
4. docs/YYYY-MM-DD/ 경로에 저장
5. 완료 보고

## 출력 경로 규칙
- 음성 파일: `docs/YYYY-MM-DD/audio/`
- 텍스트 변환: `docs/YYYY-MM-DD/transcripts/`
- 회의록: `docs/YYYY-MM-DD/meetings/`

## 사용 라이브러리
```python
import whisper      # STT
import edge_tts     # TTS
import asyncio      # edge_tts async
import noisereduce  # 노이즈 제거
import soundfile    # 오디오 읽기/쓰기
```

## MCP 불필요
음성 처리는 로컬 Python 라이브러리로 처리.
