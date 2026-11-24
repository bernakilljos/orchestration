#!/bin/bash
# SessionStart hook — .vscode/settings.json 에 setup/templates 성능 설정 중 빠진 키만 채움.
# 2026-11-24: 종전엔 파일이 있으면 건너뛰어 기존 설정이 있는 대상은 한 번도 적용 안 됨 → 빠진 키 병합 (대상 값·인터프리터는 유지 · 변화 없으면 쓰기 0).
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

[ -f "$SRC" ] || exit 0

mkdir -p "$ROOT/.vscode" 2>/dev/null

# Discover python — Windows `where` first, then POSIX `command -v`
PY=""
if command -v where >/dev/null 2>&1; then
  PY="$(where python 2>/dev/null | head -n 1 | tr -d '\r')"
fi
[ -z "$PY" ] && PY="$(command -v python 2>/dev/null || true)"
[ -z "$PY" ] && PY="$(command -v python 2>/dev/null || true)"
[ -z "$PY" ] && PY="python"

# JSON-safe render — load template, replace placeholder, dump (auto-escapes backslashes)
PYBIN="$PY"
[ ! -x "$PYBIN" ] && command -v python >/dev/null 2>&1 && PYBIN="python" || true
[ ! -x "$PYBIN" ] && command -v python >/dev/null 2>&1 && PYBIN="python" || true

"$PYBIN" - "$SRC" "$DST" "$PY" <<'PYEOF'
import json, re, sys, pathlib
src = pathlib.Path(sys.argv[1]); dst = pathlib.Path(sys.argv[2]); py = sys.argv[3]
tpl = json.loads(src.read_text(encoding="utf-8-sig"))
tpl["python.defaultInterpreterPath"] = py
cur = {}
if dst.exists():
    try:
        cur = json.loads(re.sub(r"^\s*//.*$", "", dst.read_text(encoding="utf-8-sig"), flags=re.M) or "{}")
    except ValueError:
        sys.exit(0)   # 대상이 손으로 쓴 JSONC 등 → 건드리지 않음
added = 0
for k, v in tpl.items():
    if k not in cur:
        cur[k] = v; added += 1
    elif isinstance(v, dict) and isinstance(cur[k], dict):
        for sk, sv in v.items():
            if sk not in cur[k]:
                cur[k][sk] = sv; added += 1
    elif isinstance(v, list) and isinstance(cur[k], list):
        for i in v:
            if i not in cur[k]:
                cur[k].append(i); added += 1
if added:
    dst.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[deploy-vscode-settings] {dst} +{added}")
PYEOF

exit 0
