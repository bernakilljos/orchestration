#!/usr/bin/env bash
# statusline-wrapper — Windows/Mac/Linux 호환 - python 자동 검색
# 근거: v2.1.152 등 구 버전에서 python env var expansion 실패 우회
# 2026-11-18 (R288 성능 1차): 렌더마다 떠 있던 자식 프로세스 4개($(cd..) 2 · cat · tr)를 bash 내장으로 대체 — 출력 동일.
set -eu
SELF="${BASH_SOURCE[0]%/*}"
case "$SELF" in /*|[A-Za-z]:*) ;; *) SELF="$PWD/$SELF" ;; esac
ROOT="$SELF/../.."

# python 자동 검색 - WindowsApps stub 회피 (Microsoft Store Install Manager 뜨는 문제 fix)
PY=""
if [ -r "$ROOT/.claude/state/python-path.txt" ]; then
  IFS= read -r PY < "$ROOT/.claude/state/python-path.txt" || true
  PY="${PY%$'\r'}"
fi
if [ -z "$PY" ] || ! command -v "$PY" >/dev/null 2>&1; then
  # fallback - find-python.sh 로 WindowsApps stub 제외하고 검색
  if [ -r "$ROOT/.claude/hooks/find-python.sh" ]; then
    . "$ROOT/.claude/hooks/find-python.sh"
    PY="${PYTHON:-python}"
  else
    PY=python
  fi
fi

# statusline_context.py 실행 - 실패 시 fallback
# R356: 스크립트로 실행하면 .pyc 를 못 써 렌더마다 2,600줄을 다시 컴파일 (11-23 실측 ≈95ms) → 모듈로 import 해 _cli() 호출 (출력 동일)
if ! "$PY" -X utf8 -c 'import sys; sys.path.insert(0, sys.argv[1]); import statusline_context as m; m._cli()' "$ROOT/.claude/scripts" 2>/dev/null; then
  echo "[FIX] kit"
fi
