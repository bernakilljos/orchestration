#!/usr/bin/env bash
# [차단] 킬스위치 - 파일 있으면 아무것도 안 하고 종료
if [ -f "$HOME/.claude/NO-SCHTASKS" ]; then exit 0; fi
# exec_offline SessionStart hook — 시스템 자동 감지 + tier 별 자동 install 안내
# Zero-touch: 사용자 액션 0
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DETECT="$PROJECT_ROOT/.claude/scripts/detect-system.py"
CACHE="$HOME/.claude/cache/system-tier.json"

if [ ! -f "$DETECT" ]; then exit 0; fi

# 캐시 있으면 사용, 없으면 새 감지
if [ ! -f "$CACHE" ]; then
  PYTHONIOENCODING=utf-8 python "$DETECT" --force >/dev/null 2>&1 || true
fi

if [ -f "$CACHE" ]; then
  TIER="$(python -c "import json; print(json.load(open('$CACHE'))['tier'])" 2>/dev/null || echo "unknown")"
  case "$TIER" in
    full)     MSG="[exec_offline] tier=full — Ollama + Llama 3.1 8B + RAG 자동 install 가능" ;;
    lite)     MSG="[exec_offline] tier=lite — Ollama + Gemma 2 2B + RAG 자동 install 가능" ;;
    rag_only) MSG="[exec_offline] tier=rag_only — RAG (ChromaDB + Claude API). LLM 호스팅 X" ;;
    *)        MSG="" ;;
  esac
  [ -n "$MSG" ] && echo "$MSG"
fi

exit 0
