#!/usr/bin/env bash
# exec_offline plugin — 시스템 사양 자동 감지 (GPU/RAM/tier)
# core 도구: .claude/scripts/detect-system.py 호출
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec PYTHONIOENCODING=utf-8 python "$PROJECT_ROOT/.claude/scripts/detect-system.py" "$@"
