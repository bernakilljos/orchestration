#!/bin/bash
# sync-plugins.sh — 플러그인 → .claude/ 단방향 동기화
#
# 소스(원본, 편집 대상): plugins/<name>/{commands,skills,hooks}/*.md
# 타겟(생성물):          .claude/{commands,skills,hooks}/*.md
#
# 규칙:
#   1. commands: 동일 이름 있으면 덮어씀. 충돌 룰(collision map)에 등록된 파일은 접두사 붙여서 복사.
#   2. skills: 동일 이름으로 복사 (접두사 불필요 — 스킬명 자체가 유니크해야 함)
#   3. hooks: *.sh 스크립트는 직접 사용 (복사 안 함 — 훅은 플러그인 경로에서 참조)
#
# 사용법:
#   bash .claude/scripts/sync-plugins.sh          # 실제 동기화
#   bash .claude/scripts/sync-plugins.sh --dry    # 어떤 파일이 바뀔지만 출력
#
# 소스가 진실, .claude/ 의 드리프트는 덮어씀.

set -euo pipefail

DRY_RUN="false"
[ "${1:-}" = "--dry" ] && DRY_RUN="true"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

copied=0
skipped=0
renamed=0

# 충돌 룰: <plugin>/<file> → <target_name>
# 여러 플러그인에 같은 이름(make.md, status.md, install.md)이 있을 때 접두사 부여
declare -A RENAME_MAP=(
  ["design_excel/commands/make.md"]="excel-make.md"
  ["design_excel/commands/status.md"]="excel-status.md"
  ["design_word/commands/make.md"]="word-make.md"
  ["design_word/commands/status.md"]="word-status.md"
  ["design_ppt/commands/install.md"]="ppt-install.md"
  ["exec_voice/commands/status.md"]="voice-status.md"
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
)

sync_file() {
  local src="$1"      # e.g. plugins/exec_orch/commands/check-agents.md
  local subdir="$2"   # e.g. commands
  local rel="${src#plugins/}"  # e.g. exec_orch/commands/check-agents.md
  local plugin="${rel%%/*}"    # exec_orch
  local file_in_plugin="${rel#*/}"  # commands/check-agents.md
  local basename
  basename="$(basename "$src")"

  # 충돌 룰 조회 (plugin/commands/file.md 키로)
  local key="${plugin}/${subdir}/${basename}"
  local target_name="${RENAME_MAP[$key]:-$basename}"
  local dst=".claude/${subdir}/${target_name}"

  if [ "$target_name" != "$basename" ]; then
    renamed=$((renamed+1))
  fi

  if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
    skipped=$((skipped+1))
    return
  fi

  if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY] $src → $dst"
  else
    mkdir -p "$(dirname "$dst")"
    cp -f "$src" "$dst"
    echo "[SYNC] $src → $dst"
  fi
  copied=$((copied+1))
}

echo "=== Plugin → .claude/ sync ==="
[ "$DRY_RUN" = "true" ] && echo "(dry run mode)"

for plugin_dir in plugins/*/; do
  [ -d "$plugin_dir" ] || continue

  if [ -d "${plugin_dir}commands" ]; then
    for f in "${plugin_dir}commands"/*.md; do
      [ -f "$f" ] || continue
      sync_file "$f" "commands"
    done
  fi

  if [ -d "${plugin_dir}skills" ]; then
    for f in "${plugin_dir}skills"/*.md; do
      [ -f "$f" ] || continue
      sync_file "$f" "skills"
    done
  fi
done

echo ""
echo "Summary: copied=$copied  skipped(identical)=$skipped  renamed=$renamed"
[ "$DRY_RUN" = "true" ] && echo "(dry run — no files changed)"
