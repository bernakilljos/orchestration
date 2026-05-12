#!/usr/bin/env bash
# cost_youtube plugin — yt-dlp / YouTube API 도구 체크
set -e
echo "[cost_youtube] 도구 체크:"
if command -v yt-dlp >/dev/null 2>&1; then
  echo "  ✅ yt-dlp $(yt-dlp --version)"
else
  echo "  ❌ yt-dlp 없음 — pip install yt-dlp"
fi
if [ -n "$YOUTUBE_API_KEY" ]; then
  echo "  ✅ YOUTUBE_API_KEY 설정됨"
else
  echo "  ⚠️ YOUTUBE_API_KEY 미설정 — Google Cloud Console 에서 발급"
fi
