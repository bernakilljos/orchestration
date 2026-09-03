#!/bin/bash
# codex-quota-check.sh — Codex API 한도 감지 + 플래그 관리
#
# 사용처:
#   1. codex-runner.bat 내부 — 명령 실패 후 에러 메시지 검사
#   2. exec_orca-auto skill 세션 시작 시 — 플래그 존재하면 Claude 직접 모드
#
# 사용법:
#   bash .../codex-quota-check.sh --check-error "$(cat stderr.log)"
#       stderr 에서 "usage limit" 감지 시 플래그 생성 + exit 2
#   bash .../codex-quota-check.sh --status
#       플래그 존재 + TTL 체크 -> exit 0=정상, 2=한도중
#   bash .../codex-quota-check.sh --clear
#       플래그 제거 (TTL 만료 시 자동)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
STATE_DIR="$REPO_ROOT/.claude/state"
FLAG="$STATE_DIR/codex-quota-exceeded"

mkdir -p "$STATE_DIR"

MODE="${1:-status}"

case "$MODE" in
  --check-error)
    msg="${2:-}"
    # 알려진 한도 메시지 패턴
    if echo "$msg" | grep -qiE "usage limit|rate limit|quota exceed|429"; then
      # 만료 시각 추출 시도 (예: "Try again at 1:35 PM")
      retry_at=$(echo "$msg" | grep -oiE "[0-9]{1,2}:[0-9]{2} ?(AM|PM)?" | head -1)
      ts=$(date +%s)
      # 기본 3시간 후 자동 만료
      expire=$((ts + 3*3600))
      cat > "$FLAG" <<EOF
{
  "detected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "expire_epoch": $expire,
  "retry_hint": "$retry_at",
  "source": "codex"
}
EOF
      echo "[quota-flag] Codex 한도 감지 -> 플래그 생성. 만료: $(date -d @$expire 2>/dev/null || echo $expire)"
      exit 2
    fi
    exit 0
    ;;

  --status|"")
    if [ ! -f "$FLAG" ]; then
      echo "OK: 한도 플래그 없음"
      exit 0
    fi
    # TTL 체크
    expire=$(python -c "import json,sys; print(json.load(open(sys.argv[1])).get('expire_epoch', 0))" "$FLAG" 2>/dev/null || echo 0)
    now=$(date +%s)
    if [ "$expire" -gt 0 ] && [ "$now" -gt "$expire" ]; then
      rm -f "$FLAG"
      echo "OK: 한도 플래그 TTL 만료 -> 제거됨"
      exit 0
    fi
    cat "$FLAG"
    echo ""
    echo "-> Claude 직접 모드 권장 (codex 건너뛰기)"
    exit 2
    ;;

  --clear)
    rm -f "$FLAG"
    echo "플래그 제거됨"
    exit 0
    ;;

  *)
    sed -n '2,16p' "$0"
    exit 1
    ;;
esac
