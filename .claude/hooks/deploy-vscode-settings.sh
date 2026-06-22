#!/bin/bash
# SessionStart hook — Deploy .vscode/settings.json from setup/templates if missing.
# Idempotent: skips instantly if .vscode/settings.json already exists.
# JSON-safe rendering via python json.dump (auto-escapes backslashes).

set -e

# Auto-detect PROJECT_ROOT — handles both SoT (plugins/exec_orch/hooks/) and mirror (.claude/hooks/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
case "$SCRIPT_DIR" in
  */plugins/exec_orch/hooks) ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)" ;;
  */.claude/hooks)            ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)" ;;
  *)                          ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}" ;;
esac

DST="$ROOT/.vscode/settings.json"
SRC="$ROOT/setup/templates/vscode-settings.template.json"

[ -f "$DST" ] && exit 0
[ -f "$SRC" ] || exit 0

mkdir -p "$ROOT/.vscode" 2>/dev/null

# Discover python — Windows `where` first, then POSIX `command -v`
PY=""
if command -v where >/dev/null 2>&1; then
  PY="$(where python 2>/dev/null | head -n 1 | tr -d '\r')"
fi
[ -z "$PY" ] && PY="$(command -v python 2>/dev/null || true)"
[ -z "$PY" ] && PY="$(command -v python3 2>/dev/null || true)"
[ -z "$PY" ] && PY="python"

# JSON-safe render — load template, replace placeholder, dump (auto-escapes backslashes)
PYBIN="$PY"
[ ! -x "$PYBIN" ] && command -v python3 >/dev/null 2>&1 && PYBIN="python3" || true
[ ! -x "$PYBIN" ] && command -v python >/dev/null 2>&1 && PYBIN="python" || true

"$PYBIN" - "$SRC" "$DST" "$PY" <<'PYEOF'
import json, sys, pathlib
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
py  = sys.argv[3]
raw = src.read_text(encoding="utf-8").replace("__PYTHON_PATH__", "__PY_PLACEHOLDER__")
obj = json.loads(raw)
obj["python.defaultInterpreterPath"] = py
dst.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
PYEOF

echo "[deploy-vscode-settings] $DST created (interpreter=$PY)"
exit 0
