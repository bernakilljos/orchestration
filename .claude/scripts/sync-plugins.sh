#!/bin/bash
# sync-plugins.sh — bash wrapper (2026-10-13: Python 로 재작성됨 · 71s → 0.4s · 190배 빠름)
#
# 실제 로직은 sync-plugins.py 에. 이 파일은 호환성 wrapper.
#
# 사용법:
#   bash .claude/scripts/sync-plugins.sh                실제 동기화
#   bash .claude/scripts/sync-plugins.sh --dry          미리보기
#   bash .claude/scripts/sync-plugins.sh --check        드리프트-orphan 점검만
#   bash .claude/scripts/sync-plugins.sh --verbose      상세
#   bash .claude/scripts/sync-plugins.sh --prune        orphan 자동 삭제
#
# 종료 코드: drift 또는 orphan 있으면 2, 정상 0.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Windows Store 스텁 회피
if [ -f "$HERE/../hooks/find-python.sh" ]; then
  # shellcheck source=/dev/null
  . "$HERE/../hooks/find-python.sh"
fi
PY="${PYTHON:-python}"

exec "$PY" -X utf8 "$HERE/sync-plugins.py" "$@"
