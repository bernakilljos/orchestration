#!/bin/bash
# common.sh - music_studio 공통 헬퍼
set -uo pipefail
PLUGIN_NAME="music_studio"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$PLUGIN_NAME"
DATA_DIR="$REPO_ROOT/data/$PLUGIN_NAME/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"

log_info()  { echo "[INFO] $1" >&2; printf '{"ts":"%s","level":"INFO","msg":"%s"}\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
log_error() { echo "[ERROR] $1" >&2; printf '{"ts":"%s","level":"ERROR","msg":"%s"}\n' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
is_dry_run() { [ "${DRY_RUN:-false}" = "true" ] && return 0; for a in "$@"; do [ "$a" = "--dry-run" ] && return 0; done; return 1; }
load_env() { [ -f "$REPO_ROOT/.env" ] && { set -a; source "$REPO_ROOT/.env"; set +a; }; }

# 음악 전용 유틸
check_ffmpeg() {
  command -v ffmpeg >/dev/null 2>&1 || { log_error "ffmpeg 필요 — /mcp_media-install 먼저"; return 1; }
}
check_lufs() {
  # 스트리밍 LUFS 기준 (Spotify/Apple Music: -14 LUFS)
  echo "-14 LUFS (스트리밍 표준)"
}
