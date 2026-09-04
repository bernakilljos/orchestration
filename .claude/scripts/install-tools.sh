#!/usr/bin/env bash
# 외부 도구 자동 install — tier 별 분기
# tier = rag_only | lite | full (detect-system.py 결과)
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE="$HOME/.claude/cache/system-tier.json"

if [ ! -f "$CACHE" ]; then
  PYTHONIOENCODING=utf-8 python "$PROJECT_ROOT/.claude/scripts/detect-system.py" --force >/dev/null 2>&1 || true
fi

TIER="$(python -c "import json; print(json.load(open(r'$CACHE'))['tier'])" 2>/dev/null || echo "rag_only")"
echo "[install-tools] tier=$TIER"

# 공통 (모든 tier)
echo "[1/3] 공통 도구 (Python lib):"
for pkg in chromadb playwright python-docx PyMuPDF pillow psutil; do
  PYTHONIOENCODING=utf-8 python -c "import $(echo $pkg | tr '-' '_')" 2>/dev/null && echo "  [OK] $pkg" || pip install "$pkg" 2>&1 | tail -1
done

# tier 별
case "$TIER" in
  full|lite)
    echo "[2/3] Ollama (tier=$TIER):"
    if command -v ollama >/dev/null 2>&1; then
      echo "  [OK] ollama 설치됨"
    else
      echo "  [WARN] ollama 미설치 — https://ollama.com/download"
    fi
    ;;
  *)
    echo "[2/3] tier=rag_only -> Ollama skip (GPU 부족)"
    ;;
esac

# 선택 (외부 도구 — plugin 사용 시)
echo "[3/3] 선택 도구 (plugin 사용 시):"
for cmd in ffmpeg yt-dlp tesseract; do
  command -v "$cmd" >/dev/null 2>&1 && echo "  [OK] $cmd" || echo "  [WARN] $cmd 미설치 (필요 시 install)"
done

echo "[install-tools] 완료"
