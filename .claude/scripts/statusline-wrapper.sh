#!/usr/bin/env bash
# statusline-wrapper — Windows/Mac/Linux 호환 - python 자동 검색
# 근거: v2.1.152 등 구 버전에서 python env var expansion 실패 우회
set -eu
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF/../.." && pwd)"

# python 자동 검색
if command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v py >/dev/null 2>&1; then
  PY=py
else
  # fallback - 대상만 표시
  echo "[FIX] kit"
  exit 0
fi

# statusline_context.py 실행 - 실패 시 fallback
if ! "$PY" -X utf8 "$ROOT/.claude/scripts/statusline_context.py" 2>/dev/null; then
  echo "[FIX] kit"
fi
