#!/usr/bin/env bash
# music_studio plugin — 음악 도구 체크
set -e
echo "[music_studio] 도구 체크:"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "  [OK] ffmpeg (인코딩-믹싱)"
else
  echo "  [X] ffmpeg 없음 — 필요"
fi
PYTHONIOENCODING=utf-8 python -c "import pydub; print(f'  [OK] pydub {pydub.__version__}')" 2>/dev/null || echo "  [WARN] pydub 없음 — pip install pydub"
PYTHONIOENCODING=utf-8 python -c "import mido; print(f'  [OK] mido (MIDI)')" 2>/dev/null || echo "  [WARN] mido 없음 — pip install mido (MIDI)"
echo "  지원: 녹음-작곡-믹싱-편곡-가사-MIDI-커버"
