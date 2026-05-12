#!/usr/bin/env bash
# design_video plugin — ffmpeg 체크 + 기본 작업 안내
set -e
echo "[design_video] 도구 체크:"
if command -v ffmpeg >/dev/null 2>&1; then
  echo "  ✅ ffmpeg $(ffmpeg -version 2>&1 | head -1)"
  echo "  지원 작업: 자막 (--subtitle) · 쇼츠 (--shorts) · 썸네일 (--thumb) · 인코딩"
else
  echo "  ❌ ffmpeg 없음 — Windows: choco install ffmpeg / Mac: brew install ffmpeg / Linux: apt install ffmpeg"
fi
