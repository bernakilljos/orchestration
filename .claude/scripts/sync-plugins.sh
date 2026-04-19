#!/bin/bash
# sync-plugins.sh v2 — plugins/ → .claude/ 단방향 동기화 + 고도화 검사
#
# 기능:
#   1. 단방향 sync: plugins/<name>/{commands,skills}/*.md → .claude/{commands,skills}/
#   2. 충돌 룰(rename map) 적용
#   3. Orphan 탐지: .claude/ 에만 있는 파일 경고
#   4. Diff 상세: dry-run 시 내용 차이 표시
#   5. 역방향 드리프트 감지: .claude/ 파일이 plugins/ 와 다르면 경고
#   6. 의존성 순서 검증: plugin.json dependencies 기반
#
# 사용법:
#   bash .claude/scripts/sync-plugins.sh                실제 동기화
#   bash .claude/scripts/sync-plugins.sh --dry          미리보기 (변경 없음)
#   bash .claude/scripts/sync-plugins.sh --check        드리프트·orphan 점검만
#   bash .claude/scripts/sync-plugins.sh --verbose      상세 출력
#   bash .claude/scripts/sync-plugins.sh --prune        orphan 자동 삭제 (주의)

set -euo pipefail

MODE="sync"
VERBOSE="false"
PRUNE="false"

for arg in "$@"; do
  case "$arg" in
    --dry|--dry-run) MODE="dry" ;;
    --check)         MODE="check" ;;
    --prune)         PRUNE="true" ;;
    --verbose|-v)    VERBOSE="true" ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

copied=0
skipped=0
renamed=0
drift=0
orphan=0

# 충돌 룰 — 여러 플러그인에 동명 파일 있을 때만 사용
# design_excel/make.md 같은 건 이미 파일명이 excel-make.md 로 rename 됨 (RENAME_MAP 불필요)
declare -A RENAME_MAP=(
  ["mcp_collab/commands/install.md"]="mcp_collab-install.md"
  ["mcp_collab/commands/status.md"]="mcp_collab-status.md"
  ["mcp_data/commands/install.md"]="mcp_data-install.md"
  ["mcp_data/commands/status.md"]="mcp_data-status.md"
  ["mcp_dev/commands/install.md"]="mcp_dev-install.md"
  ["mcp_dev/commands/status.md"]="mcp_dev-status.md"
  ["mcp_docs/commands/install.md"]="mcp_docs-install.md"
  ["mcp_docs/commands/status.md"]="mcp_docs-status.md"
  ["mcp_media/commands/install.md"]="mcp_media-install.md"
  ["mcp_media/commands/status.md"]="mcp_media-status.md"
  ["mcp_web/commands/install.md"]="mcp_web-install.md"
  ["mcp_web/commands/status.md"]="mcp_web-status.md"
  ["mcp_social/commands/install.md"]="mcp_social-install.md"
  ["mcp_social/commands/status.md"]="mcp_social-status.md"
  ["mcp_social/commands/auth.md"]="mcp_social-auth.md"
)

# target_name → plugins/ 원본 경로 역맵 (orphan 탐지용)
declare -A REVERSE_MAP=()

# =========================================================================
# 1. 의존성 순서 결정 (plugin.json dependencies 위상정렬)
# =========================================================================
resolve_plugin_order() {
  # Windows 의 python3 는 MS 스토어 placeholder 일 수 있어 python 우선
  local py=""
  if command -v python >/dev/null 2>&1 && python -c "import sys" 2>/dev/null; then
    py="python"
  elif command -v python3 >/dev/null 2>&1 && python3 -c "import sys" 2>/dev/null; then
    py="python3"
  fi

  if [ -n "$py" ]; then
    $py .claude/scripts/resolve-plugin-order.py 2>/dev/null | tr -d '\r'
  else
    ls plugins/ | grep -v "^_template$" | tr -d '\r'
  fi
}

# =========================================================================
# 2. sync 함수
# =========================================================================
sync_file() {
  local src="$1"
  local subdir="$2"
  local rel="${src#plugins/}"
  local plugin="${rel%%/*}"
  local file_in_plugin="${rel#*/}"
  local basename
  basename="$(basename "$src")"

  local key="${plugin}/${subdir}/${basename}"
  local target_name="${RENAME_MAP[$key]:-$basename}"
  local dst=".claude/${subdir}/${target_name}"

  # 역맵 기록 (orphan 탐지용)
  REVERSE_MAP["${subdir}/${target_name}"]="$src"

  if [ "$target_name" != "$basename" ]; then
    renamed=$((renamed+1))
  fi

  if [ -f "$dst" ]; then
    if cmp -s "$src" "$dst"; then
      skipped=$((skipped+1))
      return
    fi
    # 역방향 드리프트 체크: .claude/ 파일 수정 시각이 plugins/ 보다 새로우면
    if [ "$MODE" = "check" ] || [ "$VERBOSE" = "true" ]; then
      local src_mtime dst_mtime
      src_mtime=$(stat -c %Y "$src" 2>/dev/null || stat -f %m "$src" 2>/dev/null || echo 0)
      dst_mtime=$(stat -c %Y "$dst" 2>/dev/null || stat -f %m "$dst" 2>/dev/null || echo 0)
      if [ "$dst_mtime" -gt "$src_mtime" ]; then
        echo "⚠️  DRIFT: $dst 가 $src 보다 새로움 (.claude/ 직접 수정 의심)"
        drift=$((drift+1))
      fi
    fi
  fi

  case "$MODE" in
    dry)
      echo "[DRY] $src → $dst"
      if [ "$VERBOSE" = "true" ] && [ -f "$dst" ]; then
        diff -u "$dst" "$src" 2>/dev/null | head -20 || true
      fi
      copied=$((copied+1))
      ;;
    sync)
      mkdir -p "$(dirname "$dst")"
      cp -f "$src" "$dst"
      [ "$VERBOSE" = "true" ] && echo "[SYNC] $src → $dst"
      copied=$((copied+1))
      ;;
    check)
      echo "[DIFF] $src ↔ $dst"
      copied=$((copied+1))
      ;;
  esac
}

# =========================================================================
# 3. 메인 실행
# =========================================================================
echo "=== sync-plugins.sh v2 (mode=$MODE) ==="

ORDER=$(resolve_plugin_order)

for plugin in $ORDER; do
  plugin_dir="plugins/${plugin}/"
  [ -d "$plugin_dir" ] || continue

  for sub in commands skills; do
    if [ -d "${plugin_dir}${sub}" ]; then
      for f in "${plugin_dir}${sub}"/*.md; do
        [ -f "$f" ] || continue
        sync_file "$f" "$sub"
      done
    fi
  done
done

# =========================================================================
# 4. Orphan 탐지 — .claude/commands,skills/ 에 있지만 plugins/ 에 원본 없음
# =========================================================================
echo ""
echo "=== Orphan 점검 ==="
orphan_list=()
for sub in commands skills; do
  [ -d ".claude/${sub}" ] || continue
  for f in ".claude/${sub}"/*.md; do
    [ -f "$f" ] || continue
    local_key="${sub}/$(basename "$f")"
    if [ -z "${REVERSE_MAP[$local_key]:-}" ]; then
      # skill-01 ~ skill-40 등 레거시는 제외
      case "$(basename "$f")" in
        skill-0[0-9]-*.md|skill-[1-3][0-9]-*.md|skill-4[0-5]-*.md) continue ;;
      esac
      orphan_list+=("$f")
      orphan=$((orphan+1))
    fi
  done
done

if [ "$orphan" -gt 0 ]; then
  echo "⚠️  Orphan $orphan 개 발견 (plugins/ 에 원본 없음):"
  for f in "${orphan_list[@]}"; do
    echo "   - $f"
  done
  echo ""
  if [ "$PRUNE" = "true" ]; then
    echo "   [--prune] 삭제 진행..."
    for f in "${orphan_list[@]}"; do
      rm -f "$f" && echo "      ✂ $f 삭제됨" || echo "      ⚠ $f 삭제 실패"
    done
    orphan=0
  else
    echo "   해결: plugins/<name>/commands/<name>.md 로 이동 또는 --prune 으로 일괄 삭제"
  fi
else
  echo "✓ Orphan 없음"
fi

# =========================================================================
# 5. 요약
# =========================================================================
echo ""
echo "=== Summary ==="
echo "  copied/changed: $copied"
echo "  skipped (identical): $skipped"
echo "  renamed (conflict): $renamed"
echo "  drift (.claude manual edit suspected): $drift"
echo "  orphan: $orphan"

case "$MODE" in
  dry)   echo "  (dry run — 실제 파일 변경 없음)" ;;
  check) echo "  (check mode — 드리프트·orphan 점검만)" ;;
  sync)  echo "  ✓ sync complete" ;;
esac

# 종료 코드: drift 또는 orphan 있으면 경고 (2), 정상은 0
if [ "$drift" -gt 0 ] || [ "$orphan" -gt 0 ]; then
  exit 2
fi
exit 0
