#!/usr/bin/env bash
# find-python.sh — Windows Store 스텁 회피, 실제 Python 탐지
# 사용: source "$(dirname "$0")/find-python.sh"  → $PYTHON 변수 사용
# 목적: WindowsApps\python.exe (Store installer 스텁) 제외

_find_real_python() {
  local p path
  for p in python3 python; do
    path="$(command -v "$p" 2>/dev/null)" || continue
    # Windows Store 스텁 제외
    case "$path" in
      *WindowsApps*) continue ;;
    esac
    echo "$path"
    return 0
  done
  return 1
}

PYTHON="$(_find_real_python 2>/dev/null)" || PYTHON=""
export PYTHON
