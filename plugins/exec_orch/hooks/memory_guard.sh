#!/usr/bin/env bash
# memory_guard.sh — strategy_memory.json 크기 모니터링 (100MB 초과시 경고)
# Windows Git Bash 호환
# Usage: bash .claude/hooks/memory_guard.sh

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$PROJECT_DIR"

SM="$PROJECT_DIR/data/strategy_memory.json"
# Convert Git Bash /c/ paths to C:/ for Python on Windows
SM_PY=$(echo "$SM" | sed -E 's|^/([a-zA-Z])/|\1:/|')
WARN_SIZE_MB=100
CRITICAL_SIZE_MB=200

echo "=== [MEMORY-GUARD] strategy_memory.json 모니터링 ==="

if [ ! -f "$SM" ]; then
    echo "[WARN] strategy_memory.json 파일 없음"
    exit 0
fi

# 1. 파일 크기 확인
FILE_SIZE=$(wc -c < "$SM" | tr -d ' ')
FILE_SIZE_MB=$((FILE_SIZE / 1048576))
FILE_SIZE_KB=$((FILE_SIZE / 1024))

echo "[INFO] 파일 크기: ${FILE_SIZE_KB}KB (${FILE_SIZE_MB}MB)"

# 2. 크기 기반 경고
if [ "$FILE_SIZE_MB" -ge "$CRITICAL_SIZE_MB" ]; then
    echo "[CRITICAL] ${CRITICAL_SIZE_MB}MB 초과! 즉시 정리 필요!"
    echo "[ACTION]   1) data/backups/ 에 백업"
    echo "           2) 중복 전략 제거"
    echo "           3) 오래된/저성능 전략 아카이브"
    exit 2
elif [ "$FILE_SIZE_MB" -ge "$WARN_SIZE_MB" ]; then
    echo "[WARN] ${WARN_SIZE_MB}MB 초과! 정리를 권장합니다."
    exit 1
else
    echo "[OK]   크기 정상 (임계값: ${WARN_SIZE_MB}MB)"
fi

# 3. 전략 수 확인
STRATEGY_COUNT=$(python -c "
import json
with open('${SM_PY}', encoding='utf-8') as f:
    data = json.load(f)
if isinstance(data, list):
    print(len(data))
elif isinstance(data, dict):
    strategies = data.get('strategies', data.get('experiments', []))
    if isinstance(strategies, list):
        print(len(strategies))
    else:
        print(len(data))
" 2>/dev/null || echo "N/A")

echo "[INFO] 전략 수: ${STRATEGY_COUNT}개"

# 4. JSON 유효성 확인
if python -c "import json; json.load(open('${SM_PY}', encoding='utf-8'))" 2>/dev/null; then
    echo "[OK]   JSON 구조 유효"
else
    echo "[FAIL] JSON 구조 손상!"
    exit 2
fi

# 5. 중복 전략 체크
DUPE_COUNT=$(python -c "
import json
with open('${SM_PY}', encoding='utf-8') as f:
    data = json.load(f)
entries = data if isinstance(data, list) else data.get('strategies', data.get('experiments', []))
if isinstance(entries, list):
    names = [e.get('name', e.get('phase', '')) for e in entries if isinstance(e, dict)]
    dupes = len(names) - len(set(names))
    print(dupes)
else:
    print(0)
" 2>/dev/null || echo "0")

if [ "${DUPE_COUNT:-0}" -gt 0 ]; then
    echo "[WARN] 중복 전략 감지: ${DUPE_COUNT}건"
else
    echo "[OK]   중복 전략 없음"
fi

# 6. 마지막 수정 시각
LAST_MOD=$(date -r "$SM" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "N/A")
echo "[INFO] 마지막 수정: $LAST_MOD"

echo "=== [MEMORY-GUARD] 점검 완료 ==="
