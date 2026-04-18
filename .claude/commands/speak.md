---
description: "텍스트 → 음성 출력 (edge-tts TTS) — 결과 읽어주기"
allowed-tools: Bash(python:*), Write
---

## Context
- edge-tts: !`python -c "import edge_tts; print('OK')" 2>/dev/null || echo 없음`

## Your task

### Step 1 — 사전 확인
edge-tts 없음 → `pip install edge-tts` 안내 후 중단

### Step 2 — 음성 변환
입력: `$ARGUMENTS` (텍스트 또는 텍스트 파일 경로)

```python
import edge_tts, asyncio, os, datetime

text = """$ARGUMENTS"""

# 파일 경로면 파일 읽기
if os.path.isfile(text.strip()):
    with open(text.strip(), encoding="utf-8") as f:
        text = f.read()

today = datetime.date.today().strftime("%Y-%m-%d")
os.makedirs(f"docs/{today}/audio", exist_ok=True)
out = f"docs/{today}/audio/output_{datetime.datetime.now().strftime('%H%M%S')}.mp3"

async def run():
    communicate = edge_tts.Communicate(text, voice="ko-KR-SunHiNeural")
    await communicate.save(out)

asyncio.run(run())
print(f"저장: {out}")
```

한국어 음성: `ko-KR-SunHiNeural` (여성) / `ko-KR-InJoonNeural` (남성)

### Step 3 — 결과
- 저장 경로: `docs/YYYY-MM-DD/audio/output_HHMMSS.mp3`
- 파일 크기, 예상 재생 시간
- FFmpeg 있으면 wav 변환 옵션 안내
