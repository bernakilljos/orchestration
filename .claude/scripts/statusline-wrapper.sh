#!/usr/bin/env bash
# statusline-wrapper — Windows/Mac/Linux 호환 - python 자동 검색
# 근거: v2.1.152 등 구 버전에서 python env var expansion 실패 우회
set -eu
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF/../.." && pwd)"

# python 자동 검색 - WindowsApps stub 회피 (Microsoft Store Install Manager 뜨는 문제 fix)
PY=$(cat "$ROOT/.claude/state/python-path.txt" 2>/dev/null | tr -d '\r\n')
if [ -z "$PY" ] || [ ! -x "$(command -v "$PY" 2>/dev/null)" ]; then
  # fallback - find-python.sh 로 WindowsApps stub 제외하고 검색
  if [ -r "$ROOT/.claude/hooks/find-python.sh" ]; then
    . "$ROOT/.claude/hooks/find-python.sh"
    PY="${PYTHON:-python}"
  else
    PY=python
  fi
fi

# statusline_context.py 실행 - 실패 시 fallback
if ! "$PY" -X utf8 "$ROOT/.claude/scripts/statusline_context.py" 2>/dev/null; then
  echo "[FIX] kit"
fi
