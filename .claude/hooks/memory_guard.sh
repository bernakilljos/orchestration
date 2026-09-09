#!/usr/bin/env bash
# memory_guard.sh — strategy_memory.json 크기 모니터링 (100MB 초과시 경고)
# Windows Git Bash 호환
# Usage: bash .claude/hooks/memory_guard.sh

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
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
# 2026-09-09: 이 검사가 매 세션 "중복 2,179건" 을 외쳤는데 **전부 거짓**이었다.
#   원인 = e.get('name', ...) 이 name 키 없는 항목까지 빈 문자열 하나로 뭉갠 것.
#   실측: 3,529개 중 2,530개(72%)가 name 키 자체가 없고 id 로 식별된다
#   (예: claude_exp_20260327_072113). 내용 완전동일 0건 · 이름 겹침 0건 · id 겹침 0건.
#   그래서 식별자를 id > name > phase 순으로 잡고, 셋 다 없는 항목은 중복이 아니라
#   '식별자 없음' 으로 따로 센다. 진짜 중복은 내용 해시로도 교차 확인한다.
DUPE_OUT=$(python -c "
import json, hashlib
with open('${SM_PY}', encoding='utf-8') as f:
    data = json.load(f)
entries = data if isinstance(data, list) else data.get('strategies', data.get('experiments', []))
if not isinstance(entries, list):
    print('0 0 0'); raise SystemExit
items = [e for e in entries if isinstance(e, dict)]
keys, noid = [], 0
for e in items:
    k = e.get('id') or e.get('name') or e.get('phase')
    if k: keys.append(k)
    else: noid += 1
dup_key = len(keys) - len(set(keys))
hashes = {hashlib.sha256(json.dumps(e, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest() for e in items}
dup_full = len(items) - len(hashes)
print('%d %d %d' % (dup_key, dup_full, noid))
" 2>/dev/null || echo "0 0 0")
DUPE_KEY=$(echo "$DUPE_OUT" | awk '{print $1}')
DUPE_FULL=$(echo "$DUPE_OUT" | awk '{print $2}')
NO_ID=$(echo "$DUPE_OUT" | awk '{print $3}')

if [ "${DUPE_KEY:-0}" -gt 0 ] || [ "${DUPE_FULL:-0}" -gt 0 ]; then
    echo "[WARN] 중복 전략 감지: 식별자 중복 ${DUPE_KEY}건 · 내용 완전동일 ${DUPE_FULL}건"
else
    echo "[OK]   중복 전략 없음 (식별자 0 · 내용 0)"
fi
if [ "${NO_ID:-0}" -gt 0 ]; then
    echo "[INFO] 식별자(id/name/phase) 없는 항목: ${NO_ID}건 — 중복 아님"
fi

# 6. 마지막 수정 시각
LAST_MOD=$(date -r "$SM" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "N/A")
echo "[INFO] 마지막 수정: $LAST_MOD"

echo "=== [MEMORY-GUARD] 점검 완료 ==="

# 7. 급종료 기록기(crash-forensics) idempotent 재기동
#    프로젝트에 .claude/scripts/crash-forensics.ps1 이 있을 때만 동작한다([ -f ] 가드).
#    기록기는 60초마다 여유RAM·커밋·PagedPool·프로세스 상위를 로그에 적재하고,
#    10분마다 프로젝트의 메모리 가드를 단발 호출한다 — schtasks 미사용(NO-SCHTASKS 존중).
#    2026-09-09: 이 블록을 target 에만 두었더니 2026-09-02 kit sync 가 지워
#    17일간 아무도 안 돌았다. kit 이 정본이어야 sync 가 되돌리지 않는다.
FORENSICS_PS1="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}/.claude/scripts/crash-forensics.ps1"
if [ -f "$FORENSICS_PS1" ]; then
    WIN_PS1=$(cygpath -w "$FORENSICS_PS1" 2>/dev/null || echo "$FORENSICS_PS1")
    powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "
      \$me = \$PID
      \$run = Get-CimInstance Win32_Process -Filter \"Name='powershell.exe'\" |
              Where-Object { \$_.ProcessId -ne \$me -and \$_.CommandLine -match '-File\s+\S*crash-forensics\.ps1' }
      if (-not \$run) {
        Start-Process powershell.exe -ArgumentList '-NoProfile','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File','$WIN_PS1' -WindowStyle Hidden | Out-Null
      }
    " >/dev/null 2>&1
    echo "[OK]   급종료 기록기 가동 중 (10분마다 메모리 가드 동반)"
fi
