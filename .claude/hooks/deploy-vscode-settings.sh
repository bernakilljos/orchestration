#!/bin/bash
# SessionStart hook — .vscode/settings.json 을 setup/templates 템플릿과 동적으로 맞춘다.
# 2026-11-24 R389 (사용자 "다른 PC 는 전파해도 설정이 안 바뀐다 · 동적으로"): 종전은 파일이 이미 있으면 즉시 종료해
#   먼저 만들어진 PC 에는 나중에 템플릿에 추가한 성능 설정(search.followSymlinks 등)이 영원히 안 들어갔다.
#   → 없으면 생성 · 있으면 «템플릿에만 있는 키·하위 항목» 만 채움 (그 PC 에서 바꾼 값은 보존 · 병합 키를 코드에 두지 않음).
#   주석·끝 쉼표 등으로 JSON 해석이 안 되는 파일은 건드리지 않고 한 줄 기록. 바뀐 게 없으면 쓰지 않음 (멱등).

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
[ -z "$PY" ] && PY="python"
PYBIN="$PY"
[ ! -x "$PYBIN" ] && command -v python >/dev/null 2>&1 && PYBIN="python" || true

"$PYBIN" -X utf8 - "$SRC" "$DST" "$PY" <<'PYEOF'
import json, os, sys, pathlib
src, dst, py = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
tmpl = json.loads(src.read_text(encoding="utf-8"))
tmpl = {k: (py if v == "__PYTHON_PATH__" else v) for k, v in tmpl.items()}   # 자리표시 = 이 PC 의 python (동적)


def merge(cur, add):
    """add 에만 있는 것만 cur 에 채움 · 반환 = 채운 항목 수. 값이 다르면 cur(그 PC 설정) 유지."""
    n = 0
    for k, v in add.items():
        if k not in cur:
            cur[k] = v
            n += 1
        elif isinstance(cur[k], dict) and isinstance(v, dict):
            n += merge(cur[k], v)
        elif isinstance(cur[k], list) and isinstance(v, list):
            for x in v:
                if x not in cur[k]:
                    cur[k].append(x)
                    n += 1
    return n


if dst.is_file():
    try:
        cur = json.loads(dst.read_text(encoding="utf-8-sig") or "{}")
    except ValueError as e:
        print(f"[deploy-vscode-settings] {dst} JSON 해석 불가(주석·끝 쉼표 등) — 건드리지 않음: {e}")
        sys.exit(0)
    if not isinstance(cur, dict):
        sys.exit(0)
    added = merge(cur, tmpl)
    if not added:
        sys.exit(0)
    msg = f"{dst} 템플릿 항목 {added}개 추가 (기존 값 유지)"
else:
    cur, msg = tmpl, f"{dst} created (interpreter={py})"
tmp = dst.with_name(dst.name + f".{os.getpid()}.tmp")
tmp.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
os.replace(tmp, dst)
print(f"[deploy-vscode-settings] {msg}")
PYEOF
exit 0
