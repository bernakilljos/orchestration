#!/bin/bash
# uninstall.sh — Orchestration Kit 제거 (생성물만. 소스는 git 관리)
#
# 제거 대상:
#   - .claude/commands/, .claude/skills/ (sync 결과물)
#   - ~/.claude/orca/ (전역 큐, 옵션)
#   - 실행 중인 워커 (orcauto-stop)
#
# 보존:
#   - plugins/ (소스 오브 트루스)
#   - .claude/settings.json, hooks/ (수동 설정)

set -euo pipefail

FORCE="false"
REMOVE_GLOBAL="false"

for arg in "$@"; do
  case "$arg" in
    --force|-f)        FORCE="true" ;;
    --remove-global)   REMOVE_GLOBAL="true" ;;
    -h|--help)
      sed -n '2,13p' "$0"
      exit 0
      ;;
  esac
done

echo "=== Orchestration Kit Uninstall ==="
echo ""

# 확인
if [ "$FORCE" = "false" ]; then
  echo "다음이 제거됩니다:"
  echo "  - .claude/commands/*.md (sync 결과물)"
  echo "  - .claude/skills/*.md (sync 결과물)"
  [ "$REMOVE_GLOBAL" = "true" ] && echo "  - ~/.claude/orca/ (전역 큐)"
  echo ""
  echo "보존됩니다:"
  echo "  - plugins/ (소스)"
  echo "  - .claude/settings.json, hooks/ (설정)"
  echo ""
  read -p "계속? (y/N) " -n 1 -r
  echo ""
  [[ ! $REPLY =~ ^[Yy]$ ]] && { echo "취소됨"; exit 0; }
fi

# 워커 종료
if [ -f .claude/orca-stopped ]; then
  echo "[1] 워커 이미 정지됨"
else
  echo "[1] 워커 정지..."
  touch .claude/orca-stopped 2>/dev/null || true
fi

# .claude sync 결과물 제거
echo "[2] sync 결과물 제거..."
rm -f .claude/commands/*.md .claude/skills/*.md 2>/dev/null || true
echo "   ✓"

# 전역 큐 제거 (선택)
if [ "$REMOVE_GLOBAL" = "true" ]; then
  echo "[3] 전역 큐 제거..."
  rm -rf ~/.claude/orca/
  echo "   ✓"
else
  echo "[3] 전역 큐 보존 (--remove-global 시 제거)"
fi

echo ""
echo "=== 제거 완료 ==="
echo ""
echo "복구: bash .claude/scripts/install.sh"
