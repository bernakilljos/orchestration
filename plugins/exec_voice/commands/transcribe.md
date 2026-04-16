---
description: "음성 파일 → 텍스트 변환 (Whisper STT)"
allowed-tools: Bash(python:*), Bash(where:*), Write
---

## Context
- Whisper: !`python -c "import whisper; print('OK')" 2>/dev/null || echo 없음`
- FFmpeg: !`where ffmpeg 2>/dev/null && echo OK || echo 없음`

## Your task

### Step 1 — 사전 확인
Whisper 없음 → `/status` 실행 후 중단 안내

### Step 2 — 변환 실행
입력: `$ARGUMENTS` (파일 경로 또는 디렉터리)

```python
import whisper, os, datetime

model = whisper.load_model("base")  # tiny/base/small/medium/large

audio_file = "$ARGUMENTS"
result = model.transcribe(audio_file, language="ko")

# 저장 경로
today = datetime.date.today().strftime("%Y-%m-%d")
os.makedirs(f"docs/{today}/transcripts", exist_ok=True)

base = os.path.splitext(os.path.basename(audio_file))[0]
out = f"docs/{today}/transcripts/{base}.txt"

with open(out, "w", encoding="utf-8") as f:
    f.write(result["text"])

print(f"저장: {out}")
```

### Step 3 — 결과
- 저장 경로: `docs/YYYY-MM-DD/transcripts/파일명.txt`
- 텍스트 미리보기 (앞 200자)
- 소요 시간
- `/speak` 또는 `/meeting` 으로 후속 처리 안내
