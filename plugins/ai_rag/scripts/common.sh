#!/bin/bash
# common.sh - ai_rag 공통 헬퍼
set -uo pipefail
ai_rag_NAME="ai_rag"
REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
LOG_DIR="$REPO_ROOT/.claude/state/$ai_rag_NAME"
DATA_DIR="$REPO_ROOT/data/$ai_rag_NAME/$(date +%Y-%m-%d)"
mkdir -p "$LOG_DIR" "$DATA_DIR"
log_info()  { echo "[INFO] $1" >&2; printf '{"ts":"%s","level":"INFO","msg":"%s"}
' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
log_error() { echo "[ERROR] $1" >&2; printf '{"ts":"%s","level":"ERROR","msg":"%s"}
' "$(date -u +%FT%TZ)" "$1" >> "$LOG_DIR/log.jsonl"; }
is_dry_run() { [ "${DRY_RUN:-false}" = "true" ] && return 0; for a in "$@"; do [ "$a" = "--dry-run" ] && return 0; done; return 1; }
load_env() { [ -f "$REPO_ROOT/.env" ] && { set -a; source "$REPO_ROOT/.env"; set +a; }; }
