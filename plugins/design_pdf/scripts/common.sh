#!/bin/bash
# common.sh - design_pdf 공통 헬퍼 (dry-run·검증·로깅)

set -uo pipefail

design_pdf="design_pdf"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$design_pdf"
DATA_DIR="$REPO_ROOT/data/$design_pdf/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"

log_info() {
  local msg="$1"
  local ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '{"ts":"%s","level":"INFO","plugin":"%s","msg":"%s"}\n' "$ts" "$design_pdf" "$msg" >> "$LOG_DIR/log.jsonl"
  echo "[INFO] $msg"
}

log_error() {
  local msg="$1"
  local ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  printf '{"ts":"%s","level":"ERROR","plugin":"%s","msg":"%s"}\n' "$ts" "$design_pdf" "$msg" >> "$LOG_DIR/log.jsonl"
  echo "[ERROR] $msg" >&2
}

is_dry_run() {
  [ "${DRY_RUN:-false}" = "true" ] && return 0
  for arg in "$@"; do
    [ "$arg" = "--dry-run" ] && return 0
  done
  return 1
}

load_env() {
  if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    source "$REPO_ROOT/.env"
    set +a
  fi
}

require_env() {
  local var_name="$1"
  eval "local val=\"\${$var_name:-}\""
  if [ -z "$val" ]; then
    log_error "Required env var not set: $var_name"
    return 1
  fi
}
